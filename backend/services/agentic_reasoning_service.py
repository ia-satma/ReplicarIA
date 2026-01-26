import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# OpenAI client setup (replaces Anthropic)
try:
    from services.openai_provider import openai_client, chat_completion_sync, is_configured
    OPENAI_AVAILABLE = is_configured()
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None
    logger.warning("OpenAI provider not available for AgenticReasoningService")

from config.agents_config import AGENT_CONFIGURATIONS
from services.query_router import route_query
from agents.pmo_integration import validate_pmo_response_sync

COMPLIANCE_PILLARS = {
    "razon_de_negocios": {
        "name": "Razón de Negocios",
        "article": "Art. 5-A CFF",
        "description": "Justificación económica y estratégica del servicio",
        "keywords": ["razón de negocios", "justificación económica", "propósito empresarial", "beneficio corporativo"]
    },
    "beneficio_economico": {
        "name": "Beneficio Económico Esperado",
        "article": "Art. 5-A CFF",
        "description": "ROI y valor tangible esperado del servicio",
        "keywords": ["beneficio económico", "roi", "retorno", "valor", "ahorro", "eficiencia"]
    },
    "materialidad": {
        "name": "Materialidad del Servicio",
        "article": "Art. 69-B CFF",
        "description": "Evidencia de que el servicio fue efectivamente prestado",
        "keywords": ["materialidad", "evidencia", "entregables", "documentación", "comprobación"]
    },
    "trazabilidad": {
        "name": "Trazabilidad",
        "article": "NOM-151",
        "description": "Cadena de evidencia documental completa",
        "keywords": ["trazabilidad", "cadena", "registro", "audit trail", "documentación"]
    }
}


class AgenticReasoningService:
    def __init__(self):
        self.client = openai_client
        self.model = "gpt-4o"

        if OPENAI_AVAILABLE:
            logger.info("✅ AgenticReasoningService initialized with OpenAI")
        else:
            logger.warning("OpenAI not configured - agentic reasoning will be limited")
    
    def get_agent_system_prompt(self, agent_id: str, include_rag_context: bool = True) -> str:
        agent_config = AGENT_CONFIGURATIONS.get(agent_id, {})
        base_prompt = agent_config.get("system_prompt", "")
        
        enhanced_prompt = f"""{base_prompt}

CONTEXTO DE GRUPO FORTEZZA:
Revisar.ia es una empresa constructora e inmobiliaria líder en Nuevo León, México.
Especializada en desarrollos residenciales, comerciales e industriales.
Facturación anual aproximada: $500M MXN.

MARCO REGULATORIO SAT:
Debes evaluar cada proyecto considerando los 4 pilares de cumplimiento fiscal:
1. RAZÓN DE NEGOCIOS (Art. 5-A CFF): ¿El servicio tiene justificación económica real?
2. BENEFICIO ECONÓMICO (Art. 5-A CFF): ¿Existe ROI medible y valor tangible?
3. MATERIALIDAD (Art. 69-B CFF): ¿Se puede demostrar que el servicio fue prestado?
4. TRAZABILIDAD (NOM-151): ¿Existe documentación completa y verificable?

FORMATO DE RESPUESTA:
Tu análisis debe ser estructurado, profesional y fundamentado.
Incluye siempre:
- Tu evaluación específica desde tu rol
- Riesgos identificados
- Recomendación clara (APROBAR / SOLICITAR AJUSTES / RECHAZAR)
- Justificación de tu decisión
"""
        return enhanced_prompt
    
    def reason_about_project(
        self,
        agent_id: str,
        project_data: Dict[str, Any],
        rag_context: Optional[List[str]] = None,
        previous_deliberations: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        if not self.client:
            return self._fallback_reasoning(agent_id, project_data)
        
        agent_config = AGENT_CONFIGURATIONS.get(agent_id, {})
        agent_name = agent_config.get("name", agent_id)
        agent_role = agent_config.get("role", "analyst")
        
        system_prompt = self.get_agent_system_prompt(agent_id)
        
        rag_section = ""
        if rag_context:
            rag_section = "\n\nDOCUMENTOS DE TU BASE DE CONOCIMIENTO:\n" + "\n---\n".join(rag_context[:5])
        
        prev_section = ""
        if previous_deliberations:
            prev_section = "\n\nDELIBERACIONES PREVIAS DE OTROS AGENTES:\n"
            for delib in previous_deliberations:
                prev_section += f"\n- {delib.get('agent_name', 'Agente')}: {delib.get('analysis', '')[:500]}...\n"
        
        modification_section = ""
        if project_data.get('is_modification'):
            parent_folio = project_data.get('parent_folio', 'No especificado')
            mod_notes = project_data.get('modification_notes', 'Sin notas')
            modification_section = f"""
⚠️ ATENCIÓN: ESTE ES UN REENVÍO/MODIFICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este proyecto es una MODIFICACIÓN de un entregable previo.
Folio del proyecto original: {parent_folio}
Notas de ajuste del proveedor: {mod_notes}

IMPORTANTE: Evalúa si los ajustes solicitados anteriormente 
fueron atendidos correctamente en esta nueva versión.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        user_message = f"""
PROYECTO A EVALUAR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: {project_data.get('id', 'N/A')}
Nombre: {project_data.get('name', 'Sin nombre')}
Cliente/Proveedor: {project_data.get('client_name', 'No especificado')}
Tipo de Servicio: {project_data.get('service_type', 'Consultoría')}
Monto: ${project_data.get('amount', 0):,.2f} MXN
Descripción: {project_data.get('description', 'Sin descripción')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{modification_section}
{rag_section}
{prev_section}

Por favor, realiza tu análisis desde tu perspectiva como {agent_name} ({agent_role}).
Evalúa los 4 pilares de cumplimiento SAT y proporciona tu recomendación fundamentada.
"""
        
        try:
            enable_router = os.getenv("ENABLE_QUERY_ROUTER", "true").lower() == "true"
            
            if enable_router:
                routing = route_query(
                    prompt=user_message,
                    task_type="reasoning"
                )
                selected_model = routing["model"]
                logger.info(f"🎯 Query Router (Anthropic): {routing['model']} | Tokens: {routing['token_count']} | Cost: ${routing['estimated_cost']:.6f} | {routing['reasoning']}")
            else:
                selected_model = self.model
                logger.info(f"Query Router deshabilitado, usando {self.model} por defecto")
            
            # Use OpenAI Chat Completion API
            analysis = chat_completion_sync(
                messages=[{"role": "user", "content": user_message}],
                system_message=system_prompt,
                model=self.model,
                max_tokens=2000
            )
            
            decision = self._extract_decision(analysis)
            pillars_evaluation = self._evaluate_compliance_pillars(analysis)
            adjustments = self._extract_adjustments(analysis)
            
            if adjustments and decision not in ["reject", "request_adjustment"]:
                decision = "request_adjustment"
            
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "analysis": analysis,
                "decision": decision,
                "adjustments": adjustments,
                "compliance_pillars": pillars_evaluation,
                "model_used": self.model,
                "tokens_used": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Anthropic reasoning error for {agent_id}: {str(e)}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "fallback": self._fallback_reasoning(agent_id, project_data)
            }
    
    def _extract_decision(self, analysis: str) -> str:
        analysis_lower = analysis.lower()
        
        if "rechazar" in analysis_lower or "rechazo" in analysis_lower:
            return "reject"
        elif "solicitar ajuste" in analysis_lower or "requiere ajuste" in analysis_lower or "solicito ajuste" in analysis_lower:
            return "request_adjustment"
        elif "ajustes requeridos" in analysis_lower or "[ajuste" in analysis_lower:
            return "request_adjustment"
        elif "aprobar" in analysis_lower or "aprobado" in analysis_lower or "recomiendo aprobar" in analysis_lower:
            return "approve"
        else:
            return "pending_review"
    
    def _extract_adjustments(self, analysis: str) -> List[Dict[str, str]]:
        """Extract specific adjustments requested from the analysis text"""
        import re
        adjustments = []
        
        structured_match = re.search(r'### AJUSTES REQUERIDOS ###(.*?)### FIN AJUSTES ###', analysis, re.DOTALL | re.IGNORECASE)
        if structured_match:
            adjustment_text = structured_match.group(1)
            pattern = r'\[AJUSTE\s*\d+\]:\s*(.+?)(?=\[AJUSTE|\Z)'
            matches = re.findall(pattern, adjustment_text, re.DOTALL | re.IGNORECASE)
            for i, match in enumerate(matches, 1):
                adjustments.append({
                    "id": i,
                    "description": match.strip(),
                    "status": "pending"
                })
        else:
            patterns = [
                r'(?:se\s+(?:requiere|solicita|necesita)|(?:debe|deber[áa])\s+(?:incluir|agregar|modificar|corregir))\s*[:\-]?\s*(.+?)(?:\.|$)',
                r'(?:ajuste\s*\d*[:\-]?\s*)(.+?)(?:\.|$)',
                r'(?:falta|carece\s+de|ausencia\s+de)\s*[:\-]?\s*(.+?)(?:\.|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, analysis, re.IGNORECASE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 10 and len(clean_match) < 500:
                        if not any(adj['description'] == clean_match for adj in adjustments):
                            adjustments.append({
                                "id": len(adjustments) + 1,
                                "description": clean_match,
                                "status": "pending"
                            })
        
        return adjustments[:10]
    
    def _evaluate_compliance_pillars(self, analysis: str) -> Dict[str, Dict]:
        analysis_lower = analysis.lower()
        result = {}
        
        for pillar_id, pillar_info in COMPLIANCE_PILLARS.items():
            mentioned = any(kw in analysis_lower for kw in pillar_info["keywords"])
            
            positive_indicators = ["cumple", "satisface", "adecuado", "suficiente", "correcto"]
            negative_indicators = ["no cumple", "insuficiente", "falta", "carece", "riesgo"]
            
            status = "not_evaluated"
            if mentioned:
                for indicator in negative_indicators:
                    if indicator in analysis_lower:
                        status = "concern"
                        break
                else:
                    for indicator in positive_indicators:
                        if indicator in analysis_lower:
                            status = "compliant"
                            break
                    else:
                        status = "mentioned"
            
            result[pillar_id] = {
                "name": pillar_info["name"],
                "article": pillar_info["article"],
                "status": status,
                "mentioned": mentioned
            }
        
        return result
    
    def _fallback_reasoning(self, agent_id: str, project_data: Dict) -> Dict[str, Any]:
        agent_config = AGENT_CONFIGURATIONS.get(agent_id, {})
        agent_name = agent_config.get("name", agent_id)
        
        fallback_analyses = {
            "A1_SPONSOR": f"""
ANÁLISIS ESTRATÉGICO - {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name')}
Monto: ${project_data.get('amount', 0):,.2f} MXN

EVALUACIÓN PRELIMINAR:
El proyecto requiere validación de alineación estratégica con los objetivos 2026.

RAZÓN DE NEGOCIOS: Pendiente de validación detallada
BENEFICIO ECONÓMICO: Requiere análisis de ROI
MATERIALIDAD: Pendiente documentación
TRAZABILIDAD: En proceso de establecer

RECOMENDACIÓN: SOLICITAR AJUSTES
Se requiere documentación adicional para proceder.

[NOTA: Análisis generado en modo fallback - requiere revisión humana]
""",
            "A2_PMO": f"""
CONSOLIDACIÓN PMO - {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name')}

ESTADO: En proceso de consolidación
Se requieren las validaciones de todos los agentes antes de generar el reporte final.

[NOTA: Análisis generado en modo fallback]
""",
            "A3_FISCAL": f"""
ANÁLISIS FISCAL - {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name')}
Monto: ${project_data.get('amount', 0):,.2f} MXN

CUMPLIMIENTO SAT:
1. Razón de Negocios (Art. 5-A CFF): Pendiente
2. Estricta Indispensabilidad (Art. 27 LISR): Requiere documentación
3. Materialidad (Art. 69-B CFF): Pendiente evidencia

RECOMENDACIÓN: SOLICITAR AJUSTES
Se requiere documentación fiscal completa.

[NOTA: Análisis generado en modo fallback - requiere revisión humana]
""",
            "A5_FINANZAS": f"""
ANÁLISIS FINANCIERO - {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name')}
Monto Solicitado: ${project_data.get('amount', 0):,.2f} MXN

EVALUACIÓN:
- Presupuesto: Pendiente validación
- ROI Estimado: Requiere cálculo
- Viabilidad: En análisis

RECOMENDACIÓN: SOLICITAR AJUSTES
Se requiere información financiera adicional.

[NOTA: Análisis generado en modo fallback]
""",
            "LEGAL": f"""
REVISIÓN LEGAL - {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name')}

PENDIENTES:
- Contrato de servicios
- Términos y condiciones
- Documentación legal

[NOTA: Análisis generado en modo fallback]
"""
        }
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "analysis": fallback_analyses.get(agent_id, "Análisis pendiente"),
            "decision": "request_adjustment",
            "compliance_pillars": {},
            "model_used": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
            "is_fallback": True
        }
    
    def generate_inter_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        project_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        stage: str
    ) -> str:
        from_config = AGENT_CONFIGURATIONS.get(from_agent, {})
        to_config = AGENT_CONFIGURATIONS.get(to_agent, {})
        
        from_name = from_config.get("name", from_agent)
        to_name = to_config.get("name", to_agent)
        
        decision_text = {
            "approve": "APROBADO para continuar",
            "reject": "RECHAZADO - ver justificación",
            "request_adjustment": "REQUIERE AJUSTES",
            "pending_review": "EN REVISIÓN"
        }.get(analysis_result.get("decision", "pending"), "PENDIENTE")
        
        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA SATMA - COMUNICACIÓN INTER-AGENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

De: {from_name} ({from_config.get('department', '')})
Para: {to_name} ({to_config.get('department', '')})
Etapa: {stage}
Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROYECTO: {project_data.get('name', 'Sin nombre')}
ID: {project_data.get('id', 'N/A')}
MONTO: ${project_data.get('amount', 0):,.2f} MXN
DECISIÓN: {decision_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MI ANÁLISIS:

{analysis_result.get('analysis', 'Análisis no disponible')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGUIENTE PASO: Tu turno de evaluar este proyecto desde tu perspectiva.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Atentamente,
{from_name}
{from_config.get('department', '')}
Revisar.ia
"""
        return message
    
    def generate_pmo_consolidation(
        self,
        project_data: Dict[str, Any],
        all_deliberations: List[Dict],
        final_status: str
    ) -> Dict[str, Any]:
        """
        Generate PMO consolidation report with GPT-4o.
        Carlos (PMO) synthesizes all agent deliberations into a final report.
        """
        if not self.client:
            return self._fallback_pmo_consolidation(project_data, all_deliberations, final_status)
        
        agent_config = AGENT_CONFIGURATIONS.get("A2_PMO", {})
        agent_name = agent_config.get("name", "Carlos Mendoza")
        
        deliberations_text = ""
        for delib in all_deliberations:
            deliberations_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENTE: {delib.get('agent_name', delib.get('agent_id'))}
ETAPA: {delib.get('stage', 'N/A')}
DECISIÓN: {delib.get('decision', 'N/A').upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{delib.get('analysis', 'Sin análisis')}

"""
        
        system_prompt = f"""{agent_config.get('system_prompt', '')}

IMPORTANTE: DEBES RESPONDER COMPLETAMENTE EN ESPAÑOL MEXICANO.
Tu tarea es generar el REPORTE DE CONSOLIDACIÓN FINAL para el sistema SATMA de Revisar.ia.
Este documento será enviado al solicitante original del proyecto.

INSTRUCCIONES DE IDIOMA:
- TODO el contenido DEBE estar en español mexicano
- NO uses inglés bajo ninguna circunstancia
- Usa terminología profesional mexicana

ESTRUCTURA OBLIGATORIA DEL REPORTE (mínimo 1500 palabras):

1. ENCABEZADO Y RESUMEN EJECUTIVO (300+ palabras)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   REPORTE DE CONSOLIDACIÓN - SISTEMA SATMA
   Revisar.ia - Control de Servicios de Consultoría
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   - Identificación completa del proyecto (nombre, ID, monto)
   - Proveedor/Solicitante
   - Síntesis ejecutiva de la solicitud
   - DECISIÓN FINAL: {final_status.upper()}
   - Principales hallazgos del proceso de evaluación

2. ANÁLISIS DETALLADO POR ÁREA FUNCIONAL (500+ palabras)
   
   2.1 EVALUACIÓN ESTRATÉGICA (María Rodríguez - Dirección)
   - Alineación con objetivos estratégicos 2026
   - Justificación del servicio en el portafolio
   - Riesgos estratégicos identificados
   - Dictamen de Estrategia
   
   2.2 ANÁLISIS FISCAL (Laura Sánchez - Fiscal)
   - Cumplimiento de Razón de Negocios (Art. 5-A CFF)
   - Evaluación de Estricta Indispensabilidad (Art. 27 LISR)
   - Riesgos fiscales ante el SAT
   - Dictamen Fiscal
   
   2.3 EVALUACIÓN FINANCIERA (Roberto Torres - Finanzas)
   - Análisis presupuestal y disponibilidad
   - Cálculo de ROI proyectado
   - Viabilidad financiera del proyecto
   - Dictamen Financiero
   
   2.4 REVISIÓN LEGAL (Equipo Legal)
   - Validación contractual
   - Requisitos de materialidad documental
   - Protección jurídica
   - Dictamen Legal

3. EVALUACIÓN DE CUMPLIMIENTO SAT - 4 PILARES (300+ palabras)
   
   3.1 RAZÓN DE NEGOCIOS (Art. 5-A CFF)
   - ¿El servicio tiene justificación económica real?
   - Análisis de propósito empresarial
   
   3.2 BENEFICIO ECONÓMICO (Art. 5-A CFF)
   - ROI esperado y valor tangible
   - Métricas de beneficio proyectado
   
   3.3 MATERIALIDAD DEL SERVICIO (Art. 69-B CFF)
   - Evidencia de prestación efectiva del servicio
   - Entregables documentados
   
   3.4 TRAZABILIDAD (NOM-151)
   - Cadena de custodia documental
   - Completitud del Defense File

4. CONCLUSIONES Y SIGUIENTES PASOS (300+ palabras)
   
   4.1 DECISIÓN CONSOLIDADA
   - Resumen de votos de cada agente
   - Decisión final fundamentada
   
   4.2 RECOMENDACIONES
   - Acciones sugeridas para el solicitante
   - Mejoras para proyectos futuros
   
   4.3 DOCUMENTACIÓN GENERADA
   - Lista de documentos adjuntos
   - Links a pCloud del Defense File
   
   4.4 PRÓXIMAS ACCIONES
   - Pasos a seguir según la decisión
   - Responsables y plazos

5. FIRMA Y CIERRE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Carlos Mendoza
   Gerente de PMO
   Revisar.ia
   pmo@revisar.ia
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        user_message = f"""
PROYECTO A CONSOLIDAR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: {project_data.get('id', 'N/A')}
Nombre: {project_data.get('name', 'Sin nombre')}
Cliente/Proveedor: {project_data.get('client_name', 'No especificado')}
Tipo de Servicio: {project_data.get('service_type', 'Consultoría')}
Monto: ${project_data.get('amount', 0):,.2f} MXN
Email Solicitante: {project_data.get('email', 'No especificado')}
Descripción: {project_data.get('description', 'Sin descripción')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESTADO FINAL: {final_status.upper()}

DELIBERACIONES DE TODOS LOS AGENTES:
{deliberations_text}

INSTRUCCIONES FINALES:
1. Genera el Reporte de Consolidación Final EN ESPAÑOL MEXICANO
2. Sigue la estructura indicada con TODOS los apartados
3. El reporte debe ser profesional, completo y detallado (mínimo 1500 palabras)
4. NO uses inglés - todo debe estar en español
5. Incluye análisis específico de cada agente basándote en sus deliberaciones
6. Mantén un tono formal y ejecutivo apropiado para documentación corporativa
"""
        
        try:
            enable_router = os.getenv("ENABLE_QUERY_ROUTER", "true").lower() == "true"
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            if enable_router:
                routing = route_query(
                    prompt=user_message,
                    task_type="reasoning"
                )
                selected_model = routing["model"]
                logger.info(f"🎯 Query Router (PMO): {routing['model']} | Tokens: {routing['token_count']} | Cost: ${routing['estimated_cost']:.6f} | {routing['reasoning']}")
            else:
                selected_model = self.model
                logger.info(f"Query Router deshabilitado, usando {self.model} por defecto")
            
            # Use OpenAI Chat Completion API for PMO consolidation
            consolidation = chat_completion_sync(
                messages=[{"role": "user", "content": user_message}],
                system_message=system_prompt,
                model=self.model,
                max_tokens=4500
            )
            tokens_used = len(user_message.split()) + len(consolidation.split())  # Approximate token count
            
            print(f"🕵️ PMO: Sending draft to Strategy Council for audit...")
            logger.info("PMO: Starting Strategy Council audit for consolidation")
            
            rag_context = [
                deliberations_text,
                f"Proyecto: {project_data.get('name', '')}",
                f"Descripción: {project_data.get('description', '')}",
                f"Monto: ${project_data.get('amount', 0):,.2f} MXN",
                f"Estado Final: {final_status}"
            ]
            
            audit_result = validate_pmo_response_sync(
                pmo_draft=consolidation or "",
                rag_context=rag_context
            )
            
            consolidation = audit_result.get("validated_response", consolidation)
            risk_score = audit_result.get("risk_score", 0)
            was_modified = audit_result.get("was_modified", False)
            hallucinations_removed = audit_result.get("hallucinations_removed", [])
            
            print(f"✅ PMO: Audit complete. Risk Score: {risk_score}, Modified: {was_modified}")
            if hallucinations_removed:
                print(f"🚨 PMO: {len(hallucinations_removed)} hallucinations removed!")
            logger.info(f"PMO consolidation audited - Risk: {risk_score}, Modified: {was_modified}, Hallucinations: {len(hallucinations_removed)}")
            
            return {
                "success": True,
                "agent_id": "A2_PMO",
                "agent_name": agent_name,
                "consolidation": consolidation,
                "final_status": final_status,
                "agents_consolidated": len(all_deliberations),
                "model_used": self.model,
                "tokens_used": tokens_used,
                "timestamp": datetime.utcnow().isoformat(),
                "audit_metadata": {
                    "risk_score": risk_score,
                    "was_modified": was_modified,
                    "hallucinations_removed": hallucinations_removed,
                    "council_validated": True
                }
            }
            
        except Exception as e:
            logger.error(f"PMO consolidation failed: {e}")
            return self._fallback_pmo_consolidation(project_data, all_deliberations, final_status)
    
    def _fallback_pmo_consolidation(
        self,
        project_data: Dict[str, Any],
        all_deliberations: List[Dict],
        final_status: str
    ) -> Dict[str, Any]:
        """Fallback consolidation when Anthropic is not available"""
        agent_config = AGENT_CONFIGURATIONS.get("A2_PMO", {})
        agent_name = agent_config.get("name", "Carlos Mendoza")
        
        agents_summary = "\n".join([
            f"- {d.get('agent_name', d.get('agent_id'))}: {d.get('decision', 'N/A').upper()}"
            for d in all_deliberations
        ])
        
        consolidation = f"""
REPORTE DE CONSOLIDACIÓN - SISTEMA SATMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. RESUMEN EJECUTIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proyecto: {project_data.get('name', 'Sin nombre')}
ID: {project_data.get('id', 'N/A')}
Monto Solicitado: ${project_data.get('amount', 0):,.2f} MXN
Solicitante: {project_data.get('client_name', 'No especificado')}
Decisión Final: {final_status.upper()}

2. SÍNTESIS DE DELIBERACIONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{agents_summary}

3. CONCLUSIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
El proyecto ha sido evaluado por todos los agentes del sistema SATMA.
Se adjuntan los reportes individuales de cada agente para su revisión.

4. DOCUMENTOS ADJUNTOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Reporte de Estrategia (María Rodríguez)
- Reporte Fiscal (Laura Sánchez)
- Reporte Financiero (Roberto Torres)
- Reporte Legal (Equipo Legal)

[NOTA: Reporte generado en modo fallback - requiere revisión humana]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Consolidado por: {agent_name}
PMO - Revisar.ia
Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return {
            "success": True,
            "agent_id": "A2_PMO",
            "agent_name": agent_name,
            "consolidation": consolidation,
            "final_status": final_status,
            "agents_consolidated": len(all_deliberations),
            "model_used": "fallback",
            "tokens_used": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "is_fallback": True
        }
    
    def generate_consolidation_email(
        self,
        project_data: Dict[str, Any],
        consolidation_result: Dict[str, Any],
        pcloud_links: Any,
        deliberations: Optional[List[Dict]] = None
    ) -> str:
        """Generate the email body for PMO consolidation to send to submitter"""
        agent_config = AGENT_CONFIGURATIONS.get("A2_PMO", {})
        agent_name = agent_config.get("name", "Carlos Mendoza")
        
        client_name = (
            project_data.get('client_name') or 
            project_data.get('submitter_name') or 
            project_data.get('name', 'Solicitante')
        )
        
        documents_list = []
        folders_dict = {}
        bitacora_link = None
        
        if isinstance(pcloud_links, dict):
            documents_list = pcloud_links.get('documents', []) or []
            folders_dict = pcloud_links.get('agent_folders', {}) or {}
            bitacora_link = pcloud_links.get('bitacora')
        elif isinstance(pcloud_links, list):
            documents_list = pcloud_links
        
        links_section = ""
        
        if documents_list:
            links_section = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            links_section += "📁 DOCUMENTOS EN NUBE (pCloud) - EVIDENCIA PARA SAT\n"
            links_section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            links_section += "Los siguientes documentos están disponibles para descarga:\n\n"
            for i, link in enumerate(documents_list, 1):
                if isinstance(link, dict):
                    doc_type = link.get('doc_type', 'Documento')
                    if doc_type:
                        doc_type = doc_type.replace('reporte_', '').replace('_', ' ').title()
                    else:
                        doc_type = 'Documento'
                    agent_id = link.get('agent_id', '')
                    pcloud_url = link.get('pcloud_link') or link.get('download_url') or 'N/A'
                    links_section += f"   {i}. {doc_type}"
                    if agent_id:
                        links_section += f" ({agent_id})"
                    links_section += f"\n      📎 {pcloud_url}\n\n"
                elif isinstance(link, str):
                    links_section += f"   {i}. Documento\n      📎 {link}\n\n"
        
        if folders_dict:
            links_section += "\n📂 CARPETAS DE AGENTES:\n"
            for agent_id, folder_url in folders_dict.items():
                if isinstance(folder_url, str):
                    links_section += f"   • {agent_id}: {folder_url}\n"
        
        if bitacora_link:
            links_section += f"\n📋 BITÁCORA DEL PROYECTO:\n   📎 {bitacora_link}\n"
        
        adjustments_section = ""
        if deliberations:
            all_adjustments = []
            for delib in deliberations:
                if delib.get('decision') == 'request_adjustment':
                    agent_adjustments = delib.get('adjustments', [])
                    agent_name_delib = delib.get('agent_name', delib.get('agent_id', 'Agente'))
                    for adj in agent_adjustments:
                        if isinstance(adj, dict):
                            desc = adj.get('description', '')
                        else:
                            desc = str(adj)
                        if desc:
                            all_adjustments.append({
                                'agent': agent_name_delib,
                                'description': desc
                            })
            
            if all_adjustments:
                adjustments_section = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### AJUSTES SOLICITADOS POR EQUIPO LEGAL ###
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Los siguientes ajustes fueron solicitados durante el proceso de evaluación:

"""
                for i, adj in enumerate(all_adjustments, 1):
                    adjustments_section += f"{i}. [{adj['agent']}] {adj['description']}\n"
                
                adjustments_section += """
Por favor, revise y atienda estos ajustes para completar el proceso de aprobación.
"""
        
        email_body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA SATMA - REPORTE DE CONSOLIDACIÓN FINAL
Revisar.ia
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimado(a) {client_name},

Le informamos que su solicitud de proyecto ha completado el proceso de evaluación multi-agente del Sistema SATMA.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATOS DEL PROYECTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: {project_data.get('id', 'N/A')}
Nombre: {project_data.get('name', 'Sin nombre')}
Monto: ${project_data.get('amount', 0):,.2f} MXN
Estado Final: {consolidation_result.get('final_status', 'PENDIENTE').upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPORTE DE CONSOLIDACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{consolidation_result.get('consolidation', 'Consolidación no disponible')}
{adjustments_section}
{links_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADJUNTOS EN ESTE CORREO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este correo incluye los reportes PDF de cada agente que participó 
en la evaluación. Puede descargarlos directamente del correo o 
acceder a ellos desde los enlaces de pCloud arriba listados.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quedamos a su disposición para cualquier aclaración.

Atentamente,

{agent_name}
Gerente de PMO
Revisar.ia
Email: pmo@revisar.ia
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return email_body


agentic_service = AgenticReasoningService()
