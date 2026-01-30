"""
Agent Communication Routes - API endpoints for inter-agent email communication
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agent_comms_service import (
    agent_comms,
    AgentType,
    RequestType,
    RequestStatus,
    AGENT_EMAILS,
    LEGAL_WEB_SOURCES
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-comms", tags=["Agent Communications"])


# Request/Response Models
class LegalOpinionRequest(BaseModel):
    project_id: str = Field(..., description="ID del proyecto")
    project_name: str = Field(..., description="Nombre del proyecto")
    document_type: str = Field(..., description="Tipo de documento (contrato, factura, etc.)")
    questions: List[str] = Field(..., description="Preguntas especificas para el agente legal")
    context: Optional[str] = Field(None, description="Contexto adicional")
    iteration: int = Field(1, description="Numero de iteracion (1 = primera vez)")
    previous_feedback: Optional[str] = Field(None, description="Feedback de iteracion anterior")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "PROJ-2026-001",
                "project_name": "Consultoria Estrategica XYZ",
                "document_type": "Contrato de servicios profesionales",
                "questions": [
                    "Cumple con requisitos de deducibilidad Art. 27 LISR?",
                    "La descripcion del servicio es suficientemente especifica?",
                    "Incluye todos los elementos de materialidad?"
                ],
                "context": "Contrato por $500,000 MXN para consultoria de 3 meses",
                "iteration": 1
            }
        }


class LegalResponseRequest(BaseModel):
    project_id: str
    project_name: str
    status: RequestStatus
    opinion: str = Field(..., description="Opinion detallada del agente legal")
    articles_cited: List[str] = Field(..., description="Articulos de ley citados")
    required_changes: Optional[List[str]] = Field(None, description="Cambios requeridos si aplica")
    iteration: int = Field(1)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "PROJ-2026-001",
                "project_name": "Consultoria Estrategica XYZ",
                "status": "requiere_cambios",
                "opinion": "El contrato no cumple completamente con los requisitos de materialidad...",
                "articles_cited": ["Art. 27 LISR", "Art. 5-A CFF", "Art. 29 LISR"],
                "required_changes": [
                    "Agregar clausula de entregables especificos",
                    "Especificar fechas de inicio y fin del servicio",
                    "Incluir descripcion detallada del alcance"
                ],
                "iteration": 1
            }
        }


class ChangeRequestToProvider(BaseModel):
    project_id: str
    project_name: str
    provider_email: str = Field(..., description="Email del proveedor")
    changes_required: List[str] = Field(..., description="Lista de cambios requeridos")
    deadline: Optional[str] = Field(None, description="Fecha limite para cambios")
    iteration: int = Field(1)


# Endpoints
@router.get("/config")
async def get_agent_config():
    """Get current agent email configuration and available sources"""
    return {
        "agents": {agent.value: email for agent, email in AGENT_EMAILS.items()},
        "legal_sources": LEGAL_WEB_SOURCES,
        "request_types": [rt.value for rt in RequestType],
        "status_options": [rs.value for rs in RequestStatus]
    }


@router.post("/pmo-to-legal")
async def pmo_request_legal_opinion(request: LegalOpinionRequest):
    """
    PMO (A2) requests legal opinion from Legal (A4).
    Sends email to legal@satma.mx with specific questions.
    """
    try:
        result = await agent_comms.send_legal_opinion_request(
            project_id=request.project_id,
            project_name=request.project_name,
            document_type=request.document_type,
            specific_questions=request.questions,
            context=request.context,
            iteration=request.iteration,
            previous_feedback=request.previous_feedback
        )

        return {
            "success": result.get("success", False),
            "message": "Solicitud enviada a Agente Legal" if result.get("success") else "Error enviando solicitud",
            "details": result
        }

    except Exception as e:
        logger.error(f"Error in pmo_request_legal_opinion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/legal-to-pmo")
async def legal_respond_to_pmo(request: LegalResponseRequest):
    """
    Legal (A4) responds to PMO (A2) with opinion/dictamen.
    """
    try:
        result = await agent_comms.send_legal_response(
            project_id=request.project_id,
            project_name=request.project_name,
            status=request.status,
            opinion=request.opinion,
            articles_cited=request.articles_cited,
            required_changes=request.required_changes,
            iteration=request.iteration
        )

        return {
            "success": result.get("success", False),
            "message": f"Dictamen enviado con estatus: {request.status.value}",
            "details": result
        }

    except Exception as e:
        logger.error(f"Error in legal_respond_to_pmo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pmo-to-provider")
async def pmo_request_changes_from_provider(request: ChangeRequestToProvider):
    """
    PMO (A2) sends change request to external provider.
    """
    try:
        from services.email_service import email_service

        changes_html = "\n".join([f"<li>{c}</li>" for c in request.changes_required])

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #1e3a5f; }}
                .changes {{ background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Solicitud de Cambios - {request.project_name}</h1>
                <p>Estimado proveedor,</p>
                <p>Se requieren los siguientes ajustes en el entregable del proyecto <strong>{request.project_id}</strong>:</p>

                <div class="changes">
                    <h3>Cambios Requeridos (Iteracion #{request.iteration}):</h3>
                    <ol>
                        {changes_html}
                    </ol>
                </div>

                {f'<p><strong>Fecha limite:</strong> {request.deadline}</p>' if request.deadline else ''}

                <p>Por favor enviar el documento actualizado respondiendo a este correo.</p>

                <div class="footer">
                    <p>Este mensaje fue generado por Revisar.IA - Sistema de Auditoria Fiscal</p>
                </div>
            </div>
        </body>
        </html>
        """

        result = await email_service.send_email(
            to=request.provider_email,
            subject=f"[CAMBIOS REQUERIDOS] {request.project_name} - Iter #{request.iteration}",
            body_html=body_html
        )

        return {
            "success": result.get("success", False),
            "message": "Solicitud de cambios enviada al proveedor",
            "details": result
        }

    except Exception as e:
        logger.error(f"Error in pmo_request_changes_from_provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow-status/{project_id}")
async def get_workflow_status(project_id: str):
    """
    Get the current status of the review workflow for a project.
    """
    status = agent_comms.get_workflow_status(project_id)
    return {
        "project_id": project_id,
        **status
    }


@router.get("/communications/{project_id}")
async def get_project_communications(project_id: str):
    """
    Get all communications for a project.
    Returns the conversation thread between agents for frontend display.
    """
    communications = agent_comms.get_project_communications(project_id)
    return {
        "project_id": project_id,
        "count": len(communications),
        "communications": communications
    }


@router.get("/active-workflows")
async def get_active_workflows():
    """
    Get all active workflows across all projects.
    Useful for a dashboard showing agents at work.
    """
    workflows = agent_comms.get_all_active_workflows()
    return {
        "count": len(workflows),
        "workflows": workflows
    }


@router.post("/communications/{project_id}/{comm_id}/read")
async def mark_communication_read(project_id: str, comm_id: str):
    """
    Mark a communication as read.
    """
    success = agent_comms.mark_communication_read(project_id, comm_id)
    return {
        "success": success,
        "message": "Comunicacion marcada como leida" if success else "Comunicacion no encontrada"
    }


class SimulatedAgentResponse(BaseModel):
    """For simulating agent responses in demo mode"""
    project_id: str
    responding_agent: str = Field(..., description="A2, A4, etc")
    response_content: str
    status: RequestStatus = RequestStatus.REQUIERE_CAMBIOS
    iteration: int = 1


@router.post("/simulate-response")
async def simulate_agent_response(request: SimulatedAgentResponse):
    """
    Simulate an agent response (for demo/testing purposes).
    In production, responses would come from actual email webhooks.
    """
    try:
        # Determine from/to agents based on responding_agent
        agent_map = {
            "A2": AgentType.PMO,
            "A4": AgentType.LEGAL,
            "A3": AgentType.FISCAL,
            "A6": AgentType.PROVEEDOR,
        }

        responding = agent_map.get(request.responding_agent)
        if not responding:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.responding_agent}")

        # Determine recipient (usually who sent the last message)
        comms = agent_comms.get_project_communications(request.project_id)
        if comms:
            last_comm = comms[-1]
            # Response goes back to whoever sent the last message
            to_agent = agent_map.get(last_comm["from_agent"])
        else:
            # Default to PMO if no previous comms
            to_agent = AgentType.PMO

        # Store the simulated response
        stored = agent_comms._store_communication(
            project_id=request.project_id,
            from_agent=responding,
            to_agent=to_agent,
            message_type="respuesta",
            subject=f"Re: [{request.project_id}] Respuesta de {agent_comms.get_agent_name(responding)}",
            content=request.response_content,
            status=request.status,
            iteration=request.iteration
        )

        return {
            "success": True,
            "message": f"Respuesta simulada de {responding.value}",
            "communication": stored
        }

    except Exception as e:
        logger.error(f"Error in simulate_agent_response: {e}")
        raise HTTPException(status_code=500, detail=str(e))
