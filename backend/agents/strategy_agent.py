"""
StrategyAgent: Quality Assurance Council for Anti-Hallucination

This agent implements a multi-persona council pattern (inspired by llm-council)
to validate PMO responses before they are sent to users.

The council consists of 3 specialized personas using DIFFERENT LLMs:
1. Fact Auditor (Claude 3.5 Sonnet) - Validates claims against RAG context
2. Business Strategist (Gemini 1.5 Pro) - Evaluates strategic alignment  
3. Devil's Advocate (GPT-4o) - Challenges assumptions and finds weaknesses
4. Chairman (Claude 3.5 Sonnet) - Synthesizes and produces final response

Architecture:
- STAGE 1 (CRITICS): 3 different LLMs critique the draft in parallel
- STAGE 2 (REVIEW): Each LLM reviews others' responses anonymously
- STAGE 3 (CHAIRMAN): Synthesize critiques, remove hallucinations, generate final response

Supports OpenRouter for multi-LLM access, with OpenAI fallback.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from services.query_router import route_query

OPENROUTER_MODELS = {
    "fact_auditor": "anthropic/claude-3.5-sonnet",
    "business_strategist": "google/gemini-pro-1.5",
    "devils_advocate": "openai/gpt-4o",
    "chairman": "anthropic/claude-3.5-sonnet",
}


def normalize_strategy_evaluation(data: Dict[str, Any], default_strategy: str = "") -> Dict[str, Any]:
    """
    Normalize strategy_evaluation to ensure consistent schema.
    Coerces types and provides defaults for all required fields.
    """
    if not isinstance(data, dict):
        data = {}
    
    if "strategy_evaluation" in data:
        eval_data = data["strategy_evaluation"]
        if not isinstance(eval_data, dict):
            eval_data = {}
    else:
        eval_data = data
    
    risk_score = eval_data.get("risk_score", 50)
    if isinstance(risk_score, str):
        try:
            risk_score = int(float(risk_score))
        except (ValueError, TypeError):
            risk_score = 50
    risk_score = max(0, min(100, int(risk_score)))
    
    hallucinations = eval_data.get("hallucinations_removed", [])
    if not isinstance(hallucinations, list):
        hallucinations = [hallucinations] if hallucinations else []
    hallucinations = [str(h) if not isinstance(h, str) else h for h in hallucinations]
    
    critiques = eval_data.get("critiques", [])
    if not isinstance(critiques, list):
        critiques = [critiques] if critiques else []
    normalized_critiques = []
    for c in critiques:
        if isinstance(c, dict):
            normalized_critiques.append({
                "perspective": str(c.get("perspective", "Unknown")),
                "observations": str(c.get("observations", ""))
            })
        elif isinstance(c, str):
            normalized_critiques.append({"perspective": "Unknown", "observations": c})
    
    final_strategy = eval_data.get("final_strategy", default_strategy)
    if not isinstance(final_strategy, str):
        final_strategy = str(final_strategy) if final_strategy else default_strategy
    
    consensus = eval_data.get("consensus", "")
    if not isinstance(consensus, str):
        consensus = str(consensus) if consensus else ""
    
    normalized = {
        "strategy_evaluation": {
            "critiques": normalized_critiques,
            "consensus": consensus or "Council evaluation complete",
            "hallucinations_removed": hallucinations,
            "final_strategy": final_strategy or default_strategy,
            "risk_score": risk_score
        }
    }
    
    for key in ["multi_llm_council", "models_used", "chairman_model"]:
        if key in eval_data:
            normalized["strategy_evaluation"][key] = eval_data[key]
        elif key in data:
            normalized["strategy_evaluation"][key] = data[key]
    
    merged_metadata = {"normalized": True}
    if isinstance(data.get("_metadata"), dict):
        merged_metadata.update(data["_metadata"])
    if isinstance(eval_data.get("_metadata"), dict):
        merged_metadata.update(eval_data["_metadata"])
    normalized["strategy_evaluation"]["_metadata"] = merged_metadata
    normalized["_metadata"] = merged_metadata
    
    if "error" in data:
        normalized["error"] = data["error"]
    if "error_code" in data:
        normalized["error_code"] = data["error_code"]
    if "message" in data:
        normalized["message"] = data["message"]
    
    return normalized


class StrategyAgent:
    """
    Quality Assurance Council Agent that filters hallucinations
    and validates strategy before PMO responds to users.
    """
    
    PERSONAS = {
        "fact_auditor": {
            "name": "Fact Auditor",
            "name_es": "Auditor de Hechos",
            "role": "Validates factual accuracy against source documents",
            "system_prompt": """You are a Fact Auditor for business documents. Your role is to:
1. Identify FACTUAL ERRORS - invented numbers, fake dates, non-existent companies, false regulatory citations
2. Professional analysis and recommendations are NOT hallucinations - they are valid content
3. Only flag content that contains objectively false factual claims
4. Strategic observations, risk assessments, and conclusions are VALID content

WHAT IS A HALLUCINATION (flag these):
- Invented percentages or statistics not in source data
- Fake document references with specific dates that don't exist
- Non-existent company names or people referenced as if real
- False legal article citations (e.g., citing Article 100 when it doesn't exist)

WHAT IS NOT A HALLUCINATION (do NOT flag):
- Professional recommendations and analysis
- Strategic observations based on the data
- Risk assessments and conclusions
- Synthesis of information from sources

Your output MUST be in JSON format:
{
    "hallucinations_found": [
        {"claim": "the problematic claim", "reason": "why it's unsupported"}
    ],
    "verified_claims": ["list of claims that ARE supported by context"],
    "accuracy_score": 0-100,
    "recommendation": "APPROVE/FLAG/REJECT"
}"""
        },
        "business_strategist": {
            "name": "Business Strategist",
            "name_es": "Estratega de Negocio",
            "role": "Evaluates strategic coherence and business value",
            "system_prompt": """You are a Business Strategist. Your role is to:
1. Evaluate if the response aligns with business objectives
2. Assess strategic coherence and practical applicability
3. Identify missing business considerations
4. Suggest improvements for business impact

Your output MUST be in JSON format:
{
    "strategic_alignment": "HIGH/MEDIUM/LOW",
    "strengths": ["list of strategic strengths"],
    "weaknesses": ["list of strategic gaps"],
    "missing_considerations": ["business factors not addressed"],
    "recommendation": "APPROVE/IMPROVE/REJECT"
}"""
        },
        "devils_advocate": {
            "name": "Devil's Advocate",
            "name_es": "Abogado del Diablo",
            "role": "Challenges assumptions and finds weaknesses",
            "system_prompt": """You are a Devil's Advocate. Your role is to:
1. Challenge every assumption in the draft
2. Find logical flaws and contradictions
3. Identify potential risks or unintended consequences
4. Question the validity of conclusions

Your output MUST be in JSON format:
{
    "challenged_assumptions": [
        {"assumption": "the assumption", "challenge": "why it might be wrong"}
    ],
    "logical_flaws": ["list of logical issues"],
    "risks_identified": ["potential negative outcomes"],
    "counterarguments": ["alternative viewpoints"],
    "robustness_score": 0-100
}"""
        }
    }
    
    CHAIRMAN_PROMPT = """You are the Chairman of a Quality Assurance Council for Revisar.IA's multi-agent system.
You have received critiques from three specialized auditors:
1. Fact Auditor - checked for factual accuracy against source documents
2. Business Strategist - evaluated strategic alignment
3. Devil's Advocate - challenged assumptions

CRITICAL RULES:
1. PRESERVE the original draft structure and language (Spanish if the draft is in Spanish)
2. Only remove FACTUAL errors: invented numbers, fake dates, non-existent people, false claims
3. Analysis, opinions, and synthesis are VALID content - do not remove them
4. If the draft is in Spanish, your final_strategy MUST also be in Spanish
5. The final_strategy should be at least as long as the original draft
6. Do NOT summarize or shorten the content - preserve the full detail

WHAT IS A HALLUCINATION (remove these):
- Invented statistics or percentages not in source data
- Fake document references or dates
- Non-existent company names or people
- False regulatory article citations

WHAT IS NOT A HALLUCINATION (keep these):
- Professional analysis and recommendations
- Strategic observations and conclusions
- Risk assessments based on the data
- Synthesis of deliberation content

Your output MUST be in this EXACT JSON format:
{
    "strategy_evaluation": {
        "critiques": [
            {"perspective": "Fact Auditor", "observations": "summary of findings"},
            {"perspective": "Business Strategist", "observations": "summary of findings"},
            {"perspective": "Devil's Advocate", "observations": "summary of findings"}
        ],
        "consensus": "brief summary of council resolution",
        "hallucinations_removed": ["list of FACTUAL errors removed (invented data only)"],
        "final_strategy": "THE COMPLETE, VALIDATED RESPONSE IN THE SAME LANGUAGE AS ORIGINAL",
        "risk_score": 0-100
    }
}"""

    def __init__(self):
        """Initialize the StrategyAgent with OpenRouter (preferred) or OpenAI fallback."""
        self.openrouter_service = None
        self.openai_client = None
        self.use_openrouter = False
        self.model = "gpt-4o"
        
        openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
        if openrouter_key:
            try:
                from services.openrouter_service import OpenRouterService
                self.openrouter_service = OpenRouterService()
                if self.openrouter_service.initialized:
                    self.use_openrouter = True
                    logger.info("StrategyAgent initialized with OpenRouter (multi-LLM council)")
            except Exception as e:
                logger.warning(f"OpenRouter not available: {e}")
        
        if not self.use_openrouter:
            openai_key = os.environ.get('OPENAI_API_KEY', '')
            if openai_key:
                try:
                    from openai import OpenAI
                    self.openai_client = OpenAI(api_key=openai_key)
                    logger.info("StrategyAgent initialized with OpenAI GPT-4o (single-LLM fallback)")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
            else:
                logger.warning("No LLM API keys found - StrategyAgent will use passthrough mode")
    
    @property
    def client(self):
        """Backward compatibility property"""
        return self.openai_client
    
    async def review_and_strategize(
        self,
        context_data: Dict[str, Any],
        proposed_draft: str
    ) -> Dict[str, Any]:
        """
        Main entry point: Review PMO draft through multi-persona council.
        
        Args:
            context_data: Dict containing 'rag_context' (list of source documents)
            proposed_draft: The PMO's proposed response to validate
            
        Returns:
            Dict with strategy_evaluation containing critiques, consensus, 
            final_strategy, and risk_score
        """
        try:
            rag_context = context_data.get('rag_context', [])
            if isinstance(rag_context, list):
                rag_context_str = "\n---\n".join(rag_context)
            else:
                rag_context_str = str(rag_context)
            
            if self.use_openrouter and self.openrouter_service:
                logger.info("🏛️ StrategyAgent: Using OpenRouter multi-LLM Council")
                return await self._run_openrouter_council(rag_context_str, proposed_draft)
            
            if not self.openai_client:
                fallback = self._fallback_response(proposed_draft, "No LLM client available")
                return normalize_strategy_evaluation(fallback, proposed_draft)
            
            logger.info("StrategyAgent: Starting CRITICS PHASE (3 personas - single LLM)")
            critiques = await self._critics_phase(rag_context_str, proposed_draft)
            
            logger.info("StrategyAgent: Starting CHAIRMAN PHASE (synthesis)")
            final_result = await self._chairman_phase(
                rag_context_str, 
                proposed_draft, 
                critiques
            )
            
            return final_result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in StrategyAgent: {e}")
            error_resp = self._error_response("JSON_PARSE_ERROR", str(e), proposed_draft)
            return normalize_strategy_evaluation(error_resp, proposed_draft)
        except Exception as e:
            logger.error(f"Error in StrategyAgent: {e}")
            error_resp = self._error_response("PROCESSING_ERROR", str(e), proposed_draft)
            return normalize_strategy_evaluation(error_resp, proposed_draft)
    
    async def _run_openrouter_council(
        self,
        rag_context: str,
        proposed_draft: str
    ) -> Dict[str, Any]:
        """
        Run the full multi-LLM council using OpenRouter.
        Each persona uses a DIFFERENT LLM for true multi-perspective validation.
        
        Stage 1: Claude (Fact Auditor), Gemini (Strategist), GPT-4o (Devil's Advocate)
        Stage 2: Cross-review between LLMs
        Stage 3: Claude Chairman synthesizes final response
        """
        full_prompt = f"""## CONTEXTO RAG (Documentos Fuente - ÚNICA FUENTE DE VERDAD):
{rag_context}

## BORRADOR A REVISAR:
{proposed_draft}

Analiza el borrador contra el contexto RAG. Identifica:
1. Afirmaciones no respaldadas por el contexto (alucinaciones)
2. Debilidades estratégicas o lógicas
3. Riesgos no considerados

Proporciona tu análisis en español."""

        system_prompts = {
            "fact_auditor": """Eres el Auditor de Hechos (Claude 3.5 Sonnet).
Tu rol es verificar la precisión factual contra los documentos fuente:
- Compara CADA afirmación contra el contexto RAG
- Identifica información que NO está en el contexto (ALUCINACIÓN)
- Señala datos inventados o no verificables
- Sé extremadamente estricto: si no está en el contexto, es alucinación

Responde en JSON:
{
    "hallucinations_found": [{"claim": "...", "reason": "..."}],
    "verified_claims": ["..."],
    "accuracy_score": 0-100,
    "recommendation": "APPROVE/FLAG/REJECT"
}""",
            
            "business_strategist": """Eres el Estratega de Negocios (Gemini 1.5 Pro).
Tu rol es evaluar la coherencia estratégica y valor comercial:
- Evalúa si la respuesta alinea con objetivos de negocio
- Considera el contexto del mercado mexicano
- Identifica consideraciones de negocio faltantes
- Sugiere mejoras para impacto comercial

Responde en JSON:
{
    "strategic_alignment": "HIGH/MEDIUM/LOW",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "missing_considerations": ["..."],
    "recommendation": "APPROVE/IMPROVE/REJECT"
}""",
            
            "devils_advocate": """Eres el Abogado del Diablo (GPT-4o).
Tu rol es desafiar suposiciones y encontrar debilidades:
- Cuestiona cada suposición en el borrador
- Busca fallas lógicas y contradicciones
- Identifica riesgos potenciales
- Propón contraargumentos

Responde en JSON:
{
    "challenged_assumptions": [{"assumption": "...", "challenge": "..."}],
    "logical_flaws": ["..."],
    "risks_identified": ["..."],
    "counterarguments": ["..."],
    "robustness_score": 0-100
}"""
        }
        
        logger.info("🏛️ Council Stage 1: Claude, Gemini, GPT-4o analizando en paralelo...")
        stage1 = await self.openrouter_service.call_council_parallel(
            full_prompt,
            system_prompts,
            OPENROUTER_MODELS
        )
        
        logger.info("🔍 Council Stage 2: Revisión cruzada anónima...")
        review_template = """Mi análisis fue:
{my_response}

Otros análisis (anónimos):
{other_responses}

Evalúa objetivamente:
1. ¿Qué análisis tiene los argumentos más sólidos?
2. ¿Hay afirmaciones sin fundamento en alguno?
3. ¿Qué puntos deberían incluirse en la conclusión final?"""
        
        stage2 = await self.openrouter_service.run_council_review(stage1, review_template)
        
        chairman_prompt = """Eres el Presidente del Consejo de Estrategia de Revisar.ia.
Has recibido análisis de tres expertos usando diferentes IAs:
- Auditor de Hechos (Claude): Verificó precisión factual
- Estratega de Negocios (Gemini): Evaluó alineación estratégica
- Abogado del Diablo (GPT-4o): Desafió suposiciones

REGLAS CRÍTICAS:
1. Si el Auditor encontró alucinaciones, DEBEN ELIMINARSE del resultado final
2. El contexto RAG es la ÚNICA fuente de verdad
3. Sintetiza los mejores elementos eliminando contenido problemático
4. Genera una respuesta final limpia y validada

Tu respuesta DEBE ser JSON:
{
    "strategy_evaluation": {
        "critiques": [
            {"perspective": "Auditor de Hechos (Claude)", "observations": "resumen"},
            {"perspective": "Estratega (Gemini)", "observations": "resumen"},
            {"perspective": "Abogado del Diablo (GPT)", "observations": "resumen"}
        ],
        "consensus": "resumen de resolución del consejo",
        "hallucinations_removed": ["lista de afirmaciones eliminadas"],
        "final_strategy": "LA RESPUESTA FINAL VALIDADA",
        "risk_score": 0-100,
        "council_models_used": ["claude-3.5-sonnet", "gemini-pro-1.5", "gpt-4o"]
    }
}"""
        
        logger.info("👨‍⚖️ Council Stage 3: Chairman (Claude) sintetizando...")
        
        try:
            final = await self.openrouter_service.chairman_synthesize(
                full_prompt,
                stage1,
                stage2,
                chairman_prompt
            )
        except Exception as e:
            logger.error(f"Chairman synthesis failed: {e}")
            logger.info("Falling back to single-LLM pipeline...")
            return await self._fallback_to_single_llm(rag_context, proposed_draft)
        
        if not final.get("success") or not final.get("content"):
            logger.warning("OpenRouter council failed, falling back to single-LLM")
            return await self._fallback_to_single_llm(rag_context, proposed_draft)
        
        models_used = {}
        for role, resp in stage1.items():
            if resp.get("success"):
                models_used[role] = resp.get("model_name", "unknown")
            else:
                models_used[role] = f"FAILED: {resp.get('error', 'unknown error')}"
        
        try:
            result = json.loads(final["content"])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse chairman JSON: {e}")
            result = {
                "final_strategy": final["content"],
                "consensus": "Council synthesis completed (non-JSON response)"
            }
        
        result["multi_llm_council"] = True
        result["models_used"] = models_used
        result["chairman_model"] = "Claude 3.5 Sonnet"
        
        normalized = normalize_strategy_evaluation(result, proposed_draft)
        normalized["strategy_evaluation"]["multi_llm_council"] = True
        normalized["strategy_evaluation"]["models_used"] = models_used
        normalized["strategy_evaluation"]["chairman_model"] = "Claude 3.5 Sonnet"
        
        logger.info("✅ Multi-LLM Council completed successfully")
        return normalized
    
    async def _fallback_to_single_llm(self, rag_context: str, proposed_draft: str) -> Dict[str, Any]:
        """Fallback to single-LLM pipeline when OpenRouter fails"""
        if self.openai_client:
            logger.info("Using OpenAI single-LLM fallback")
            try:
                critiques = await self._critics_phase(rag_context, proposed_draft)
                result = await self._chairman_phase(rag_context, proposed_draft, critiques)
                
                existing_metadata = result.get("_metadata", {})
                if not isinstance(existing_metadata, dict):
                    existing_metadata = {}
                existing_metadata["fallback_mode"] = "single_llm_openai"
                result["_metadata"] = existing_metadata
                
                normalized = normalize_strategy_evaluation(result, proposed_draft)
                normalized["strategy_evaluation"]["multi_llm_council"] = False
                
                return normalized
            except Exception as e:
                logger.error(f"Single-LLM fallback failed: {e}")
                fallback = self._fallback_response(proposed_draft, f"Single-LLM fallback error: {str(e)}")
                return normalize_strategy_evaluation(fallback, proposed_draft)
        else:
            fallback = self._fallback_response(proposed_draft, "All LLM backends unavailable")
            return normalize_strategy_evaluation(fallback, proposed_draft)
    
    async def _critics_phase(
        self, 
        rag_context: str, 
        draft: str
    ) -> Dict[str, Any]:
        """
        CRITICS PHASE: Run 3 personas in parallel to critique the draft.
        
        Returns dict with each persona's critique.
        """
        tasks = []
        for persona_id, persona_config in self.PERSONAS.items():
            task = self._get_persona_critique(
                persona_id,
                persona_config,
                rag_context,
                draft
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        critiques = {}
        for persona_id, result in zip(self.PERSONAS.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Persona {persona_id} failed: {result}")
                critiques[persona_id] = {"error": str(result)}
            else:
                critiques[persona_id] = result
        
        return critiques
    
    async def _get_persona_critique(
        self,
        persona_id: str,
        persona_config: Dict[str, Any],
        rag_context: str,
        draft: str
    ) -> Dict[str, Any]:
        """Get critique from a single persona."""
        if not self.client:
            return {"error": "OpenAI client not available", "skipped": True}
        
        user_prompt = f"""## RAG CONTEXT (Source Documents - ONLY SOURCE OF TRUTH):
{rag_context}

## DRAFT TO REVIEW:
{draft}

Analyze the draft against the RAG context and provide your critique in the specified JSON format."""

        content: Optional[str] = None
        try:
            enable_router = os.getenv("ENABLE_QUERY_ROUTER", "true").lower() == "true"
            messages = [
                {"role": "system", "content": persona_config["system_prompt"]},
                {"role": "user", "content": user_prompt}
            ]
            
            if enable_router:
                routing = route_query(
                    prompt=user_prompt,
                    task_type="validation"
                )
                selected_model = routing["model"]
                logger.info(f"🎯 Strategy Router (Persona): {routing['model']} | Tokens: {routing['token_count']} | Cost: ${routing['estimated_cost']:.6f} | {routing['reasoning']}")
            else:
                selected_model = self.model
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
            )
            
            content = response.choices[0].message.content
            if content is None:
                return {"error": "Empty response from model", "skipped": True}
            return json.loads(content)
            
        except json.JSONDecodeError:
            return {"raw_response": content or "", "parse_error": True}
        except Exception as e:
            raise e
    
    async def _chairman_phase(
        self,
        rag_context: str,
        original_draft: str,
        critiques: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CHAIRMAN PHASE: Synthesize critiques and generate final validated response.
        
        Critical: If Fact Auditor found hallucinations, they MUST be removed.
        """
        if not self.client:
            return self._fallback_synthesis(critiques, original_draft)
        
        critiques_summary = self._format_critiques_for_chairman(critiques)
        
        user_prompt = f"""## RAG CONTEXT (SOURCE DATA):
{rag_context}

## ORIGINAL DRAFT (PRESERVE THIS CONTENT):
{original_draft}

## COUNCIL CRITIQUES:
{critiques_summary}

IMPORTANT INSTRUCTIONS:
1. The ORIGINAL DRAFT is a valid professional report - PRESERVE its structure and content
2. Only remove FACTUAL ERRORS (invented numbers, fake dates, false claims)
3. Analysis and recommendations are VALID content - DO NOT remove them
4. If the original is in SPANISH, your final_strategy MUST be in SPANISH
5. Do NOT shorten or summarize - maintain the full length and detail
6. Return the cleaned report in final_strategy field

Provide your synthesis in the specified JSON format."""

        try:
            enable_router = os.getenv("ENABLE_QUERY_ROUTER", "true").lower() == "true"
            messages = [
                {"role": "system", "content": self.CHAIRMAN_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            if enable_router:
                routing = route_query(
                    prompt=user_prompt,
                    task_type="reasoning"
                )
                selected_model = routing["model"]
                logger.info(f"🎯 Strategy Router (Chairman): {routing['model']} | Tokens: {routing['token_count']} | Cost: ${routing['estimated_cost']:.6f}")
            else:
                selected_model = self.model
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=4500,
                    response_format={"type": "json_object"}
                )
            )
            
            content = response.choices[0].message.content
            if content is None:
                fallback = self._fallback_synthesis(critiques, original_draft)
                return normalize_strategy_evaluation(fallback, original_draft)
            result = json.loads(content)
            
            result["_metadata"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.model,
                "council_version": "1.0"
            }
            
            return normalize_strategy_evaluation(result, original_draft)
            
        except json.JSONDecodeError as e:
            logger.error(f"Chairman JSON parse error: {e}")
            fallback = self._fallback_synthesis(critiques, original_draft)
            return normalize_strategy_evaluation(fallback, original_draft)
        except Exception as e:
            logger.error(f"Chairman phase error: {e}")
            raise e
    
    def _format_critiques_for_chairman(self, critiques: Dict[str, Any]) -> str:
        """Format all persona critiques for the chairman to review."""
        formatted = []
        
        for persona_id, critique in critiques.items():
            persona_name = self.PERSONAS[persona_id]["name"]
            formatted.append(f"### {persona_name}:\n{json.dumps(critique, indent=2, ensure_ascii=False)}")
        
        return "\n\n".join(formatted)
    
    def _fallback_synthesis(
        self, 
        critiques: Dict[str, Any], 
        original_draft: str
    ) -> Dict[str, Any]:
        """Fallback when chairman fails - basic synthesis without LLM."""
        hallucinations = []
        fact_audit = critiques.get("fact_auditor", {})
        if isinstance(fact_audit, dict):
            hallucinations = fact_audit.get("hallucinations_found", [])
        
        risk_score = 50
        if hallucinations:
            risk_score = min(100, 50 + len(hallucinations) * 15)
        
        return {
            "strategy_evaluation": {
                "critiques": [
                    {
                        "perspective": self.PERSONAS[pid]["name"],
                        "observations": json.dumps(critique, ensure_ascii=False)[:500]
                    }
                    for pid, critique in critiques.items()
                ],
                "consensus": "Fallback synthesis - manual review recommended",
                "hallucinations_removed": [h.get("claim", str(h)) for h in hallucinations] if hallucinations else [],
                "final_strategy": original_draft if not hallucinations else "[REQUIRES MANUAL REVIEW - Hallucinations detected]",
                "risk_score": risk_score
            },
            "_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "fallback_mode": True
            }
        }
    
    def _fallback_response(self, draft: str, reason: str) -> Dict[str, Any]:
        """Return when OpenAI is not available."""
        return {
            "strategy_evaluation": {
                "critiques": [
                    {"perspective": "Fact Auditor", "observations": f"Skipped: {reason}"},
                    {"perspective": "Business Strategist", "observations": f"Skipped: {reason}"},
                    {"perspective": "Devil's Advocate", "observations": f"Skipped: {reason}"}
                ],
                "consensus": f"Council skipped: {reason}. Draft passed through without validation.",
                "hallucinations_removed": [],
                "final_strategy": draft,
                "risk_score": 75
            },
            "_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "fallback_mode": True,
                "reason": reason
            }
        }
    
    def _error_response(self, error_code: str, message: str, draft: str = "") -> Dict[str, Any]:
        """Return structured error response with valid strategy_evaluation."""
        return {
            "error": True,
            "error_code": error_code,
            "message": message,
            "strategy_evaluation": {
                "critiques": [],
                "consensus": f"Error: {error_code} - {message}",
                "hallucinations_removed": [],
                "final_strategy": draft if draft else "[Error occurred - original draft not available]",
                "risk_score": 100
            },
            "_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "error_mode": True
            }
        }
    
    def validate_against_context(
        self, 
        claim: str, 
        rag_context: List[str]
    ) -> bool:
        """
        Utility method: Check if a specific claim exists in RAG context.
        Returns True if the claim is supported, False if it's a potential hallucination.
        """
        context_text = " ".join(rag_context).lower()
        claim_lower = claim.lower()
        
        claim_words = [w for w in claim_lower.split() if len(w) > 3]
        
        if not claim_words:
            return True
        
        matches = sum(1 for word in claim_words if word in context_text)
        match_ratio = matches / len(claim_words)
        
        return match_ratio >= 0.5


strategy_agent = StrategyAgent()
