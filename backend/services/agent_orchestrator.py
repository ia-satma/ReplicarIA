"""
agent_orchestrator.py - Orquestador de Agentes Optimizado para REVISAR.IA
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import json
import os

AGENTS_CONFIG = {
    "A1_RECEPCION": {
        "name": "Agente de Recepción",
        "role": "Recibir y clasificar documentos del contribuyente",
        "capabilities": ["clasificación", "extracción_datos", "validación_inicial"],
        "system_prompt": """Eres el Agente de Recepción de REVISAR.IA. Tu función es:
1. Recibir documentos fiscales del contribuyente
2. Clasificar el tipo de documento (CFDI, contrato, póliza de pago, etc.)
3. Extraer datos clave (RFC, monto, fecha, concepto)
4. Validar completitud inicial
Siempre responde en español con formato estructurado."""
    },
    "A2_ANALISIS": {
        "name": "Agente de Análisis Fiscal",
        "role": "Analizar implicaciones fiscales de operaciones",
        "capabilities": ["análisis_fiscal", "deducibilidad", "ISR", "IVA"],
        "system_prompt": """Eres el Agente de Análisis Fiscal de REVISAR.IA. Tu función es:
1. Analizar la naturaleza fiscal de las operaciones
2. Evaluar deducibilidad conforme al Art. 27 LISR
3. Identificar requisitos fiscales aplicables
4. Detectar riesgos de rechazo de deducciones
Cita siempre los artículos de ley aplicables."""
    },
    "A3_NORMATIVO": {
        "name": "Agente Normativo",
        "role": "Verificar cumplimiento de normatividad fiscal",
        "capabilities": ["CFF", "LISR", "LIVA", "criterios_SAT"],
        "system_prompt": """Eres el Agente Normativo de REVISAR.IA. Tu función es:
1. Verificar cumplimiento del CFF
2. Validar requisitos de LISR y LIVA
3. Consultar criterios no vinculativos del SAT
4. Identificar riesgos normativos
Fundamenta cada conclusión con artículos específicos."""
    },
    "A4_CONTABLE": {
        "name": "Agente Contable",
        "role": "Validar registro y soporte contable",
        "capabilities": ["NIF", "registro_contable", "pólizas", "conciliaciones"],
        "system_prompt": """Eres el Agente Contable de REVISAR.IA. Tu función es:
1. Validar registro contable conforme a NIF
2. Verificar pólizas contables
3. Revisar conciliaciones
4. Evaluar soporte documental contable
Indica las NIF aplicables en cada caso."""
    },
    "A5_OPERATIVO": {
        "name": "Agente Operativo",
        "role": "Validar materialidad y sustancia operativa",
        "capabilities": ["materialidad", "sustancia", "evidencia_operativa"],
        "system_prompt": """Eres el Agente Operativo de REVISAR.IA. Tu función es:
1. Validar la materialidad de las operaciones
2. Verificar evidencia de sustancia económica
3. Revisar entregables y evidencia de servicios
4. Evaluar capacidad operativa del proveedor
Detalla qué evidencia específica se requiere."""
    },
    "A6_FINANCIERO": {
        "name": "Agente Financiero",
        "role": "Analizar flujos financieros y bancarización",
        "capabilities": ["bancarización", "flujos", "pagos", "rastreo"],
        "system_prompt": """Eres el Agente Financiero de REVISAR.IA. Tu función es:
1. Validar bancarización de pagos >$2,000
2. Verificar flujos financieros
3. Rastrear origen y destino de fondos
4. Evaluar cumplimiento de requisitos de pago
Indica montos y fechas específicas."""
    },
    "A7_LEGAL": {
        "name": "Agente Legal",
        "role": "Revisar aspectos contractuales y legales",
        "capabilities": ["contratos", "obligaciones", "disputas", "representación"],
        "system_prompt": """Eres el Agente Legal de REVISAR.IA. Tu función es:
1. Revisar contratos y obligaciones
2. Validar poderes y representación legal
3. Identificar riesgos contractuales
4. Evaluar cláusulas relevantes para defensa fiscal
Señala cláusulas específicas del contrato."""
    },
    "A8_REDTEAM": {
        "name": "Agente Red Team",
        "role": "Simular objeciones del SAT",
        "capabilities": ["objeciones", "simulación_SAT", "contraargumentos"],
        "system_prompt": """Eres el Agente Red Team de REVISAR.IA. Tu función es:
1. Simular objeciones que haría el SAT
2. Identificar debilidades en el expediente
3. Proponer contraargumentos
4. Evaluar probabilidad de éxito en defensa
Actúa como un auditor fiscal del SAT."""
    },
    "A9_SINTESIS": {
        "name": "Agente de Síntesis",
        "role": "Consolidar análisis y generar reporte final",
        "capabilities": ["síntesis", "reporte", "conclusiones", "recomendaciones"],
        "system_prompt": """Eres el Agente de Síntesis de REVISAR.IA. Tu función es:
1. Consolidar análisis de todos los agentes
2. Generar conclusiones ponderadas
3. Calcular score de riesgo/compliance
4. Emitir dictamen final con recomendaciones
Estructura tu respuesta para el Defense File."""
    },
    "A10_ARCHIVO": {
        "name": "Agente de Archivo",
        "role": "Organizar y catalogar el expediente",
        "capabilities": ["catalogación", "índice", "trazabilidad", "exportación"],
        "system_prompt": """Eres el Agente de Archivo de REVISAR.IA. Tu función es:
1. Organizar documentos del expediente
2. Generar índice y tabla de contenido
3. Asegurar trazabilidad de evidencia
4. Preparar expediente para exportación PDF
Lista los documentos y su ubicación."""
    },
}


@dataclass
class AgentContext:
    """Contexto de ejecución del agente."""
    empresa_id: str
    project_id: str
    user_id: str
    agent_id: str
    conversation_history: List[dict] = field(default_factory=list)
    rag_context: str = ""
    related_deliberations: List[dict] = field(default_factory=list)


class AgentOrchestrator:
    """Orquestador de Agentes Multi-Tenant."""
    
    def __init__(self):
        self.agents = AGENTS_CONFIG
        self._claude = None
        self._vector_search = None
        self._cache = None
    
    @property
    def llm_client(self):
        if self._claude is None:
            from services.openai_provider import openai_client
            self._claude = openai_client
        return self._claude
    
    @property
    def vector_search(self):
        if self._vector_search is None:
            try:
                from services.vector_search_service import VectorSearchService
                self._vector_search = VectorSearchService()
            except (ImportError, Exception) as e:
                logging.debug(f"Vector search not available: {e}")
                self._vector_search = None
        return self._vector_search

    @property
    def cache(self):
        if self._cache is None:
            try:
                from services.cache_service import get_cache
                self._cache = get_cache()
            except (ImportError, Exception) as e:
                logging.debug(f"Cache not available: {e}")
                self._cache = None
        return self._cache
    
    async def process_request(
        self,
        empresa_id: str,
        project_id: str,
        user_id: str,
        user_message: str,
        target_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Procesa una solicitud usando los agentes apropiados."""
        trace_id = str(uuid4())[:8]
        start_time = datetime.utcnow()
        
        if target_agents:
            agents_to_invoke = target_agents
        else:
            agents_to_invoke = self._select_agents(user_message)
        
        rag_context = await self._get_rag_context(empresa_id, user_message)
        
        context = AgentContext(
            empresa_id=empresa_id,
            project_id=project_id,
            user_id=user_id,
            agent_id="orchestrator",
            rag_context=rag_context,
        )
        
        results = await self._execute_agents_parallel(
            agents=agents_to_invoke,
            user_message=user_message,
            context=context,
            trace_id=trace_id,
        )
        
        if len(results) > 1:
            final_response = await self._synthesize_responses(results, context)
        else:
            final_response = results[0] if results else {"error": "No agent response"}
        
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "trace_id": trace_id,
            "agents_invoked": agents_to_invoke,
            "response": final_response,
            "rag_context_used": bool(rag_context),
            "elapsed_ms": elapsed_ms,
        }
    
    def _select_agents(self, user_message: str) -> List[str]:
        """Selecciona automáticamente los agentes apropiados."""
        agent_keywords = {
            "A1_RECEPCION": ["documento", "subir", "cargar", "archivo", "cfdi"],
            "A2_ANALISIS": ["deducible", "deducción", "impuesto", "fiscal", "ISR", "requisitos"],
            "A3_NORMATIVO": ["ley", "artículo", "CFF", "LISR", "norma", "SAT"],
            "A4_CONTABLE": ["contable", "póliza", "NIF", "registro", "cuenta"],
            "A5_OPERATIVO": ["materialidad", "operación", "servicio", "entregable"],
            "A6_FINANCIERO": ["pago", "banco", "transferencia", "flujo", "dinero"],
            "A7_LEGAL": ["contrato", "legal", "cláusula", "obligación"],
            "A8_REDTEAM": ["objeción", "SAT", "auditoría", "riesgo", "defensa"],
            "A9_SINTESIS": ["resumen", "conclusión", "reporte", "dictamen"],
            "A10_ARCHIVO": ["expediente", "documento", "índice", "archivo"],
        }
        
        message_lower = user_message.lower()
        selected = []
        
        for agent_id, keywords in agent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                selected.append(agent_id)
        
        return selected if selected else ["A2_ANALISIS"]
    
    async def _get_rag_context(self, empresa_id: str, query: str) -> str:
        """Obtiene contexto RAG del knowledge base."""
        if not self.vector_search:
            return ""
        
        try:
            results = await self.vector_search.hybrid_search(
                empresa_id=empresa_id,
                query=query,
                limit=5,
            )
            
            if not results:
                return ""
            
            context_parts = []
            for i, result in enumerate(results, 1):
                context_parts.append(
                    f"[Doc {i}: {result.get('filename', 'N/A')}]\n"
                    f"{result.get('contenido', '')}\n"
                )

            return "\n---\n".join(context_parts)
        except Exception as e:
            logging.warning(f"RAG context retrieval failed: {e}")
            return ""
    
    async def _execute_agents_parallel(
        self,
        agents: List[str],
        user_message: str,
        context: AgentContext,
        trace_id: str,
    ) -> List[dict]:
        """Ejecuta múltiples agentes en paralelo con manejo de errores."""
        tasks = [
            self._invoke_agent(agent_id, user_message, context, trace_id)
            for agent_id in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_id = agents[i]
                logging.error(f"Error executing agent {agent_id}: {result}", exc_info=True)
                valid_results.append({
                    "agent_id": agent_id,
                    "agent_name": self.agents.get(agent_id, {}).get("name", "Unknown"),
                    "response": f"Error ejecutando agente: {str(result)}",
                    "error": True, 
                    "trace_id": trace_id
                })
            else:
                valid_results.append(result)
                
        return valid_results
    
    async def _invoke_agent(
        self,
        agent_id: str,
        user_message: str,
        context: AgentContext,
        trace_id: str,
    ) -> dict:
        """Invoca un agente individual con soporte para tools."""
        from services.tools.registry import registry
        
        agent_config = self.agents.get(agent_id)
        if not agent_config:
            raise ValueError(f"Agente no encontrado: {agent_id}")
            
        # Get all tools (in a real app, filter by agent permissions)
        available_tools = registry.get_openai_tools() if agent_id in ["A3_FISCAL", "A5_OPERATIVO", "A6_FINANCIERO"] else None
        
        system_prompt = f"""{agent_config['system_prompt']}

CONTEXTO DEL TENANT:
- Empresa ID: {context.empresa_id}
- Proyecto ID: {context.project_id}

Responde SOLO con información relevante para este tenant."""
        
        start_time = datetime.utcnow()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONSULTA: {user_message}" + (f"\n\nDOCUMENTOS RELEVANTES:\n{context.rag_context}" if context.rag_context else "")}
        ]
        
        # 1. First LLM Call
        response = await asyncio.to_thread(
            self.llm_client.chat.completions.create,
            model="gpt-4o",
            max_tokens=4096,
            temperature=0.3,
            messages=messages,
            tools=available_tools,
            tool_choice="auto" if available_tools else None
        )
        
        response_msg = response.choices[0].message
        tool_calls = response_msg.tool_calls
        
        # 2. Handle Tool Calls
        if tool_calls:
            # Add assistant's message with tool calls
            messages.append(response_msg)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute tool
                tool_result = await registry.invoke(function_name, function_args)
                
                # Add tool result
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_result, default=str)
                })
            
            # 3. Second LLM Call (with tool results)
            response = await asyncio.to_thread(
                self.llm_client.chat.completions.create,
                model="gpt-4o",
                max_tokens=4096,
                temperature=0.3,
                messages=messages
            )
            final_content = response.choices[0].message.content
        else:
            final_content = response_msg.content

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "agent_id": agent_id,
            "agent_name": agent_config["name"],
            "response": final_content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            "elapsed_ms": elapsed_ms,
            "trace_id": trace_id,
        }
    
    async def _synthesize_responses(
        self,
        results: List[dict],
        context: AgentContext,
    ) -> dict:
        """Sintetiza respuestas de múltiples agentes."""
        agent_responses = "\n\n".join([
            f"## {r['agent_name']}\n{r['response']}"
            for r in results
        ])
        
        synthesis_prompt = f"""Consolida las siguientes respuestas de los agentes en una respuesta coherente:

{agent_responses}

INSTRUCCIONES:
1. Identifica los puntos clave
2. Genera una conclusión consolidada
3. Incluye un score de riesgo/compliance (0-100)
4. Lista las recomendaciones principales"""
        
        response = await asyncio.to_thread(
            self.llm_client.chat.completions.create,
            model="gpt-4o",
            max_tokens=4096,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Eres el Agente de Síntesis de REVISAR.IA."},
                {"role": "user", "content": synthesis_prompt}
            ],
        )

        return {
            "synthesized": True,
            "response": response.choices[0].message.content,
            "individual_responses": results,
        }


_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
