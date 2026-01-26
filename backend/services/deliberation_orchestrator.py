"""
Deliberation Orchestrator Service
Coordinates the 5-stage workflow between Revisar.IA agents via email
Creates audit trail for SAT Materialidad compliance
"""
import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.dreamhost_email_service import DreamHostEmailService
from services.rag_service import RAGService
from services.defense_file_service import defense_file_service
from services.agentic_reasoning_service import agentic_service
from services.report_generator import ReportGeneratorService
from services.evidence_portfolio_service import evidence_portfolio_service
from services.event_stream import event_emitter
from services.auditor_service import auditor_service
from config.agents_config import AGENT_CONFIGURATIONS
from pathlib import Path
from services.inyeccion_contexto_service import (
    construir_contexto_completo_para_agente,
    generar_system_prompt_con_contexto
)
from config.reglas_tipologia import get_reglas_tipologia
from validation.validation_service import validar_output_agente, validar_y_corregir
from services.database import deliberation_state_repository
from services.cliente_contexto_service import cliente_contexto_service

logger = logging.getLogger(__name__)


def get_cliente_id_from_project(project: Dict) -> Optional[int]:
    """
    Extrae el cliente_id del proyecto.
    Busca en varios campos posibles donde puede estar el ID del cliente.
    
    Args:
        project: Diccionario con datos del proyecto
        
    Returns:
        cliente_id como entero o None si no se encuentra
    """
    cliente_id = project.get("cliente_id") or project.get("client_id")
    
    if cliente_id is None:
        cliente_id = project.get("empresa_cliente_id") or project.get("customer_id")
    
    if cliente_id is not None:
        try:
            return int(cliente_id)
        except (ValueError, TypeError):
            logger.warning(f"cliente_id inválido: {cliente_id}")
            return None
    
    return None


class WorkflowStage(str, Enum):
    E1_ESTRATEGIA = "E1_ESTRATEGIA"
    E2_FISCAL = "E2_FISCAL"
    E3_FINANZAS = "E3_FINANZAS"
    E4_LEGAL = "E4_LEGAL"
    E5_APROBADO = "E5_APROBADO"
    RECHAZADO = "RECHAZADO"


WORKFLOW_ORDER = [
    WorkflowStage.E1_ESTRATEGIA,
    WorkflowStage.E2_FISCAL,
    WorkflowStage.E3_FINANZAS,
    WorkflowStage.E4_LEGAL,
    WorkflowStage.E5_APROBADO
]

STAGE_TO_AGENT = {
    WorkflowStage.E1_ESTRATEGIA: "A1_SPONSOR",
    WorkflowStage.E2_FISCAL: "A3_FISCAL",
    WorkflowStage.E3_FINANZAS: "A5_FINANZAS",
    WorkflowStage.E4_LEGAL: "LEGAL",
}

AGENT_TO_STAGE = {v: k for k, v in STAGE_TO_AGENT.items()}

STAGE_TO_REPORT_TYPE = {
    WorkflowStage.E1_ESTRATEGIA: "estrategia",
    WorkflowStage.E2_FISCAL: "fiscal",
    WorkflowStage.E3_FINANZAS: "finanzas",
    WorkflowStage.E4_LEGAL: "legal",
}


def preload_rag_contexts_parallel(project_data: Dict, rag_service) -> Dict[str, List[Dict]]:
    """
    Pre-carga contextos RAG de TODOS los agentes EN PARALELO usando threads.
    Reduce latencia de ~2s×4 agentes = 8s a ~2s total.
    """
    agent_ids = ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS", "LEGAL"]
    project_description = f"{project_data.get('name', '')} {project_data.get('description', '')}"
    
    def fetch_context(agent_id: str) -> Tuple[str, List[Dict]]:
        """Fetch individual de contexto RAG"""
        try:
            results = rag_service.query(
                agent_id=agent_id,
                query_text=project_description,
                n_results=5
            )
            docs = results.get("documents", [])
            logger.info(f"✅ RAG pre-loaded for {agent_id}: {len(docs)} docs")
            return (agent_id, docs)
        except Exception as e:
            logger.warning(f"⚠️ No RAG context for {agent_id}: {e}")
            return (agent_id, [])
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_context, agent_ids))
    
    try:
        from routes.metrics import track_rag_preload
        track_rag_preload()
    except ImportError:
        pass
    
    return dict(results)


class Deliberation:
    """Represents a single deliberation record with multi-tenant isolation"""
    def __init__(
        self,
        project_id: str,
        stage: WorkflowStage,
        agent_id: str,
        decision: str,
        analysis: str,
        rag_context: List[Dict],
        empresa_id: Optional[str] = None,
        email_sent: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        self.project_id = project_id
        self.empresa_id = empresa_id
        self.stage = stage
        self.agent_id = agent_id
        self.decision = decision  # "approve", "reject", "request_info"
        self.analysis = analysis
        self.rag_context = rag_context
        self.email_sent = email_sent
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "empresa_id": self.empresa_id,
            "stage": self.stage.value,
            "agent_id": self.agent_id,
            "decision": self.decision,
            "analysis": self.analysis,
            "rag_context": self.rag_context,
            "email_sent": self.email_sent,
            "timestamp": self.timestamp.isoformat()
        }


class DeliberationOrchestrator:
    """
    Orchestrates the multi-agent deliberation process for project validation
    
    Workflow:
    1. Project submitted → E1_ESTRATEGIA (María)
    2. María analyzes with RAG → emails Carlos (PMO) with decision
    3. If approved → E2_FISCAL (Laura) analyzes
    4. If approved → E3_FINANZAS (Roberto) analyzes
    5. If approved → E4_LEGAL (Legal Team) analyzes
    6. If all approve → E5_APROBADO
    
    Each step creates email evidence for SAT Materialidad audit trail
    """
    
    def __init__(self):
        self.email_service = DreamHostEmailService()
        self.rag_service = RAGService()
        self.report_generator = ReportGeneratorService()
        self.deliberations: Dict[str, List[Deliberation]] = {}
    
    async def _preparar_contexto_agente(self, agent_id: str, project: dict, proveedor: dict = None):
        """Prepara contexto completo para el agente incluyendo normativo y reglas"""
        documentos = self._obtener_documentos_proyecto(project.get("id"))
        deliberaciones_previas = self.deliberations.get(project.get("id"), [])
        deliberaciones_dict = [d.to_dict() if hasattr(d, 'to_dict') else d for d in deliberaciones_previas]
        
        contexto = construir_contexto_completo_para_agente(
            agente_id=agent_id,
            proyecto=project,
            proveedor=proveedor,
            documentos=documentos,
            deliberaciones_previas=deliberaciones_dict
        )
        system_prompt = generar_system_prompt_con_contexto(agent_id, contexto)
        return contexto, system_prompt
    
    def _obtener_documentos_proyecto(self, project_id: str) -> list:
        """Obtiene documentos del proyecto desde el defense file"""
        try:
            df = defense_file_service.get_defense_file(project_id)
            return df.documents if df else []
        except:
            return []
    
    def _validar_y_registrar_output(self, agent_id: str, output_dict: dict, deliberation_record: dict) -> dict:
        """Valida output del agente y registra resultado"""
        validation_result = validar_output_agente(agent_id, output_dict)
        
        if not validation_result.get("valido", False):
            logger.warning(f"Output de {agent_id} inválido: {validation_result.get('errores', [])}")
            corrected = validar_y_corregir(agent_id, output_dict)
            if corrected.get("valido"):
                output_dict = corrected.get("output_validado", output_dict)
                deliberation_record["validation_status"] = "CORRECTED"
                logger.info(f"Output de {agent_id} corregido automáticamente")
            else:
                deliberation_record["validation_status"] = "INVALID"
                deliberation_record["validation_errors"] = validation_result.get("errores", [])
        else:
            deliberation_record["validation_status"] = "VALID"
        
        deliberation_record["output_validado"] = output_dict
        return output_dict
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict]:
        """Get agent configuration by ID"""
        config = AGENT_CONFIGURATIONS.get(agent_id)
        if config:
            return {"id": agent_id, **config}
        return None
    
    def get_next_stage(self, current_stage: WorkflowStage) -> Optional[WorkflowStage]:
        """Get the next stage in the workflow"""
        try:
            current_idx = WORKFLOW_ORDER.index(current_stage)
            if current_idx < len(WORKFLOW_ORDER) - 1:
                return WORKFLOW_ORDER[current_idx + 1]
        except ValueError:
            pass
        return None
    
    def get_rag_context(self, agent_id: str, project_description: str, n_results: int = 5) -> List[Dict]:
        """Query agent's RAG knowledge base for relevant context"""
        try:
            results = self.rag_service.query(
                agent_id=agent_id,
                query_text=project_description,
                n_results=n_results
            )
            return results.get("documents", [])
        except Exception as e:
            logger.error(f"Error querying RAG for {agent_id}: {e}")
            return []
    
    def build_deliberation_email(
        self,
        project: Dict,
        from_agent: Dict,
        to_agent: Dict,
        decision: str,
        analysis: str,
        rag_context: List[Dict]
    ) -> Dict[str, str]:
        """Build email content for agent-to-agent communication"""
        
        project_id = project.get("id", "N/A")
        project_name = project.get("name", "Sin nombre")
        client_name = project.get("client_name", "N/A")
        amount = project.get("amount", 0)
        
        subject = f"[Revisar.IA] Deliberación Proyecto {project_id}: {project_name}"
        
        rag_summary = ""
        if rag_context:
            rag_summary = "\n\n📚 CONTEXTO NORMATIVO APLICABLE:\n"
            for i, doc in enumerate(rag_context[:3], 1):
                content = doc.get("content", "")[:200]
                source = doc.get("metadata", {}).get("source", "Base de conocimiento")
                rag_summary += f"\n{i}. [{source}]: {content}..."
        
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA REVISAR.IA - DELIBERACIÓN MULTI-AGENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PROYECTO: {project_name}
🔢 ID: {project_id}
🏢 Cliente: {client_name}
💰 Monto: ${amount:,.2f} MXN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 DE: {from_agent.get('name', 'Agente')} ({from_agent.get('role', '')})
📧 Email: {from_agent.get('email', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 DECISIÓN: {decision.upper()}

📝 ANÁLISIS:
{analysis}
{rag_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Fecha/Hora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
🔐 Este correo constituye evidencia de Materialidad para auditorías SAT
   conforme al Artículo 69-B del CFF y NOM-151
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return {
            "subject": subject,
            "body": body
        }
    
    async def start_deliberation(self, project: Dict) -> Dict:
        """
        Start the deliberation process for a new project
        Sends to first agent (María/Estrategia)
        """
        project_id = project.get("id", str(datetime.now().timestamp()))
        
        first_agent_id = STAGE_TO_AGENT[WorkflowStage.E1_ESTRATEGIA]
        first_agent = self.get_agent_config(first_agent_id)
        
        if not first_agent:
            return {"success": False, "error": "Agent A1_SPONSOR not found"}
        
        project_description = f"""
        Proyecto: {project.get('name', '')}
        Cliente: {project.get('client_name', '')}
        Descripción: {project.get('description', '')}
        Monto: ${project.get('amount', 0):,.2f}
        Tipo de servicio: {project.get('service_type', 'Consultoría')}
        """
        
        rag_context = self.get_rag_context(first_agent_id, project_description)
        
        email_content = {
            "subject": f"[Revisar.IA] Nuevo Proyecto para Validación: {project.get('name', 'Sin nombre')}",
            "body": f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA REVISAR.IA - NUEVA SOLICITUD DE VALIDACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimada {first_agent.get('name', 'María')},

Se ha recibido un nuevo proyecto para validación de cumplimiento SAT.

📋 DATOS DEL PROYECTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔢 ID: {project_id}
📋 Nombre: {project.get('name', 'Sin nombre')}
🏢 Cliente: {project.get('client_name', 'N/A')}
📝 Descripción: {project.get('description', 'Sin descripción')}
💰 Monto: ${project.get('amount', 0):,.2f} MXN
🏷️ Tipo: {project.get('service_type', 'Consultoría')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 DOCUMENTOS RELEVANTES DE TU BASE DE CONOCIMIENTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""" + self._format_rag_context(rag_context) + f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ACCIÓN REQUERIDA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Por favor analiza este proyecto considerando:
1. Razón de Negocios (Art. 5-A CFF)
2. Beneficio Económico Esperado
3. Materialidad del servicio
4. Trazabilidad documental

Responde a este correo con tu análisis y decisión:
- APROBAR: Para pasar al siguiente agente
- RECHAZAR: Si no cumple los criterios
- SOLICITAR_INFO: Si necesitas más información

⏰ Fecha de solicitud: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sistema Revisar.IA - Revisar.ia
"""
        }
        
        try:
            result = self.email_service.send_email(
                from_agent_id=first_agent_id,
                to_email=first_agent.get("email", ""),
                subject=email_content["subject"],
                body=email_content["body"]
            )
            
            deliberation = Deliberation(
                project_id=project_id,
                stage=WorkflowStage.E1_ESTRATEGIA,
                agent_id=first_agent_id,
                decision="pending",
                analysis="Proyecto enviado para análisis inicial",
                rag_context=rag_context,
                empresa_id=project.get("empresa_id"),
                email_sent=result
            )
            
            if project_id not in self.deliberations:
                self.deliberations[project_id] = []
            self.deliberations[project_id].append(deliberation)
            
            defense_file_service.create_defense_file(project_id, project)
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            
            if result.get("success"):
                defense_file_service.add_email(project_id, {
                    "from_email": first_agent.get("email", ""),
                    "to_email": first_agent.get("email", ""),
                    "subject": email_content["subject"],
                    "body": email_content["body"][:500],
                    "message_id": result.get("message_id", "")
                })
            
            return {
                "success": True,
                "project_id": project_id,
                "current_stage": WorkflowStage.E1_ESTRATEGIA.value,
                "agent_notified": first_agent_id,
                "email_sent": result.get("success", False),
                "rag_documents_used": len(rag_context),
                "defense_file_created": True
            }
            
        except Exception as e:
            logger.error(f"Error starting deliberation: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_rag_context(self, rag_context: List[Dict]) -> str:
        """Format RAG context for email"""
        if not rag_context:
            return "No se encontraron documentos relevantes en la base de conocimiento.\n"
        
        formatted = ""
        for i, doc in enumerate(rag_context[:5], 1):
            content = doc.get("content", "")[:300]
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Base de conocimiento")
            doc_type = metadata.get("tipo", "documento")
            
            formatted += f"""
📄 Documento {i}:
   Fuente: {source}
   Tipo: {doc_type}
   Contenido relevante: {content}...
"""
        return formatted
    
    async def advance_workflow(
        self,
        project_id: str,
        current_agent_id: str,
        decision: str,
        analysis: str,
        project: Dict
    ) -> Dict:
        """
        Advance the workflow to the next stage based on agent's decision
        """
        current_stage = AGENT_TO_STAGE.get(current_agent_id)
        if not current_stage:
            return {"success": False, "error": f"Unknown agent: {current_agent_id}"}
        
        current_agent = self.get_agent_config(current_agent_id)
        if not current_agent:
            return {"success": False, "error": f"Agent config not found: {current_agent_id}"}
        
        project_description = f"{project.get('name', '')} {project.get('description', '')}"
        rag_context = self.get_rag_context(current_agent_id, project_description)
        
        if decision.lower() == "reject" or decision.lower() == "rechazar":
            deliberation = Deliberation(
                project_id=project_id,
                stage=current_stage,
                agent_id=current_agent_id,
                decision="reject",
                analysis=analysis,
                rag_context=rag_context,
                empresa_id=project.get("empresa_id")
            )
            
            if project_id not in self.deliberations:
                self.deliberations[project_id] = []
            self.deliberations[project_id].append(deliberation)
            
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            defense_file_service.finalize_defense_file(
                project_id, 
                "rejected", 
                f"Rechazado por {current_agent_id}: {analysis}"
            )
            
            try:
                defense_audit = auditor_service.audit_defense_zip(project_id)
                if defense_audit.get("audit_passed"):
                    logger.info(f"✅ [A8_AUDITOR] Defense File audit passed for {project_id}")
                else:
                    logger.warning(f"⚠️ [A8_AUDITOR] Defense File audit issues: {defense_audit.get('issues', [])}")
            except Exception as audit_err:
                logger.warning(f"[A8_AUDITOR] Defense File audit failed: {audit_err}")
            
            return {
                "success": True,
                "project_id": project_id,
                "final_stage": WorkflowStage.RECHAZADO.value,
                "rejected_by": current_agent_id,
                "analysis": analysis,
                "workflow_complete": True,
                "defense_file_finalized": True
            }
        
        next_stage = self.get_next_stage(current_stage)
        
        if next_stage == WorkflowStage.E5_APROBADO:
            deliberation = Deliberation(
                project_id=project_id,
                stage=current_stage,
                agent_id=current_agent_id,
                decision="approve",
                analysis=analysis,
                rag_context=rag_context,
                empresa_id=project.get("empresa_id")
            )
            
            if project_id not in self.deliberations:
                self.deliberations[project_id] = []
            self.deliberations[project_id].append(deliberation)
            
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            defense_file_service.finalize_defense_file(
                project_id,
                "approved",
                f"Aprobado por todos los agentes. Última revisión: {current_agent_id}"
            )
            
            try:
                defense_audit = auditor_service.audit_defense_zip(project_id)
                if defense_audit.get("audit_passed"):
                    logger.info(f"✅ [A8_AUDITOR] Defense File audit passed for {project_id}")
                else:
                    logger.warning(f"⚠️ [A8_AUDITOR] Defense File audit issues: {defense_audit.get('issues', [])}")
            except Exception as audit_err:
                logger.warning(f"[A8_AUDITOR] Defense File audit failed: {audit_err}")
            
            return {
                "success": True,
                "project_id": project_id,
                "final_stage": WorkflowStage.E5_APROBADO.value,
                "approved_by_all": True,
                "workflow_complete": True,
                "deliberation_count": len(self.deliberations.get(project_id, [])),
                "defense_file_finalized": True
            }
        
        next_agent_id = STAGE_TO_AGENT.get(next_stage)
        next_agent = self.get_agent_config(next_agent_id)
        
        if not next_agent:
            return {"success": False, "error": f"Next agent not found: {next_agent_id}"}
        
        email_content = self.build_deliberation_email(
            project=project,
            from_agent=current_agent,
            to_agent=next_agent,
            decision="APROBADO - Pasa a siguiente etapa",
            analysis=analysis,
            rag_context=rag_context
        )
        
        try:
            email_result = self.email_service.send_email(
                from_agent_id=current_agent_id,
                to_email=next_agent.get("email", ""),
                subject=email_content["subject"],
                body=email_content["body"]
            )
            
            deliberation = Deliberation(
                project_id=project_id,
                stage=current_stage,
                agent_id=current_agent_id,
                decision="approve",
                analysis=analysis,
                rag_context=rag_context,
                empresa_id=project.get("empresa_id"),
                email_sent=email_result
            )
            
            if project_id not in self.deliberations:
                self.deliberations[project_id] = []
            self.deliberations[project_id].append(deliberation)
            
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            
            if email_result.get("success"):
                defense_file_service.add_email(project_id, {
                    "from_email": current_agent.get("email", ""),
                    "to_email": next_agent.get("email", ""),
                    "subject": email_content["subject"],
                    "body": email_content["body"][:500],
                    "message_id": email_result.get("message_id", "")
                })
            
            return {
                "success": True,
                "project_id": project_id,
                "previous_stage": current_stage.value,
                "current_stage": next_stage.value,
                "agent_notified": next_agent_id,
                "email_sent": email_result.get("success", False),
                "workflow_complete": False,
                "defense_file_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error advancing workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def get_deliberation_trail(self, project_id: str) -> Dict:
        """
        Get the complete deliberation trail for a project
        This serves as the audit evidence for SAT Materialidad
        """
        deliberations = self.deliberations.get(project_id, [])
        
        return {
            "project_id": project_id,
            "deliberation_count": len(deliberations),
            "deliberations": [d.to_dict() for d in deliberations],
            "compliance_pillars": {
                "razon_de_negocios": "Art. 5-A CFF - Documentado en análisis",
                "beneficio_economico": "Evaluado por cada agente",
                "materialidad": "Art. 69-B CFF - Emails como evidencia",
                "trazabilidad": "NOM-151 - Trail completo de deliberaciones"
            },
            "audit_ready": len(deliberations) > 0
        }
    
    def get_project_status(self, project_id: str) -> Dict:
        """Get current workflow status for a project"""
        deliberations = self.deliberations.get(project_id, [])
        
        if not deliberations:
            return {
                "project_id": project_id,
                "status": "not_found",
                "current_stage": None
            }
        
        last_deliberation = deliberations[-1]
        
        if last_deliberation.decision == "reject":
            return {
                "project_id": project_id,
                "status": "rejected",
                "current_stage": WorkflowStage.RECHAZADO.value,
                "rejected_by": last_deliberation.agent_id,
                "rejection_reason": last_deliberation.analysis
            }
        
        next_stage = self.get_next_stage(last_deliberation.stage)
        
        if next_stage == WorkflowStage.E5_APROBADO or next_stage is None:
            return {
                "project_id": project_id,
                "status": "approved",
                "current_stage": WorkflowStage.E5_APROBADO.value,
                "approval_count": len(deliberations)
            }
        
        return {
            "project_id": project_id,
            "status": "in_progress",
            "current_stage": next_stage.value,
            "stages_completed": len(deliberations),
            "pending_agent": STAGE_TO_AGENT.get(next_stage)
        }
    
    async def run_agentic_deliberation(self, project: Dict) -> Dict:
        """
        Run the FULL agentic deliberation process with LLM reasoning.
        Each agent analyzes, reasons, and passes to the next agent.
        Returns complete audit trail when done.
        """
        import uuid
        project_id = project.get("id") or f"PROJ-{uuid.uuid4().hex[:8].upper()}"
        project["id"] = project_id
        
        event_emitter.create_session(project_id)
        
        defense_file_service.create_defense_file(project_id, project)
        
        all_deliberations = []
        previous_analyses = []
        current_stage = WorkflowStage.E1_ESTRATEGIA
        
        # Get empresa_id from project for multi-tenant tracking
        empresa_id = project.get("empresa_id", project.get("client_name", "unknown"))

        # Initialize state persistence
        await deliberation_state_repository.save_state(
            project_id=project_id,
            empresa_id=empresa_id,
            current_stage=current_stage.value,
            stage_results={},
            status="in_progress",
            project_data=project
        )
        
        logger.info(f"Starting agentic deliberation for project {project_id}")
        
        # Pre-carga de contextos RAG en paralelo (optimización ~6s ahorro)
        logger.info("🚀 Pre-loading RAG contexts in parallel...")
        preload_start = datetime.now(timezone.utc)
        preloaded_rag_contexts = preload_rag_contexts_parallel(project, self.rag_service)
        preload_elapsed = (datetime.now(timezone.utc) - preload_start).total_seconds()
        logger.info(f"✅ Loaded {len(preloaded_rag_contexts)} RAG contexts in {preload_elapsed:.2f}s (paralelo)")
        
        await event_emitter.emit(
            project_id, "SYSTEM", "thinking",
            "Iniciando análisis multi-agente con IA...",
            progress=5
        )
        
        total_stages = len(WORKFLOW_ORDER) - 1
        for stage_idx, stage in enumerate(WORKFLOW_ORDER[:-1]):
            agent_id = STAGE_TO_AGENT.get(stage)
            if not agent_id:
                continue
            
            agent_config = self.get_agent_config(agent_id)
            if not agent_config:
                continue
            
            stage_progress = int(10 + (stage_idx * 80 / total_stages))
            
            logger.info(f"Stage {stage.value}: Agent {agent_id} reasoning...")
            
            await event_emitter.emit_thinking(
                project_id, agent_id,
                f"{agent_config.get('name', agent_id)} está revisando el proyecto..."
            )
            
            project_description = f"{project.get('name', '')} {project.get('description', '')}"
            
            await event_emitter.emit_rag_search(
                project_id, agent_id,
                f"{agent_config.get('name', agent_id)} consultando base de conocimiento normativo..."
            )
            
            # Usar contexto RAG pre-cargado en paralelo
            rag_context = preloaded_rag_contexts.get(agent_id, [])
            rag_texts = [doc.get("content", "") for doc in rag_context] if rag_context else []
            logger.debug(f"Using pre-loaded RAG for {agent_id}: {len(rag_context)} docs")
            
            # Obtener contexto evolutivo del cliente si está disponible
            cliente_id = get_cliente_id_from_project(project)
            cliente_contexto_str = ""
            if cliente_id:
                try:
                    cliente_contexto_str = await cliente_contexto_service.get_contexto_para_agente(
                        cliente_id=cliente_id,
                        agente_id=agent_id
                    )
                    if cliente_contexto_str and not cliente_contexto_str.startswith("[ERROR]"):
                        # Agregar contexto del cliente al inicio de los textos RAG
                        rag_texts = [cliente_contexto_str] + rag_texts
                        logger.info(f"✅ Contexto evolutivo incluido para {agent_id}, cliente {cliente_id}")
                    else:
                        logger.debug(f"No hay contexto evolutivo para cliente {cliente_id}")
                except Exception as ctx_err:
                    logger.warning(f"Error obteniendo contexto evolutivo para cliente {cliente_id}: {ctx_err}")
            
            await event_emitter.emit_analyzing(
                project_id, agent_id,
                f"{agent_config.get('name', agent_id)} analizando cumplimiento SAT con GPT-4o...",
                progress=stage_progress + 10
            )
            
            reasoning_start_time = datetime.now(timezone.utc)
            
            # Run synchronous LLM call in thread to avoid blocking event loop
            reasoning_result = await asyncio.to_thread(
                agentic_service.reason_about_project,
                agent_id=agent_id,
                project_data=project,
                rag_context=rag_texts,
                previous_deliberations=previous_analyses
            )
            
            reasoning_elapsed_ms = int((datetime.now(timezone.utc) - reasoning_start_time).total_seconds() * 1000)
            
            decision = reasoning_result.get("decision", "pending")
            analysis = reasoning_result.get("analysis", "Análisis no disponible")
            
            # Registrar la interacción del agente con el cliente
            if cliente_id:
                try:
                    await cliente_contexto_service.registrar_interaccion(
                        cliente_id=cliente_id,
                        agente_id=agent_id,
                        agente_nombre=agent_config.get("name", agent_id),
                        tipo="deliberacion",
                        pregunta_usuario=f"Análisis de proyecto: {project.get('name', 'Sin nombre')} - {project_description}",
                        respuesta_agente=analysis[:2000] if analysis else "Sin análisis",
                        hallazgos={
                            "decision": decision,
                            "stage": stage.value,
                            "compliance_pillars": reasoning_result.get("compliance_pillars", {})
                        },
                        recomendaciones={
                            "adjustments": reasoning_result.get("adjustments", [])
                        },
                        duracion_ms=reasoning_elapsed_ms,
                        tokens_usados=reasoning_result.get("tokens_used", 0)
                    )
                    logger.info(f"✅ Interacción registrada para cliente {cliente_id}, agente {agent_id}")
                except Exception as reg_err:
                    logger.warning(f"Error registrando interacción para cliente {cliente_id}: {reg_err}")
            
            await event_emitter.emit_complete(
                project_id, agent_id,
                decision=decision,
                message=f"{agent_config.get('name', agent_id)} completó análisis: {decision.upper()}"
            )
            
            deliberation = Deliberation(
                project_id=project_id,
                stage=stage,
                agent_id=agent_id,
                decision=decision,
                analysis=analysis,
                rag_context=rag_context,
                empresa_id=empresa_id
            )
            
            if project_id not in self.deliberations:
                self.deliberations[project_id] = []
            self.deliberations[project_id].append(deliberation)
            
            all_deliberations.append({
                "stage": stage.value,
                "agent_id": agent_id,
                "agent_name": reasoning_result.get("agent_name", agent_id),
                "decision": decision,
                "analysis": analysis[:500] + "..." if len(analysis) > 500 else analysis,
                "compliance_pillars": reasoning_result.get("compliance_pillars", {}),
                "model_used": reasoning_result.get("model_used", "unknown"),
                "tokens_used": reasoning_result.get("tokens_used", 0),
                "empresa_id": empresa_id
            })
            
            previous_analyses.append({
                "agent_name": reasoning_result.get("agent_name", agent_id),
                "analysis": analysis
            })
            
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            
            stage_results_so_far = {d["stage"]: d for d in all_deliberations}
            await deliberation_state_repository.save_state(
                project_id=project_id,
                empresa_id=empresa_id,
                current_stage=stage.value,
                stage_results=stage_results_so_far,
                status="in_progress",
                project_data=project
            )
            
            findings, recommendations = self._extract_findings_recommendations(analysis)
            report_type = STAGE_TO_REPORT_TYPE.get(stage, "analisis")
            version = defense_file_service.get_document_count(project_id, agent_id) + 1
            
            decision_label = "APROBADO" if decision == "approve" else "RECHAZADO" if decision == "reject" else "SOLICITUD_AJUSTE" if decision == "request_adjustment" else "PENDIENTE"
            
            report_path = self.report_generator.generate_agent_report(
                project_id=project_id,
                agent_id=agent_id,
                agent_name=reasoning_result.get("agent_name", agent_id),
                agent_role=agent_config.get("role", "Agente"),
                report_type=report_type,
                version=version,
                project_data=project,
                analysis=analysis,
                decision=decision_label,
                findings=findings,
                recommendations=recommendations
            )
            
            pcloud_link = None
            full_report_path = None
            
            if report_path:
                ROOT_DIR = Path(__file__).parent.parent
                full_report_path = str(ROOT_DIR / report_path.lstrip('/'))
                
                pcloud_result = evidence_portfolio_service.upload_document(
                    project_id=project_id,
                    file_path=full_report_path,
                    doc_type=report_type,
                    agent_id=agent_id
                )
                
                if pcloud_result.get("success"):
                    pcloud_link = pcloud_result.get("download_url") or pcloud_result.get("pcloud_path")
                    defense_file_service.add_pcloud_document(
                        project_id=project_id,
                        agent_id=agent_id,
                        doc_type=f"reporte_{report_type}",
                        local_path=full_report_path,
                        pcloud_path=pcloud_result.get("pcloud_path", ""),
                        pcloud_link=pcloud_link,
                        file_id=pcloud_result.get("file_id")
                    )
                    logger.info(f"☁️ Uploaded to pCloud: {pcloud_result.get('filename')}")
                else:
                    logger.warning(f"pCloud upload failed (offline mode): {pcloud_result.get('error')}")
                
                defense_file_service.add_document(
                    project_id=project_id,
                    stage=stage.value,
                    agent_id=agent_id,
                    doc_type=f"reporte_{report_type}",
                    file_path=report_path,
                    version=version,
                    pcloud_link=pcloud_link
                )
                logger.info(f"📄 Generated report for {agent_id}: {report_path}")
                
                try:
                    audit_result = auditor_service.audit_stage_upload(project_id, stage.value, agent_id)
                    if audit_result.get("audit_passed"):
                        logger.info(f"✅ [A8_AUDITOR] Document audit passed for {agent_id}")
                    else:
                        logger.warning(f"⚠️ [A8_AUDITOR] Document audit incomplete: {audit_result.get('message')}")
                except Exception as audit_error:
                    logger.warning(f"[A8_AUDITOR] Audit check failed: {audit_error}")
            
            if decision == "request_adjustment":
                mod_version = defense_file_service.get_document_count(project_id, agent_id) + 1
                mod_report_path = self.report_generator.generate_agent_report(
                    project_id=project_id,
                    agent_id=agent_id,
                    agent_name=reasoning_result.get("agent_name", agent_id),
                    agent_role=agent_config.get("role", "Agente"),
                    report_type="solicitud_modificacion",
                    version=mod_version,
                    project_data=project,
                    analysis=analysis,
                    decision="SOLICITUD_MODIFICACION",
                    findings=findings,
                    recommendations=recommendations
                )
                
                if mod_report_path:
                    defense_file_service.add_document(
                        project_id=project_id,
                        stage=stage.value,
                        agent_id=agent_id,
                        doc_type="solicitud_modificacion",
                        file_path=mod_report_path,
                        version=mod_version
                    )
                    logger.info(f"📝 Generated modification request for {agent_id}: {mod_report_path}")
                
                try:
                    adjustments = auditor_service.extract_adjustments_from_analysis(analysis)
                    provider_email = project.get("provider_email") or project.get("submitter_email", "")
                    
                    if provider_email and adjustments:
                        email_result = auditor_service.send_adjustment_email(
                            project_id=project_id,
                            agent_id=agent_id,
                            decision=decision,
                            adjustments=adjustments,
                            provider_email=provider_email
                        )
                        if email_result.get("success"):
                            logger.info(f"📧 [A8_AUDITOR] Adjustment email sent to provider: {provider_email}")
                            defense_file_service.add_email(project_id, {
                                "from_email": "auditoria@revisar-ia.com",
                                "to_email": provider_email,
                                "subject": f"Revisar.ia - Ajustes Requeridos Proyecto {project_id}",
                                "body": f"Ajustes requeridos: {', '.join(adjustments[:3])}...",
                                "message_id": email_result.get("message_id", ""),
                                "type": "adjustment_notification"
                            })
                        else:
                            logger.warning(f"[A8_AUDITOR] Failed to send adjustment email: {email_result.get('error')}")
                except Exception as adj_error:
                    logger.error(f"[A8_AUDITOR] Error processing adjustment notification: {adj_error}")
            
            next_stage = self.get_next_stage(stage)
            if next_stage and next_stage != WorkflowStage.E5_APROBADO:
                next_agent_id = STAGE_TO_AGENT.get(next_stage)
                next_agent = self.get_agent_config(next_agent_id)
                
                if next_agent:
                    await event_emitter.emit_sending(project_id, agent_id, next_agent_id)
                    
                    # Run synchronous LLM call in thread to avoid blocking event loop
                    email_body = await asyncio.to_thread(
                        agentic_service.generate_inter_agent_message,
                        from_agent=agent_id,
                        to_agent=next_agent_id,
                        project_data=project,
                        analysis_result=reasoning_result,
                        stage=stage.value
                    )
                    
                    email_subject = f"[Revisar.IA] Deliberación {project_id}: {project.get('name', '')}"
                    
                    try:
                        attachments = []
                        if full_report_path and Path(full_report_path).exists():
                            attachments.append(full_report_path)
                        
                        if attachments:
                            email_result = self.email_service.send_email_with_attachments(
                                from_agent_id=agent_id,
                                to_email=next_agent.get("email", ""),
                                subject=email_subject,
                                body=email_body,
                                attachments=attachments
                            )
                        else:
                            email_result = self.email_service.send_email(
                                from_agent_id=agent_id,
                                to_email=next_agent.get("email", ""),
                                subject=email_subject,
                                body=email_body
                            )
                        
                        deliberation.email_sent = email_result
                        
                        if email_result.get("success"):
                            defense_file_service.add_email(project_id, {
                                "from_email": agent_config.get("email", ""),
                                "to_email": next_agent.get("email", ""),
                                "subject": f"[Revisar.IA] Deliberación {stage.value}",
                                "body": email_body[:500],
                                "message_id": email_result.get("message_id", ""),
                                "attachments": email_result.get("attachments", [])
                            })
                            
                            evidence_portfolio_service.add_to_communication_log(
                                project_id=project_id,
                                entry={
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "action": "email_sent",
                                    "from_agent": agent_id,
                                    "to_agent": next_agent_id,
                                    "email_subject": email_subject,
                                    "attachment_name": Path(full_report_path).name if full_report_path else None,
                                    "pcloud_link": pcloud_link
                                }
                            )
                            logger.info(f"📧 Email with attachment sent from {agent_id} to {next_agent_id}")
                            
                    except Exception as e:
                        logger.error(f"Error sending inter-agent email: {e}")
            
            if decision == "reject":
                rejection_version = defense_file_service.get_document_count(project_id, agent_id) + 1
                rejection_report_path = self.report_generator.generate_agent_report(
                    project_id=project_id,
                    agent_id=agent_id,
                    agent_name=reasoning_result.get("agent_name", agent_id),
                    agent_role=agent_config.get("role", "Agente"),
                    report_type="dictamen_rechazo",
                    version=rejection_version,
                    project_data=project,
                    analysis=analysis,
                    decision="RECHAZADO",
                    findings=findings,
                    recommendations=recommendations
                )
                
                if rejection_report_path:
                    defense_file_service.add_document(
                        project_id=project_id,
                        stage=stage.value,
                        agent_id=agent_id,
                        doc_type="dictamen_rechazo",
                        file_path=rejection_report_path,
                        version=rejection_version
                    )
                    logger.info(f"📛 Generated rejection document for {agent_id}: {rejection_report_path}")
                
                defense_file_service.finalize_defense_file(
                    project_id,
                    "rejected",
                    f"Rechazado en etapa {stage.value} por {agent_id}: {analysis[:200]}"
                )
                
                try:
                    defense_audit = auditor_service.audit_defense_zip(project_id)
                    if defense_audit.get("audit_passed"):
                        logger.info(f"✅ [A8_AUDITOR] Defense File audit passed for {project_id}")
                    else:
                        logger.warning(f"⚠️ [A8_AUDITOR] Defense File audit issues: {defense_audit.get('issues', [])}")
                except Exception as audit_err:
                    logger.warning(f"[A8_AUDITOR] Defense File audit failed: {audit_err}")
                
                pmo_consolidation_result = await self._run_pmo_consolidation(
                    project_id=project_id,
                    project=project,
                    all_deliberations=all_deliberations,
                    final_status="RECHAZADO"
                )
                
                bitacora_result = self._generate_and_upload_bitacora(project_id, project)
                
                await event_emitter.emit(
                    project_id, agent_id, "complete",
                    f"Análisis completado. Proyecto RECHAZADO por {agent_config.get('name', agent_id)}",
                    progress=100,
                    extra_data={"final": True, "final_status": "RECHAZADO", "rejected_by": agent_id}
                )
                
                # Persist state as failed
                await deliberation_state_repository.save_state(
                    project_id=project_id,
                    empresa_id=empresa_id,
                    current_stage=stage.value,
                    stage_results={d["stage"]: d for d in all_deliberations},
                    status="failed",
                    project_data=project
                )
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "final_status": "RECHAZADO",
                    "rejected_at_stage": stage.value,
                    "rejected_by": agent_id,
                    "rejection_document": rejection_report_path,
                    "deliberations": all_deliberations,
                    "total_stages_completed": len(all_deliberations),
                    "defense_file_finalized": True,
                    "bitacora_generated": bitacora_result.get("success", False),
                    "bitacora_link": bitacora_result.get("pcloud_link"),
                    "pmo_consolidation": pmo_consolidation_result
                }
            
            current_stage = stage
        
        consolidated_analysis = "\n\n".join([
            f"**{d['agent_name']} ({d['stage']}):**\n{d['analysis']}"
            for d in all_deliberations
        ])
        
        approved_by_agents = [
            f"{d['agent_name']} ({d['stage']})"
            for d in all_deliberations
        ]
        
        po_result = None
        po_number = None
        po_path = None
        
        try:
            from services.purchase_order_service import PurchaseOrderService
            from services.database import get_db
            
            db = get_db()
            if db:
                purchase_order_service = PurchaseOrderService(db)
                po_result = await purchase_order_service.generate_purchase_order(
                    project_id=project_id,
                    project_data=project,
                    consolidated_analysis=consolidated_analysis,
                    approved_by_agents=approved_by_agents
                )
                
                if po_result:
                    po_number = po_result.get("po_number")
                    po_path = po_result.get("pdf_path")
                    
                    if po_path:
                        defense_file_service.add_document(
                            project_id=project_id,
                            stage=WorkflowStage.E5_APROBADO.value,
                            agent_id="SYSTEM",
                            doc_type="orden_compra",
                            file_path=str(po_path),
                            version=1
                        )
                        logger.info(f"✅ Generated Purchase Order: {po_number}")
        except Exception as e:
            logger.warning(f"PurchaseOrderService not available, generating approval document: {e}")
            
            approval_report_path = self.report_generator.generate_agent_report(
                project_id=project_id,
                agent_id="SYSTEM",
                agent_name="Sistema Revisar.IA",
                agent_role="Aprobación Final",
                report_type="aprobacion_final",
                version=1,
                project_data=project,
                analysis=consolidated_analysis[:2000],
                decision="APROBADO",
                findings=[f"Aprobado por {agent}" for agent in approved_by_agents],
                recommendations=["Proceder con la ejecución del proyecto"]
            )
            
            if approval_report_path:
                po_path = approval_report_path
                defense_file_service.add_document(
                    project_id=project_id,
                    stage=WorkflowStage.E5_APROBADO.value,
                    agent_id="SYSTEM",
                    doc_type="aprobacion_final",
                    file_path=approval_report_path,
                    version=1
                )
                logger.info(f"✅ Generated approval document: {approval_report_path}")
        
        defense_file_service.finalize_defense_file(
            project_id,
            "approved",
            f"Aprobado por todos los agentes. Deliberaciones: {len(all_deliberations)}"
        )
        
        try:
            defense_audit = auditor_service.audit_defense_zip(project_id)
            if defense_audit.get("audit_passed"):
                logger.info(f"✅ [A8_AUDITOR] Defense File audit passed for {project_id}")
            else:
                logger.warning(f"⚠️ [A8_AUDITOR] Defense File audit issues: {defense_audit.get('issues', [])}")
        except Exception as audit_err:
            logger.warning(f"[A8_AUDITOR] Defense File audit failed: {audit_err}")
        
        pmo_consolidation_result = await self._run_pmo_consolidation(
            project_id=project_id,
            project=project,
            all_deliberations=all_deliberations,
            final_status="APROBADO"
        )
        
        legal_to_provider_email_result = await self._send_legal_to_provider_email(
            project_id=project_id,
            project=project
        )
        
        bitacora_result = self._generate_and_upload_bitacora(project_id, project)
        
        # Persist state as completed
        await deliberation_state_repository.save_state(
            project_id=project_id,
            empresa_id=empresa_id,
            current_stage=WorkflowStage.E5_APROBADO.value,
            stage_results={d["stage"]: d for d in all_deliberations},
            status="completed",
            project_data=project
        )
        
        await event_emitter.emit(
            project_id, "SYSTEM", "complete",
            "Análisis multi-agente completado. Proyecto APROBADO.",
            progress=100,
            extra_data={"final": True, "final_status": "APROBADO"}
        )
        
        result = {
            "success": True,
            "project_id": project_id,
            "final_status": "APROBADO",
            "deliberations": all_deliberations,
            "total_stages_completed": len(all_deliberations),
            "compliance_summary": self._summarize_compliance(all_deliberations),
            "defense_file_finalized": True,
            "audit_ready": True,
            "bitacora_generated": bitacora_result.get("success", False),
            "bitacora_link": bitacora_result.get("pcloud_link"),
            "pcloud_documents": defense_file_service.get_pcloud_links(project_id),
            "pmo_consolidation": pmo_consolidation_result,
            "legal_to_provider_email": legal_to_provider_email_result
        }
        
        if po_number:
            result["purchase_order_number"] = po_number
        if po_path:
            result["purchase_order_path"] = po_path
        
        return result
    
    async def resume_deliberation(self, project_id: str, force: bool = False) -> Dict:
        """
        Resume a paused or failed deliberation from the last completed stage.
        Skips stages that have already been completed based on saved state.
        Uses stage_order to determine proper ordering (not dict insertion order).
        """
        state = await deliberation_state_repository.get_state(project_id)
        if not state:
            return {"success": False, "error": f"No saved state for project {project_id}"}
        
        if state.get("status") == "completed":
            return {"success": False, "error": "Deliberation already completed"}
        
        stage_results = state.get("stage_results", {})
        stage_order = [s.value for s in WORKFLOW_ORDER[:-1]]
        
        ordered_completed = [s for s in stage_order if s in stage_results]
        last_completed_stage = ordered_completed[-1] if ordered_completed else None
        
        if stage_results and not force:
            for stage in ordered_completed:
                stage_data = stage_results.get(stage, {})
                if stage_data.get("decision") == "reject":
                    return {
                        "success": False, 
                        "error": f"Cannot resume: project was rejected at stage {stage} by {stage_data.get('agent_id')}. Use force=true to override.",
                        "rejected_stage": stage,
                        "rejected_by": stage_data.get("agent_id")
                    }
        
        project_data = state.get("project_data")
        if not project_data:
            return {"success": False, "error": "No project data in saved state"}
        
        empresa_id = state.get("empresa_id", "unknown")
        
        logger.info(f"Resuming deliberation for {project_id}, last completed: {last_completed_stage}, all completed: {ordered_completed}")
        
        await deliberation_state_repository.update_status(project_id, "in_progress")
        
        return await self._resume_from_stage(
            project_id=project_id,
            project=project_data,
            empresa_id=empresa_id,
            last_completed_stage=last_completed_stage,
            previous_results=stage_results
        )
    
    async def _resume_from_stage(
        self,
        project_id: str,
        project: Dict,
        empresa_id: str,
        last_completed_stage: str,
        previous_results: Dict[str, Any]
    ) -> Dict:
        """
        Continue deliberation from a specific stage, skipping already completed stages.
        last_completed_stage: The last stage that was fully completed (or None to start from E1).
        """
        event_emitter.create_session(project_id)
        
        all_deliberations = list(previous_results.values())
        previous_analyses = [
            {"agent_name": d.get("agent_name", d.get("agent_id")), "analysis": d.get("analysis", "")}
            for d in all_deliberations
        ]
        
        stage_order = [s.value for s in WORKFLOW_ORDER[:-1]]
        
        if last_completed_stage is None:
            start_idx = 0
        else:
            try:
                start_idx = stage_order.index(last_completed_stage) + 1
            except ValueError:
                start_idx = 0
        
        if start_idx >= len(stage_order):
            return {
                "success": True,
                "project_id": project_id,
                "message": "All stages already completed",
                "deliberations": all_deliberations,
                "resumed": True
            }
        
        remaining_stages = stage_order[start_idx:]
        logger.info(f"Resuming from index {start_idx}, remaining stages: {remaining_stages}")
        
        preloaded_rag_contexts = preload_rag_contexts_parallel(project, self.rag_service)
        
        for stage_value in remaining_stages:
            stage = WorkflowStage(stage_value)
            agent_id = STAGE_TO_AGENT.get(stage)
            if not agent_id:
                continue
            
            agent_config = self.get_agent_config(agent_id)
            if not agent_config:
                continue
            
            logger.info(f"[RESUME] Stage {stage.value}: Agent {agent_id} reasoning...")
            
            await event_emitter.emit_thinking(
                project_id, agent_id,
                f"{agent_config.get('name', agent_id)} está revisando el proyecto (reanudado)..."
            )
            
            rag_context = preloaded_rag_contexts.get(agent_id, [])
            rag_texts = [doc.get("content", "") for doc in rag_context] if rag_context else []
            
            # Obtener contexto evolutivo del cliente si está disponible (resume)
            cliente_id = get_cliente_id_from_project(project)
            project_description = f"{project.get('name', '')} {project.get('description', '')}"
            if cliente_id:
                try:
                    cliente_contexto_str = await cliente_contexto_service.get_contexto_para_agente(
                        cliente_id=cliente_id,
                        agente_id=agent_id
                    )
                    if cliente_contexto_str and not cliente_contexto_str.startswith("[ERROR]"):
                        rag_texts = [cliente_contexto_str] + rag_texts
                        logger.info(f"✅ [RESUME] Contexto evolutivo incluido para {agent_id}, cliente {cliente_id}")
                except Exception as ctx_err:
                    logger.warning(f"[RESUME] Error obteniendo contexto evolutivo: {ctx_err}")
            
            reasoning_start_time = datetime.now(timezone.utc)
            
            # Run synchronous LLM call in thread to avoid blocking event loop
            reasoning_result = await asyncio.to_thread(
                agentic_service.reason_about_project,
                agent_id=agent_id,
                project_data=project,
                rag_context=rag_texts,
                previous_deliberations=previous_analyses
            )
            
            reasoning_elapsed_ms = int((datetime.now(timezone.utc) - reasoning_start_time).total_seconds() * 1000)
            
            decision = reasoning_result.get("decision", "pending")
            analysis = reasoning_result.get("analysis", "Análisis no disponible")
            
            # Registrar la interacción del agente (resume)
            if cliente_id:
                try:
                    await cliente_contexto_service.registrar_interaccion(
                        cliente_id=cliente_id,
                        agente_id=agent_id,
                        agente_nombre=agent_config.get("name", agent_id),
                        tipo="deliberacion_resume",
                        pregunta_usuario=f"Análisis de proyecto (reanudado): {project.get('name', 'Sin nombre')}",
                        respuesta_agente=analysis[:2000] if analysis else "Sin análisis",
                        hallazgos={
                            "decision": decision,
                            "stage": stage.value,
                            "resumed": True
                        },
                        duracion_ms=reasoning_elapsed_ms,
                        tokens_usados=reasoning_result.get("tokens_used", 0)
                    )
                    logger.info(f"✅ [RESUME] Interacción registrada para cliente {cliente_id}, agente {agent_id}")
                except Exception as reg_err:
                    logger.warning(f"[RESUME] Error registrando interacción: {reg_err}")
            
            deliberation = Deliberation(
                project_id=project_id,
                stage=stage,
                agent_id=agent_id,
                decision=decision,
                analysis=analysis,
                rag_context=rag_context,
                empresa_id=empresa_id
            )
            
            delib_dict = {
                "stage": stage.value,
                "agent_id": agent_id,
                "agent_name": reasoning_result.get("agent_name", agent_id),
                "decision": decision,
                "analysis": analysis[:500] + "..." if len(analysis) > 500 else analysis,
                "compliance_pillars": reasoning_result.get("compliance_pillars", {}),
                "model_used": reasoning_result.get("model_used", "unknown"),
                "tokens_used": reasoning_result.get("tokens_used", 0),
                "empresa_id": empresa_id
            }
            
            all_deliberations.append(delib_dict)
            previous_analyses.append({
                "agent_name": reasoning_result.get("agent_name", agent_id),
                "analysis": analysis
            })
            
            defense_file_service.add_deliberation(project_id, deliberation.to_dict())
            
            stage_results_so_far = {d["stage"]: d for d in all_deliberations}
            await deliberation_state_repository.save_state(
                project_id=project_id,
                empresa_id=empresa_id,
                current_stage=stage.value,
                stage_results=stage_results_so_far,
                status="in_progress",
                project_data=project
            )
            
            if decision == "reject":
                await deliberation_state_repository.save_state(
                    project_id=project_id,
                    empresa_id=empresa_id,
                    current_stage=stage.value,
                    stage_results=stage_results_so_far,
                    status="failed",
                    project_data=project
                )
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "final_status": "RECHAZADO",
                    "rejected_at_stage": stage.value,
                    "rejected_by": agent_id,
                    "deliberations": all_deliberations,
                    "resumed": True
                }
        
        await deliberation_state_repository.save_state(
            project_id=project_id,
            empresa_id=empresa_id,
            current_stage=WorkflowStage.E5_APROBADO.value,
            stage_results={d["stage"]: d for d in all_deliberations},
            status="completed",
            project_data=project
        )
        
        defense_file_service.finalize_defense_file(
            project_id,
            "approved",
            f"Aprobado (reanudado). Deliberaciones: {len(all_deliberations)}"
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "final_status": "APROBADO",
            "deliberations": all_deliberations,
            "total_stages_completed": len(all_deliberations),
            "resumed": True
        }
    
    async def _send_legal_to_provider_email(
        self,
        project_id: str,
        project: Dict
    ) -> Dict:
        """
        Send email from Legal to provider when project is approved.
        Includes PMO (Carlos) as CC for coordination.
        """
        logger.info(f"📧 Sending Legal to Provider email for project {project_id}")
        
        try:
            provider_email = (
                project.get("sponsor_email") or
                project.get("submitter_email") or
                project.get("client_email") or
                project.get("contact_email")
            )
            
            if not provider_email:
                df = defense_file_service.get_defense_file(project_id)
                if df:
                    df_data = df if isinstance(df, dict) else {}
                    project_data_from_df = df_data.get("project_data", {})
                    provider_email = (
                        project_data_from_df.get("sponsor_email") or
                        df_data.get("sponsor_email") or
                        project_data_from_df.get("submitter_email") or
                        project_data_from_df.get("email")
                    )
                    if provider_email:
                        logger.info(f"📧 Found provider email from defense file: {provider_email}")
            
            logger.info(f"📧 Provider email for {project_id}: {provider_email or 'NOT FOUND'}")
            
            if not provider_email:
                logger.warning(f"No provider email found for project {project_id}")
                return {"success": False, "error": "No provider email found"}
            
            project_name = project.get("name", "Sin nombre")
            client_name = project.get("client_name") or project.get("sponsor_name", "Proveedor")
            amount = project.get("amount", 0)
            
            pmo_email = "pmo@revisar-ia.com"
            
            email_subject = f"[Revisar.IA] Coordinación de Contrato - {project_name}"
            
            email_body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRUPO FORTEZZA - COORDINACIÓN DE CONTRATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimado(a) {client_name},

Le informamos que el proyecto "{project_name}" ha sido aprobado por 
todos los departamentos de Revisar.ia a través del Sistema Revisar.IA.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETALLES DEL PROYECTO APROBADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔢 ID del Proyecto: {project_id}
📋 Nombre: {project_name}
💰 Monto Aprobado: ${amount:,.2f} MXN
📅 Fecha de Aprobación: {datetime.now(timezone.utc).strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGUIENTES PASOS - COORDINACIÓN DE CONTRATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El Departamento Legal de Revisar.ia está listo para coordinar
la firma del contrato correspondiente. Por favor:

1. Confirme su disponibilidad para agendar la firma del contrato
2. Proporcione la documentación legal requerida de su empresa:
   - Acta constitutiva
   - Poder del representante legal
   - Identificación oficial del representante
   - Comprobante de domicilio fiscal
   - Constancia de Situación Fiscal vigente

3. Indique si requiere revisión de alguna cláusula contractual

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTACTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Para cualquier duda o aclaración, puede contactarnos:
📧 Legal: legal@revisar-ia.com
📧 PMO (Carlos Mendoza): pmo@revisar-ia.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quedamos en espera de su respuesta para proceder con la formalización
del contrato.

Atentamente,

Equipo Legal
Revisar.ia
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este correo es parte del trail de auditoría del Sistema Revisar.IA 
para cumplimiento SAT (Art. 69-B CFF / NOM-151)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            email_result = self.email_service.send_email(
                from_agent_id="LEGAL",
                to_email=provider_email,
                subject=email_subject,
                body=email_body,
                cc_emails=[pmo_email]
            )
            
            if email_result.get("success"):
                logger.info(f"📧 Legal to Provider email sent to {provider_email} (CC: {pmo_email})")
                
                defense_file_service.add_email(project_id, {
                    "from_email": "legal@revisar-ia.com",
                    "to_email": provider_email,
                    "cc_emails": [pmo_email],
                    "subject": email_subject,
                    "body": email_body[:500],
                    "message_id": email_result.get("message_id", ""),
                    "type": "legal_to_provider_coordination"
                })
                
                defense_file_service.add_provider_communication(project_id, {
                    "type": "contract_coordination_request",
                    "from_department": "LEGAL",
                    "to_provider": provider_email,
                    "cc": [pmo_email],
                    "subject": email_subject,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                evidence_portfolio_service.add_to_communication_log(
                    project_id=project_id,
                    entry={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "legal_to_provider_email_sent",
                        "from_agent": "LEGAL",
                        "to_agent": "PROVIDER",
                        "to_email": provider_email,
                        "cc_emails": [pmo_email],
                        "email_subject": email_subject,
                        "type": "contract_coordination"
                    }
                )
                
                return {
                    "success": True,
                    "to_email": provider_email,
                    "cc_emails": [pmo_email],
                    "subject": email_subject,
                    "message_id": email_result.get("message_id")
                }
            else:
                logger.warning(f"Failed to send Legal to Provider email: {email_result}")
                return {"success": False, "error": email_result.get("error", "Unknown error")}
                
        except Exception as e:
            logger.error(f"Error sending Legal to Provider email for {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_findings_recommendations(self, analysis: str) -> Tuple[List[str], List[str]]:
        """
        Parse analysis text to extract findings and recommendations.
        Uses regex patterns to identify structured content.
        """
        findings = []
        recommendations = []
        
        findings_patterns = [
            r'(?:hallazgo|finding|observación|observacion|conclusión|conclusion)[s]?[\s:]+([^\n]+)',
            r'(?:se\s+(?:observa|detecta|identifica|encuentra))[s]?[\s:]+([^\n]+)',
            r'•\s*([^\n]+)',
            r'-\s*([^\n]+)',
            r'\d+\.\s*([^\n]+)',
        ]
        
        recommendations_patterns = [
            r'(?:recomendación|recomendacion|recommendation|sugerencia)[s]?[\s:]+([^\n]+)',
            r'(?:se\s+(?:recomienda|sugiere|propone))[s]?[\s:]+([^\n]+)',
            r'(?:debe|debería|deberá|should)[\s:]+([^\n]+)',
        ]
        
        analysis_lower = analysis.lower()
        
        for pattern in findings_patterns:
            matches = re.findall(pattern, analysis_lower, re.IGNORECASE)
            for match in matches[:3]:
                if len(match.strip()) > 10:
                    findings.append(match.strip().capitalize())
        
        for pattern in recommendations_patterns:
            matches = re.findall(pattern, analysis_lower, re.IGNORECASE)
            for match in matches[:3]:
                if len(match.strip()) > 10:
                    recommendations.append(match.strip().capitalize())
        
        if not findings:
            paragraphs = analysis.split('\n\n')
            for para in paragraphs[:2]:
                if len(para.strip()) > 20:
                    findings.append(para.strip()[:200])
        
        if not recommendations:
            if "cumple" in analysis_lower or "aprobado" in analysis_lower:
                recommendations.append("Continuar con el proceso de aprobación")
            elif "rechaz" in analysis_lower:
                recommendations.append("Revisar y corregir las observaciones señaladas")
            else:
                recommendations.append("Evaluar criterios de cumplimiento normativo")
        
        findings = list(set(findings))[:5]
        recommendations = list(set(recommendations))[:5]
        
        return findings, recommendations
    
    async def _run_pmo_consolidation(
        self,
        project_id: str,
        project: Dict,
        all_deliberations: List[Dict],
        final_status: str
    ) -> Dict:
        """
        Run PMO consolidation: Carlos generates a final report and sends it to the submitter.
        Includes all PDFs as attachments.
        """
        logger.info(f"🔄 Starting PMO consolidation for project {project_id}")
        
        await event_emitter.emit_analyzing(
            project_id, "A2_PMO",
            "Carlos Mendoza consolidando análisis de todos los agentes...",
            progress=85
        )
        
        try:
            # Run synchronous LLM call in thread to avoid blocking event loop
            consolidation_result = await asyncio.to_thread(
                agentic_service.generate_pmo_consolidation,
                project_data=project,
                all_deliberations=all_deliberations,
                final_status=final_status
            )
            
            if not consolidation_result.get("success"):
                logger.error(f"PMO consolidation failed: {consolidation_result}")
                return {"success": False, "error": "Consolidation generation failed"}
            
            logger.info(f"✅ PMO consolidation generated with {consolidation_result.get('tokens_used', 0)} tokens")
            
            defense_file_service.set_consolidation_report(project_id, {
                "full_report": consolidation_result.get("consolidation", ""),
                "final_status": final_status,
                "tokens_used": consolidation_result.get("tokens_used", 0),
                "model_used": consolidation_result.get("model_used", "GPT-4o"),
                "audit_metadata": consolidation_result.get("audit_metadata", {})
            })
            
            await event_emitter.emit_auditing(
                project_id, "STRATEGY_COUNCIL",
                "Consejo de Estrategia validando respuesta (anti-alucinación)..."
            )
            
            consolidation_text = consolidation_result.get("consolidation", "")
            findings, recommendations = self._extract_findings_recommendations(consolidation_text)
            
            ROOT_DIR = Path(__file__).parent.parent
            consolidation_report_path = self.report_generator.generate_agent_report(
                project_id=project_id,
                agent_id="A2_PMO",
                agent_name="Carlos Mendoza",
                agent_role="Gerente PMO",
                report_type="consolidacion",
                version=1,
                project_data=project,
                analysis=consolidation_text,
                decision=final_status.upper(),
                findings=findings,
                recommendations=recommendations
            )
            
            pcloud_consolidation_link = None
            full_consolidation_path = None
            
            if consolidation_report_path:
                full_consolidation_path = str(ROOT_DIR / consolidation_report_path.lstrip('/'))
                
                pcloud_result = evidence_portfolio_service.upload_document(
                    project_id=project_id,
                    file_path=full_consolidation_path,
                    doc_type="consolidacion",
                    agent_id="A2_PMO"
                )
                
                if pcloud_result.get("success"):
                    pcloud_consolidation_link = pcloud_result.get("download_url") or pcloud_result.get("pcloud_path")
                    defense_file_service.add_pcloud_document(
                        project_id=project_id,
                        agent_id="A2_PMO",
                        doc_type="reporte_consolidacion",
                        local_path=full_consolidation_path,
                        pcloud_path=pcloud_result.get("pcloud_path", ""),
                        pcloud_link=pcloud_consolidation_link,
                        file_id=pcloud_result.get("file_id")
                    )
                    logger.info(f"☁️ Consolidation uploaded to pCloud: {pcloud_result.get('filename')}")
                
                defense_file_service.add_document(
                    project_id=project_id,
                    stage="E5_APROBADO",
                    agent_id="A2_PMO",
                    doc_type="reporte_consolidacion",
                    file_path=consolidation_report_path,
                    version=1,
                    pcloud_link=pcloud_consolidation_link
                )
                logger.info(f"📄 Generated consolidation report: {consolidation_report_path}")
            
            submitter_email = (
                project.get("sponsor_email") or
                project.get("submitter_email") or 
                project.get("email") or 
                project.get("client_email") or
                project.get("contact_email")
            )
            
            if not submitter_email:
                df = defense_file_service.get_defense_file(project_id)
                if df:
                    df_data = df if isinstance(df, dict) else {}
                    project_data_from_df = df_data.get("project_data", {})
                    submitter_email = (
                        project_data_from_df.get("sponsor_email") or
                        df_data.get("sponsor_email") or
                        project_data_from_df.get("submitter_email") or
                        project_data_from_df.get("email")
                    )
                    if submitter_email:
                        logger.info(f"📧 Found submitter email from defense file: {submitter_email}")
            
            logger.info(f"📧 Submitter email for {project_id}: {submitter_email or 'NOT FOUND'}")
            
            if submitter_email:
                pcloud_links = defense_file_service.get_pcloud_links(project_id)
                
                # Run synchronous LLM call in thread to avoid blocking event loop
                email_body = await asyncio.to_thread(
                    agentic_service.generate_consolidation_email,
                    project_data=project,
                    consolidation_result=consolidation_result,
                    pcloud_links=pcloud_links,
                    deliberations=all_deliberations
                )
                
                attachments = []
                
                reports_dir = ROOT_DIR / "reports"
                if reports_dir.exists():
                    short_id = project_id.replace("PROJ-", "")[:3]
                    for pdf_file in reports_dir.glob(f"*{short_id}*.pdf"):
                        if pdf_file.exists():
                            attachments.append(str(pdf_file))
                            logger.info(f"📎 Adding attachment: {pdf_file.name}")
                
                email_subject = f"[Revisar.IA] Resultado de Evaluación - {project.get('name', project_id)} - {final_status.upper()}"
                
                try:
                    if attachments:
                        email_result = self.email_service.send_email_with_attachments(
                            from_agent_id="A2_PMO",
                            to_email=submitter_email,
                            subject=email_subject,
                            body=email_body,
                            attachments=attachments
                        )
                    else:
                        email_result = self.email_service.send_email(
                            from_agent_id="A2_PMO",
                            to_email=submitter_email,
                            subject=email_subject,
                            body=email_body
                        )
                    
                    if email_result.get("success"):
                        logger.info(f"📧 Consolidation email sent to {submitter_email} with {len(attachments)} attachments")
                        
                        evidence_portfolio_service.add_to_communication_log(
                            project_id=project_id,
                            entry={
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "action": "consolidation_email_sent",
                                "from_agent": "A2_PMO",
                                "to_agent": "SOLICITANTE",
                                "to_email": submitter_email,
                                "email_subject": email_subject,
                                "attachments_count": len(attachments),
                                "pcloud_link": pcloud_consolidation_link
                            }
                        )
                        
                        defense_file_service.add_email(project_id, {
                            "from_email": "pmo@revisar-ia.com",
                            "to_email": submitter_email,
                            "subject": email_subject,
                            "body": email_body[:500],
                            "message_id": email_result.get("message_id", ""),
                            "attachments": [Path(a).name for a in attachments]
                        })
                    else:
                        logger.warning(f"Failed to send consolidation email: {email_result}")
                        
                except Exception as e:
                    logger.error(f"Error sending consolidation email: {e}")
            else:
                logger.warning(f"No submitter email found for project {project_id}")
            
            return {
                "success": True,
                "agent_id": "A2_PMO",
                "agent_name": "Carlos Mendoza",
                "consolidation_generated": True,
                "consolidation_report_path": consolidation_report_path,
                "pcloud_link": pcloud_consolidation_link,
                "email_sent": submitter_email is not None,
                "submitter_email": submitter_email,
                "tokens_used": consolidation_result.get("tokens_used", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in PMO consolidation for {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_and_upload_bitacora(self, project_id: str, project: Dict) -> Dict:
        """
        Generate the final bitácora PDF and upload to pCloud.
        Returns result with pcloud_link.
        """
        try:
            communication_log = evidence_portfolio_service.get_communication_log(project_id)
            communications = communication_log.get("entries", [])
            
            if not communications:
                logger.info(f"No communications to include in bitácora for {project_id}")
                return {"success": False, "error": "No communications recorded"}
            
            bitacora_path = self.report_generator.generate_bitacora_pdf(
                project_id=project_id,
                communications=communications,
                project_data=project
            )
            
            if not bitacora_path:
                logger.error(f"Failed to generate bitácora PDF for {project_id}")
                return {"success": False, "error": "Failed to generate PDF"}
            
            pcloud_result = evidence_portfolio_service.upload_bitacora_to_pcloud(
                project_id=project_id,
                bitacora_pdf_path=bitacora_path
            )
            
            pcloud_link = None
            if pcloud_result.get("success"):
                pcloud_link = pcloud_result.get("download_url") or pcloud_result.get("pcloud_path")
                defense_file_service.set_bitacora_link(project_id, pcloud_link)
                logger.info(f"📋 Bitácora uploaded to pCloud: {pcloud_link}")
            else:
                logger.warning(f"Bitácora pCloud upload failed (offline mode): {pcloud_result.get('error')}")
            
            evidence_portfolio_service.add_to_communication_log(
                project_id=project_id,
                entry={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "bitacora_generated",
                    "from_agent": "SYSTEM",
                    "to_agent": "ARCHIVO",
                    "email_subject": f"Bitácora Final - Proyecto {project_id}",
                    "attachment_name": Path(bitacora_path).name,
                    "pcloud_link": pcloud_link
                }
            )
            
            return {
                "success": True,
                "bitacora_path": bitacora_path,
                "pcloud_link": pcloud_link,
                "communication_count": len(communications)
            }
            
        except Exception as e:
            logger.error(f"Error generating bitácora for {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _summarize_compliance(self, deliberations: List[Dict]) -> Dict:
        """Summarize compliance across all deliberations"""
        pillars = {
            "razon_de_negocios": {"status": "not_evaluated", "mentions": 0},
            "beneficio_economico": {"status": "not_evaluated", "mentions": 0},
            "materialidad": {"status": "not_evaluated", "mentions": 0},
            "trazabilidad": {"status": "not_evaluated", "mentions": 0}
        }
        
        for delib in deliberations:
            agent_pillars = delib.get("compliance_pillars", {})
            for pillar_id, pillar_data in agent_pillars.items():
                if pillar_id in pillars:
                    if pillar_data.get("mentioned"):
                        pillars[pillar_id]["mentions"] += 1
                    if pillar_data.get("status") == "compliant":
                        pillars[pillar_id]["status"] = "compliant"
                    elif pillar_data.get("status") == "concern" and pillars[pillar_id]["status"] != "compliant":
                        pillars[pillar_id]["status"] = "concern"
        
        for pillar_id in pillars:
            if pillars[pillar_id]["mentions"] > 0 and pillars[pillar_id]["status"] == "not_evaluated":
                pillars[pillar_id]["status"] = "mentioned"
        
        return pillars


orchestrator = DeliberationOrchestrator()
