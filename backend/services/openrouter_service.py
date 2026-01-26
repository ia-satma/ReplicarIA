"""
OpenRouter Service - Gateway to multiple LLM providers

OpenRouter provides a unified API to access multiple LLM providers:
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Google (Gemini Pro, Gemini Flash)
- xAI (Grok)
- Meta (Llama)
- And many more

This enables the LLM Council pattern where multiple models
review and validate each other's responses.
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# All models are Claude/Anthropic only
COUNCIL_MODELS = {
    "fact_auditor": "anthropic/claude-3.5-sonnet",
    "business_strategist": "anthropic/claude-3.5-sonnet", 
    "devils_advocate": "anthropic/claude-3-opus",
    "chairman": "anthropic/claude-3.5-sonnet",
}

MODEL_DISPLAY_NAMES = {
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "anthropic/claude-3-opus": "Claude 3 Opus",
    "anthropic/claude-sonnet-4-5": "Claude Sonnet 4.5",
    "anthropic/claude-opus-4-5": "Claude Opus 4.5",
}


class OpenRouterService:
    """
    Service for calling multiple LLMs via OpenRouter API.
    Implements the LLM Council pattern for anti-hallucination validation.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY', '')
        self.initialized = bool(self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        if self.initialized:
            logger.info("OpenRouter service initialized with API key")
        else:
            logger.warning("OPENROUTER_API_KEY not found - multi-LLM council will use fallback mode")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OpenRouter API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://revisar.ia",
            "X-Title": "SATMA Multi-Agent System"
        }
    
    async def call_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Call a specific model via OpenRouter.
        
        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with response content and metadata
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "OpenRouter not initialized",
                "content": None
            }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=self._get_headers(),
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "content": None
                    }
                
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "success": True,
                    "content": content,
                    "model": model,
                    "model_name": MODEL_DISPLAY_NAMES.get(model, model),
                    "usage": data.get("usage", {})
                }
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {model}")
            return {"success": False, "error": "Request timeout", "content": None}
        except Exception as e:
            logger.error(f"Error calling {model}: {e}")
            return {"success": False, "error": str(e), "content": None}
    
    def call_model_sync(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Synchronous wrapper for call_model"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.call_model(model, messages, temperature, max_tokens),
                    loop
                )
                return future.result(timeout=65)
            else:
                return asyncio.run(
                    self.call_model(model, messages, temperature, max_tokens)
                )
        except Exception as e:
            logger.error(f"Error in sync call: {e}")
            return {"success": False, "error": str(e), "content": None}
    
    async def call_council_parallel(
        self,
        prompt: str,
        system_prompts: Dict[str, str],
        models: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Call multiple council members in parallel.
        
        Args:
            prompt: The user prompt to send to all models
            system_prompts: Dict mapping role to system prompt
            models: Optional dict mapping role to model (uses defaults if not provided)
            
        Returns:
            Dict mapping role to response
        """
        if models is None:
            models = COUNCIL_MODELS
        
        tasks = {}
        for role, model in models.items():
            if role in system_prompts and role != "chairman":
                messages = [
                    {"role": "system", "content": system_prompts[role]},
                    {"role": "user", "content": prompt}
                ]
                tasks[role] = self.call_model(model, messages)
        
        results = {}
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for role, response in zip(tasks.keys(), responses):
            if isinstance(response, Exception):
                results[role] = {
                    "success": False,
                    "error": str(response),
                    "content": None
                }
            else:
                results[role] = response
        
        return results
    
    async def run_council_review(
        self,
        original_responses: Dict[str, Dict[str, Any]],
        review_prompt_template: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Stage 2: Each council member reviews others' responses anonymously.
        
        Args:
            original_responses: Dict of role -> response from Stage 1
            review_prompt_template: Template for review prompt
            
        Returns:
            Dict of role -> review response
        """
        tasks = {}
        
        for reviewer_role, reviewer_response in original_responses.items():
            if not reviewer_response.get("success"):
                continue
            
            other_responses = []
            for i, (role, resp) in enumerate(original_responses.items()):
                if role != reviewer_role and resp.get("success"):
                    other_responses.append(f"Respuesta {i+1}:\n{resp.get('content', '')}")
            
            if not other_responses:
                continue
            
            review_prompt = review_prompt_template.format(
                my_response=reviewer_response.get("content", ""),
                other_responses="\n\n---\n\n".join(other_responses)
            )
            
            model = COUNCIL_MODELS.get(reviewer_role, "anthropic/claude-3.5-sonnet")
            messages = [
                {"role": "system", "content": "Eres un revisor experto. Evalúa las respuestas de forma objetiva e imparcial."},
                {"role": "user", "content": review_prompt}
            ]
            tasks[reviewer_role] = self.call_model(model, messages)
        
        results = {}
        if tasks:
            responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for role, response in zip(tasks.keys(), responses):
                if isinstance(response, Exception):
                    results[role] = {"success": False, "error": str(response)}
                else:
                    results[role] = response
        
        return results
    
    async def chairman_synthesize(
        self,
        original_prompt: str,
        council_responses: Dict[str, Dict[str, Any]],
        reviews: Dict[str, Dict[str, Any]],
        chairman_system_prompt: str
    ) -> Dict[str, Any]:
        """
        Stage 3: Chairman synthesizes all responses into final answer.
        
        Args:
            original_prompt: The original user prompt
            council_responses: Stage 1 responses
            reviews: Stage 2 reviews
            chairman_system_prompt: System prompt for chairman
            
        Returns:
            Final synthesized response
        """
        synthesis_prompt = f"""
CONSULTA ORIGINAL:
{original_prompt}

RESPUESTAS DEL CONSEJO:
"""
        for role, resp in council_responses.items():
            if resp.get("success"):
                model_name = resp.get("model_name", role)
                synthesis_prompt += f"\n--- {role.upper()} ({model_name}) ---\n{resp.get('content', '')}\n"
        
        if reviews:
            synthesis_prompt += "\n\nREVISIONES CRUZADAS:\n"
            for role, review in reviews.items():
                if review.get("success"):
                    synthesis_prompt += f"\n--- Revisión de {role} ---\n{review.get('content', '')}\n"
        
        synthesis_prompt += """

INSTRUCCIONES:
Basándote en todas las perspectivas anteriores:
1. Identifica los puntos de consenso
2. Resuelve las discrepancias usando el mejor argumento
3. Elimina cualquier afirmación no fundamentada (alucinaciones)
4. Produce una respuesta final coherente y validada
"""
        
        chairman_model = COUNCIL_MODELS.get("chairman", "anthropic/claude-3.5-sonnet")
        messages = [
            {"role": "system", "content": chairman_system_prompt},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        return await self.call_model(chairman_model, messages, temperature=0.3)
    
    async def run_full_council(
        self,
        prompt: str,
        context: str = "",
        include_reviews: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete 3-stage LLM Council process.
        
        Args:
            prompt: The query to evaluate
            context: Additional context (RAG results, project data, etc.)
            include_reviews: Whether to run Stage 2 (cross-review)
            
        Returns:
            Complete council result with all stages
        """
        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXTO:\n{context}\n\nCONSULTA:\n{prompt}"
        
        system_prompts = {
            "fact_auditor": """Eres el Auditor de Hechos del Consejo de Estrategia.
Tu rol es verificar la precisión factual de las afirmaciones.
- Identifica afirmaciones que no están respaldadas por el contexto
- Señala posibles alucinaciones o invenciones
- Valida que los datos numéricos sean consistentes
- Cuestiona fuentes no verificables""",
            
            "business_strategist": """Eres el Estratega de Negocios del Consejo de Estrategia.
Tu rol es evaluar la solidez estratégica y comercial.
- Analiza la viabilidad del proyecto
- Evalúa riesgos y oportunidades
- Considera el contexto del mercado mexicano
- Identifica dependencias y supuestos críticos""",
            
            "devils_advocate": """Eres el Abogado del Diablo del Consejo de Estrategia.
Tu rol es cuestionar y desafiar las conclusiones.
- Busca debilidades en los argumentos
- Identifica sesgos cognitivos
- Propón escenarios adversos
- Cuestiona suposiciones implícitas"""
        }
        
        chairman_prompt = """Eres el Presidente del Consejo de Estrategia de Revisar.ia.
Tu rol es sintetizar las perspectivas del consejo y producir una evaluación final.
- Integra los puntos válidos de cada perspectiva
- Elimina afirmaciones no fundamentadas
- Resuelve contradicciones con argumentos sólidos
- Produce una conclusión clara y accionable
- Mantén un tono profesional y objetivo"""
        
        logger.info("🏛️ Council Stage 1: Gathering individual opinions...")
        stage1_responses = await self.call_council_parallel(full_prompt, system_prompts)
        
        reviews = {}
        if include_reviews:
            logger.info("🔍 Council Stage 2: Cross-review phase...")
            review_template = """
Mi análisis fue:
{my_response}

Otros análisis (anónimos):
{other_responses}

Evalúa objetivamente:
1. ¿Qué análisis tiene los argumentos más sólidos?
2. ¿Hay afirmaciones sin fundamento en alguno?
3. ¿Qué puntos deberían incluirse en la conclusión final?
"""
            reviews = await self.run_council_review(stage1_responses, review_template)
        
        logger.info("👨‍⚖️ Council Stage 3: Chairman synthesis...")
        final_response = await self.chairman_synthesize(
            full_prompt,
            stage1_responses,
            reviews,
            chairman_prompt
        )
        
        return {
            "success": final_response.get("success", False),
            "stage1_responses": stage1_responses,
            "stage2_reviews": reviews,
            "final_response": final_response.get("content", ""),
            "chairman_model": final_response.get("model_name", "Unknown"),
            "council_models": {
                role: resp.get("model_name", "Unknown") 
                for role, resp in stage1_responses.items()
            }
        }
    
    def run_full_council_sync(
        self,
        prompt: str,
        context: str = "",
        include_reviews: bool = True
    ) -> Dict[str, Any]:
        """Synchronous wrapper for run_full_council"""
        if not self.initialized:
            logger.warning("OpenRouter not initialized - returning fallback")
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "final_response": prompt,
                "fallback": True
            }
        
        try:
            return asyncio.run(
                self.run_full_council(prompt, context, include_reviews)
            )
        except Exception as e:
            logger.error(f"Council error: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_response": prompt,
                "fallback": True
            }


openrouter_service = OpenRouterService()
