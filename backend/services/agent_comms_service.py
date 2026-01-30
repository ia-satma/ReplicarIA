"""
Agent Communication Service - Email-based inter-agent communication
Handles requests and responses between PMO, Legal, and other agents via email.
Stores communication history for frontend visualization.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import email_service with fallback
try:
    from services.email_service import email_service
except ImportError as e:
    logger.warning(f"Email service not available: {e}")
    email_service = None

# In-memory storage for communication history (per project)
# In production, this would be in MongoDB
_communication_history: Dict[str, List[Dict]] = defaultdict(list)
_active_workflows: Dict[str, Dict] = {}  # Track active workflow status


class AgentType(str, Enum):
    ESTRATEGIA = "A1"
    PMO = "A2"
    FISCAL = "A3"
    LEGAL = "A4"
    FINANZAS = "A5"
    PROVEEDOR = "A6"
    DEFENSA = "A7"


# Agent email addresses
AGENT_EMAILS = {
    AgentType.ESTRATEGIA: os.environ.get("AGENT_A1_EMAIL", "estrategia@satma.mx"),
    AgentType.PMO: os.environ.get("AGENT_A2_EMAIL", "pmo@satma.mx"),
    AgentType.FISCAL: os.environ.get("AGENT_A3_EMAIL", "fiscal@satma.mx"),
    AgentType.LEGAL: os.environ.get("AGENT_A4_EMAIL", "legal@satma.mx"),
    AgentType.FINANZAS: os.environ.get("AGENT_A5_EMAIL", "finanzas@satma.mx"),
    AgentType.PROVEEDOR: os.environ.get("AGENT_A6_EMAIL", "proveedor@satma.mx"),
    AgentType.DEFENSA: os.environ.get("AGENT_A7_EMAIL", "defensa@satma.mx"),
}

AGENT_NAMES = {
    AgentType.ESTRATEGIA: "Agente de Estrategia",
    AgentType.PMO: "Agente PMO (Orquestador)",
    AgentType.FISCAL: "Agente Fiscal",
    AgentType.LEGAL: "Agente Legal",
    AgentType.FINANZAS: "Agente de Finanzas",
    AgentType.PROVEEDOR: "Agente de Proveedores",
    AgentType.DEFENSA: "Agente de Defensa",
}

# Legal agent web sources
LEGAL_WEB_SOURCES = {
    "CFF": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
    "LISR": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf",
    "LIVA": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf",
    "RMF": "https://www.sat.gob.mx/normatividad",
    "DOF": "https://www.dof.gob.mx/",
    "69B": "https://www.sat.gob.mx/consultas/76674/consulta-la-relacion-de-contribuyentes-incumplidos",
    "32D": "https://www.sat.gob.mx/aplicacion/operacion/66288/genera-tu-constancia-de-situacion-fiscal",
}


class RequestType(str, Enum):
    OPINION_LEGAL = "opinion_legal"
    REVISION_CONTRATO = "revision_contrato"
    VALIDACION_FISCAL = "validacion_fiscal"
    SOLICITUD_CAMBIOS = "solicitud_cambios"
    APROBACION = "aprobacion"


class RequestStatus(str, Enum):
    PENDIENTE = "pendiente"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    REQUIERE_CAMBIOS = "requiere_cambios"


class AgentCommsService:
    """Service for agent-to-agent email communication with history tracking"""

    def __init__(self):
        self.email_service = email_service
        self.history = _communication_history
        self.workflows = _active_workflows
        if email_service:
            logger.info("Agent Communications Service initialized with email support")
        else:
            logger.warning("Agent Communications Service initialized WITHOUT email support (demo mode)")

    def _store_communication(
        self,
        project_id: str,
        from_agent: AgentType,
        to_agent: AgentType,
        message_type: str,
        subject: str,
        content: str,
        status: RequestStatus = RequestStatus.PENDIENTE,
        iteration: int = 1,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Store a communication in history for frontend display"""
        comm = {
            "id": f"{project_id}-{len(self.history[project_id]) + 1}",
            "timestamp": datetime.utcnow().isoformat(),
            "from_agent": from_agent.value,
            "from_name": self.get_agent_name(from_agent),
            "from_email": self.get_agent_email(from_agent),
            "to_agent": to_agent.value,
            "to_name": self.get_agent_name(to_agent),
            "to_email": self.get_agent_email(to_agent),
            "message_type": message_type,
            "subject": subject,
            "content": content,
            "status": status.value,
            "iteration": iteration,
            "metadata": metadata or {},
            "read": False
        }
        self.history[project_id].append(comm)

        # Update workflow status
        if project_id not in self.workflows:
            self.workflows[project_id] = {
                "status": "iniciado",
                "current_stage": "pmo_to_legal",
                "iteration": iteration,
                "started_at": datetime.utcnow().isoformat()
            }

        return comm

    def get_project_communications(self, project_id: str) -> List[Dict]:
        """Get all communications for a project (for frontend display)"""
        return self.history.get(project_id, [])

    def get_workflow_status(self, project_id: str) -> Dict:
        """Get current workflow status for a project"""
        return self.workflows.get(project_id, {
            "status": "no_iniciado",
            "current_stage": None,
            "iteration": 0
        })

    def get_all_active_workflows(self) -> Dict[str, Dict]:
        """Get all active workflows"""
        return dict(self.workflows)

    def mark_communication_read(self, project_id: str, comm_id: str) -> bool:
        """Mark a communication as read"""
        for comm in self.history.get(project_id, []):
            if comm["id"] == comm_id:
                comm["read"] = True
                return True
        return False

    def get_agent_email(self, agent: AgentType) -> str:
        return AGENT_EMAILS.get(agent, "sistema@satma.mx")

    def get_agent_name(self, agent: AgentType) -> str:
        return AGENT_NAMES.get(agent, "Agente")

    async def send_request(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        request_type: RequestType,
        project_id: str,
        project_name: str,
        request_content: str,
        attachments: Optional[List[str]] = None,
        iteration: int = 1,
        previous_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a request from one agent to another via email.
        """
        to_email = self.get_agent_email(to_agent)
        from_name = self.get_agent_name(from_agent)
        to_name = self.get_agent_name(to_agent)

        # Build subject with tracking info
        subject = f"[{from_agent.value}->{to_agent.value}] [{project_id}] {request_type.value.replace('_', ' ').title()} - Iter {iteration}"

        # Build HTML body
        body_html = self._build_request_email(
            from_agent=from_agent,
            to_agent=to_agent,
            from_name=from_name,
            to_name=to_name,
            request_type=request_type,
            project_id=project_id,
            project_name=project_name,
            request_content=request_content,
            iteration=iteration,
            previous_feedback=previous_feedback
        )

        # Store in history BEFORE sending email (so frontend shows immediately)
        stored_comm = self._store_communication(
            project_id=project_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=request_type.value,
            subject=subject,
            content=request_content,
            status=RequestStatus.PENDIENTE,
            iteration=iteration,
            metadata={"previous_feedback": previous_feedback} if previous_feedback else None
        )

        # Send email (if email service is available)
        if self.email_service:
            result = await self.email_service.send_email(
                to=to_email,
                subject=subject,
                body_html=body_html,
                body_text=request_content
            )

            if result.get("success"):
                logger.info(f"Request sent: {from_agent.value} -> {to_agent.value} for project {project_id}")
            else:
                logger.error(f"Failed to send request: {result.get('error')}")
        else:
            # Demo mode - no email sent
            result = {"success": True, "demo_mode": True, "message": "Email not sent (demo mode)"}
            logger.info(f"Request stored (demo mode): {from_agent.value} -> {to_agent.value} for project {project_id}")

        return {
            **result,
            "from_agent": from_agent.value,
            "to_agent": to_agent.value,
            "request_type": request_type.value,
            "project_id": project_id,
            "iteration": iteration,
            "timestamp": datetime.utcnow().isoformat(),
            "communication_id": stored_comm["id"]
        }

    async def send_legal_opinion_request(
        self,
        project_id: str,
        project_name: str,
        document_type: str,
        specific_questions: List[str],
        context: Optional[str] = None,
        iteration: int = 1,
        previous_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        PMO requests legal opinion from Legal agent.
        """
        questions_html = "\n".join([f"<li>{q}</li>" for q in specific_questions])

        request_content = f"""
        SOLICITUD DE OPINION LEGAL

        Proyecto: {project_name} ({project_id})
        Tipo de documento: {document_type}
        Iteracion: {iteration}

        CONTEXTO:
        {context or 'No especificado'}

        PREGUNTAS ESPECIFICAS:
        {chr(10).join([f'- {q}' for q in specific_questions])}

        FUENTES DE REFERENCIA:
        - CFF: {LEGAL_WEB_SOURCES['CFF']}
        - LISR: {LEGAL_WEB_SOURCES['LISR']}
        - LIVA: {LEGAL_WEB_SOURCES['LIVA']}

        {f'FEEDBACK ANTERIOR: {previous_feedback}' if previous_feedback else ''}

        Por favor responder con dictamen detallado citando articulos especificos.
        """

        return await self.send_request(
            from_agent=AgentType.PMO,
            to_agent=AgentType.LEGAL,
            request_type=RequestType.OPINION_LEGAL,
            project_id=project_id,
            project_name=project_name,
            request_content=request_content,
            iteration=iteration,
            previous_feedback=previous_feedback
        )

    async def send_legal_response(
        self,
        project_id: str,
        project_name: str,
        status: RequestStatus,
        opinion: str,
        articles_cited: List[str],
        required_changes: Optional[List[str]] = None,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Legal agent responds to PMO with opinion.
        """
        status_emoji = {
            RequestStatus.APROBADO: "APROBADO",
            RequestStatus.RECHAZADO: "RECHAZADO",
            RequestStatus.REQUIERE_CAMBIOS: "REQUIERE CAMBIOS",
            RequestStatus.EN_REVISION: "EN REVISION"
        }

        changes_text = ""
        if required_changes:
            changes_text = "\n\nCAMBIOS REQUERIDOS:\n" + "\n".join([f"- {c}" for c in required_changes])

        response_content = f"""
        DICTAMEN LEGAL

        Proyecto: {project_name} ({project_id})
        Iteracion: {iteration}

        ESTATUS: {status_emoji.get(status, status.value)}

        OPINION:
        {opinion}

        ARTICULOS CITADOS:
        {chr(10).join([f'- {a}' for a in articles_cited])}
        {changes_text}

        FUENTES CONSULTADAS:
        - {LEGAL_WEB_SOURCES['CFF']}
        - {LEGAL_WEB_SOURCES['LISR']}
        """

        return await self.send_request(
            from_agent=AgentType.LEGAL,
            to_agent=AgentType.PMO,
            request_type=RequestType.APROBACION if status == RequestStatus.APROBADO else RequestType.SOLICITUD_CAMBIOS,
            project_id=project_id,
            project_name=project_name,
            request_content=response_content,
            iteration=iteration
        )

    def _build_request_email(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        from_name: str,
        to_name: str,
        request_type: RequestType,
        project_id: str,
        project_name: str,
        request_content: str,
        iteration: int,
        previous_feedback: Optional[str] = None
    ) -> str:
        """Build HTML email for agent request"""

        agent_colors = {
            AgentType.PMO: "#3b82f6",      # Blue
            AgentType.LEGAL: "#8b5cf6",    # Purple
            AgentType.FISCAL: "#f59e0b",   # Amber
            AgentType.PROVEEDOR: "#10b981", # Green
            AgentType.DEFENSA: "#ef4444",  # Red
        }

        from_color = agent_colors.get(from_agent, "#6366f1")
        to_color = agent_colors.get(to_agent, "#6366f1")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
                .container {{ max-width: 700px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, {from_color}, {to_color}); padding: 25px; border-radius: 12px 12px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 20px; }}
                .header .meta {{ color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 10px; }}
                .content {{ background: #1e293b; padding: 25px; border-radius: 0 0 12px 12px; }}
                .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
                .badge-from {{ background: {from_color}; color: white; }}
                .badge-to {{ background: {to_color}; color: white; }}
                .iteration {{ background: #334155; color: #94a3b8; padding: 4px 10px; border-radius: 4px; font-size: 12px; }}
                .section {{ background: #0f172a; padding: 20px; border-radius: 8px; margin: 15px 0; }}
                .section-title {{ color: #60a5fa; font-size: 14px; font-weight: 600; margin-bottom: 10px; text-transform: uppercase; }}
                pre {{ background: #020617; padding: 15px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; font-size: 14px; color: #cbd5e1; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                .sources {{ background: #1e3a5f; padding: 15px; border-radius: 8px; margin-top: 15px; }}
                .sources a {{ color: #60a5fa; text-decoration: none; }}
                .sources a:hover {{ text-decoration: underline; }}
                .previous {{ background: #7c2d12; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #f97316; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Comunicacion Inter-Agente</h1>
                    <div class="meta">
                        <span class="badge badge-from">{from_agent.value} {from_name}</span>
                        <span style="margin: 0 10px; color: white;">→</span>
                        <span class="badge badge-to">{to_agent.value} {to_name}</span>
                        <span class="iteration" style="margin-left: 15px;">Iteracion #{iteration}</span>
                    </div>
                </div>
                <div class="content">
                    <div class="section">
                        <div class="section-title">Proyecto</div>
                        <strong>{project_name}</strong><br>
                        <span style="color: #64748b; font-size: 13px;">ID: {project_id}</span>
                    </div>

                    <div class="section">
                        <div class="section-title">Tipo de Solicitud</div>
                        <span style="color: #f8fafc;">{request_type.value.replace('_', ' ').title()}</span>
                    </div>

                    <div class="section">
                        <div class="section-title">Contenido</div>
                        <pre>{request_content}</pre>
                    </div>

                    {f'''<div class="previous">
                        <div class="section-title" style="color: #fb923c;">Feedback Anterior</div>
                        <pre style="background: transparent; padding: 0;">{previous_feedback}</pre>
                    </div>''' if previous_feedback else ''}

                    <div class="sources">
                        <div class="section-title">Fuentes de Referencia</div>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><a href="{LEGAL_WEB_SOURCES['CFF']}">Codigo Fiscal de la Federacion (CFF)</a></li>
                            <li><a href="{LEGAL_WEB_SOURCES['LISR']}">Ley del ISR</a></li>
                            <li><a href="{LEGAL_WEB_SOURCES['LIVA']}">Ley del IVA</a></li>
                            <li><a href="{LEGAL_WEB_SOURCES['69B']}">Lista 69-B SAT</a></li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>Revisar.IA - Sistema Multi-Agente de Auditoria Fiscal</p>
                    <p>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
            </div>
        </body>
        </html>
        """


# Singleton instance
agent_comms = AgentCommsService()
