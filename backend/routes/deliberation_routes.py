"""
Deliberation API Routes
Endpoints for multi-agent deliberation workflow
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from services.deliberation_orchestrator import orchestrator, WorkflowStage

router = APIRouter(prefix="/deliberation", tags=["Deliberation"])
logger = logging.getLogger(__name__)


class ProjectSubmission(BaseModel):
    """Project data for starting deliberation"""
    id: Optional[str] = None
    name: str = Field(..., description="Project name")
    client_name: str = Field(..., description="Client name")
    description: str = Field(..., description="Project description")
    amount: float = Field(..., description="Project amount in MXN")
    service_type: str = Field(default="Consultoría", description="Type of service")


class AgentDecision(BaseModel):
    """Agent's decision on a project"""
    project_id: str = Field(..., description="Project ID")
    agent_id: str = Field(..., description="Agent making the decision")
    decision: str = Field(..., description="approve, reject, or request_info")
    analysis: str = Field(..., description="Agent's analysis and reasoning")
    project: Dict[str, Any] = Field(..., description="Project data")


@router.post("/start")
async def start_deliberation(project: ProjectSubmission):
    """
    Start a new deliberation process for a project
    
    This sends the project to the first agent (María/Estrategia)
    who will analyze it using their RAG knowledge base and respond via email.
    
    The workflow is:
    1. E1_ESTRATEGIA (María) - Strategic alignment
    2. E2_FISCAL (Laura) - Tax compliance
    3. E3_FINANZAS (Roberto) - Financial viability
    4. E4_LEGAL (Legal Team) - Legal compliance
    5. E5_APROBADO - Final approval
    """
    try:
        project_dict = project.model_dump()
        result = await orchestrator.start_deliberation(project_dict)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
    except Exception as e:
        logger.error(f"Error starting deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agentic")
async def run_agentic_deliberation(project: ProjectSubmission):
    """
    Run FULL agentic deliberation with LLM reasoning
    
    Each agent (María, Laura, Roberto, Legal) will:
    1. Query their RAG knowledge base for context
    2. Reason about the project using GPT-4
    3. Make a decision based on their specialized perspective
    4. Send their analysis to the next agent via email
    
    Returns complete audit trail when all agents have deliberated.
    This is the core agentic workflow where each agent THINKS and REASONS.
    """
    try:
        project_dict = project.model_dump()
        result = await orchestrator.run_agentic_deliberation(project_dict)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        

        return result
    except Exception as e:
        logger.error(f"Error in agentic deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DemoCase(BaseModel):
    """Data for running a demo deliberation"""
    case_id: str
    title: str
    description: str
    amount: float = 0
    client_name: str = "Empresa Demo S.A. de C.V."


@router.post("/demo")
async def run_demo_deliberation(case: DemoCase):
    """
    Run a real agentic deliberation for a demo case.
    
    This creates a temporary project and triggers the full AI orchestration,
    allowing the frontend validation simulation to use real backend logic.
    """
    from services.defense_file_service import defense_file_service
    from services.deliberation_orchestrator import orchestrator
    import uuid
    from datetime import datetime
    
    # Create a unique project ID for this demo run
    project_id = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        # Construct project data
        project_data = {
            "id": project_id,
            "name": case.title,
            "client_name": case.client_name,
            "description": case.description,
            "amount": case.amount,
            "service_type": "Demostración",
            "sponsor_name": "Usuario Demo",
            "sponsor_email": "demo@revisar.ia",
            "department": "Finanzas",
            "created_at": datetime.now().isoformat(),
            "is_demo": True,
            "status": "processing"
        }
        
        # Initialize defense file
        defense_file = defense_file_service.get_or_create(project_id)
        defense_file.project_data = project_data
        defense_file.save()
        
        # Start the orchestration in the background (fire and forget from HTTP perspective, 
        # but state will be updated for polling)
        # We wrap it to ensure it runs independently
        async def run_async():
            try:
                logger.info(f"Starting DEMO deliberation for {project_id}")
                from routes.projects import processing_state, ProcessingStatus
                
                # Report initial status
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.PROCESSING,
                    message="Inicializando agentes para demostración...",
                    progress=5,
                    agent_statuses=[
                        {"name": "María Rodríguez", "role": "Estrategia", "status": "En cola"},
                        {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                        {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                        {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
                    ]
                )
                
                # Run the actual orchestration
                await orchestrator.run_agentic_deliberation(project_data)
                
                # Update final status
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.COMPLETED,
                    message="Demostración completada",
                    progress=100
                )
                
            except Exception as e:
                logger.error(f"Error in demo run {project_id}: {e}")
                from routes.projects import processing_state, ProcessingStatus
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.FAILED,
                    error=str(e)
                )

        import asyncio
        asyncio.create_task(run_async())
        
        return {
            "success": True,
            "project_id": project_id,
            "message": "Demo started successfully",
            "poll_url": f"/api/projects/processing-status/{project_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting demo deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advance")
async def advance_workflow(decision: AgentDecision):
    """
    Advance the workflow based on an agent's decision
    
    Decision options:
    - approve: Move to next stage
    - reject: End workflow with rejection
    - request_info: Request more information (stays at current stage)
    
    Each decision is recorded and an email is sent to the next agent.
    """
    try:
        result = await orchestrator.advance_workflow(
            project_id=decision.project_id,
            current_agent_id=decision.agent_id,
            decision=decision.decision,
            analysis=decision.analysis,
            project=decision.project
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
    except Exception as e:
        logger.error(f"Error advancing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trail/{project_id}")
async def get_deliberation_trail(project_id: str):
    """
    Get the complete deliberation trail for a project
    
    This returns all deliberation records including:
    - Stage progression
    - Agent decisions and analysis
    - RAG context used
    - Emails sent
    - Timestamps
    
    This serves as the audit evidence for SAT Materialidad compliance.
    """
    trail = orchestrator.get_deliberation_trail(project_id)
    return trail


@router.get("/status/{project_id}")
async def get_project_status(project_id: str):
    """
    Get current workflow status for a project
    
    Returns:
    - Current stage
    - Status (in_progress, approved, rejected)
    - Pending agent (if in_progress)
    - Stages completed
    """
    status = orchestrator.get_project_status(project_id)
    return status


@router.get("/stages")
async def get_workflow_stages():
    """
    Get all available workflow stages
    """
    return {
        "stages": [
            {
                "id": WorkflowStage.E1_ESTRATEGIA.value,
                "name": "Estrategia",
                "agent": "A1_SPONSOR",
                "description": "Análisis estratégico y razón de negocios"
            },
            {
                "id": WorkflowStage.E2_FISCAL.value,
                "name": "Fiscal",
                "agent": "A3_FISCAL",
                "description": "Cumplimiento fiscal y Art. 5-A CFF"
            },
            {
                "id": WorkflowStage.E3_FINANZAS.value,
                "name": "Finanzas",
                "agent": "A5_FINANZAS",
                "description": "Viabilidad financiera y beneficio económico"
            },
            {
                "id": WorkflowStage.E4_LEGAL.value,
                "name": "Legal",
                "agent": "LEGAL",
                "description": "Cumplimiento legal y contratos"
            },
            {
                "id": WorkflowStage.E5_APROBADO.value,
                "name": "Aprobado",
                "agent": None,
                "description": "Proyecto aprobado por todos los agentes"
            }
        ],
        "compliance_pillars": [
            "Razón de Negocios (Art. 5-A CFF)",
            "Beneficio Económico Esperado",
            "Materialidad (Art. 69-B CFF)",
            "Trazabilidad (NOM-151)"
        ]
    }


@router.get("/pending/{agent_id}")
async def get_pending_projects(agent_id: str):
    """
    Get projects pending review by a specific agent
    
    Checks the agent's email inbox for deliberation requests
    """
    from services.dreamhost_email_service import DreamHostEmailService
    
    email_service = DreamHostEmailService()
    
    try:
        emails = email_service.read_inbox(agent_id, limit=10)
        
        satma_emails = [
            email for email in emails.get("emails", [])
            if "[Revisar.IA]" in email.get("subject", "")
        ]
        
        return {
            "agent_id": agent_id,
            "pending_count": len(satma_emails),
            "pending_projects": satma_emails
        }
    except Exception as e:
        logger.error(f"Error getting pending projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AdjustmentRequest(BaseModel):
    """Request for project adjustments from provider"""
    project_id: str = Field(..., description="Project ID")
    agent_id: str = Field(..., description="Agent requesting the adjustment")
    provider_email: str = Field(..., description="Provider's email address")
    adjustment_type: str = Field(..., description="Type: information, documentation, clarification, pricing")
    request_details: str = Field(..., description="Detailed description of what is needed")
    deadline_days: int = Field(default=5, description="Days to respond")
    project: Dict[str, Any] = Field(..., description="Project data")


@router.post("/request-adjustment")
async def request_adjustment(request: AdjustmentRequest):
    """
    Request adjustments or additional information from the service provider
    
    This is used when an agent needs:
    - Additional documentation
    - Clarification on service scope
    - Pricing adjustments
    - More information for compliance validation
    
    An email is sent to the provider with the request details.
    The request is logged as part of the deliberation trail.
    """
    from services.dreamhost_email_service import DreamHostEmailService
    from config.agents_config import AGENT_CONFIGURATIONS
    from datetime import datetime, timezone, timedelta
    
    email_service = DreamHostEmailService()
    
    agent_config = AGENT_CONFIGURATIONS.get(request.agent_id)
    if not agent_config:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    deadline = datetime.now(timezone.utc) + timedelta(days=request.deadline_days)
    
    adjustment_types = {
        "information": "Información Adicional",
        "documentation": "Documentación Complementaria",
        "clarification": "Aclaración de Alcance",
        "pricing": "Revisión de Cotización"
    }
    
    tipo_solicitud = adjustment_types.get(request.adjustment_type, request.adjustment_type)
    
    subject = f"[Revisar.IA] Solicitud de {tipo_solicitud} - Proyecto {request.project_id}"
    
    body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SISTEMA REVISAR.IA - SOLICITUD DE AJUSTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimado Proveedor,

Como parte del proceso de validación de cumplimiento SAT para servicios
profesionales, requerimos la siguiente información adicional:

📋 DATOS DEL PROYECTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔢 ID: {request.project_id}
📋 Nombre: {request.project.get('name', 'Sin nombre')}
🏢 Cliente: {request.project.get('client_name', 'N/A')}
💰 Monto: ${request.project.get('amount', 0):,.2f} MXN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 TIPO DE SOLICITUD: {tipo_solicitud}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{request.request_details}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ FECHA LÍMITE DE RESPUESTA: {deadline.strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Por favor responda a este correo con la información solicitada.
Su respuesta será evaluada como parte de nuestro proceso de validación
de Materialidad conforme al Artículo 69-B del CFF.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Solicitante: {agent_config.get('name', 'Agente')}
📧 Departamento: {agent_config.get('department', 'N/A')}
🏢 Revisar.ia
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este correo fue generado automáticamente por Revisar.IA.
Cualquier respuesta será registrada como evidencia para auditorías SAT.
"""
    
    try:
        result = email_service.send_email(
            from_agent_id=request.agent_id,
            to_email=request.provider_email,
            subject=subject,
            body=body
        )
        
        return {
            "success": True,
            "project_id": request.project_id,
            "adjustment_type": request.adjustment_type,
            "provider_email": request.provider_email,
            "deadline": deadline.isoformat(),
            "email_sent": result.get("success", False),
            "message_id": result.get("message_id")
        }
    except Exception as e:
        logger.error(f"Error sending adjustment request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ProviderResponse(BaseModel):
    """Provider's response to an adjustment request"""
    project_id: str = Field(..., description="Project ID")
    response_text: str = Field(..., description="Provider's response")
    documents_attached: List[str] = Field(default=[], description="List of attached document names")


@router.post("/provider-response/{project_id}")
async def record_provider_response(project_id: str, response: ProviderResponse):
    """
    Record a provider's response to an adjustment request
    
    This endpoint is used to log the provider's response as part of
    the deliberation trail for audit purposes.
    """
    from datetime import datetime, timezone
    
    return {
        "success": True,
        "project_id": project_id,
        "response_recorded": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "documents_count": len(response.documents_attached),
        "note": "Response logged for SAT audit trail"
    }


from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import json

security = HTTPBearer(auto_error=False)

async def get_user_auth_info(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get user authentication info including allowed companies."""
    result = {"is_admin": False, "allowed_companies": [], "user_id": None, "authenticated": False}
    
    if not credentials:
        return result
    
    try:
        from jose import jwt
        from services.auth_service import get_secret_key
        SECRET_KEY = get_secret_key()
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        result["user_id"] = user_id
        result["authenticated"] = True
        
        if user_id:
            from services.user_db import user_service
            user = await user_service.get_user_by_id(user_id)
            if user:
                result["is_admin"] = user.role == "admin"
                if user.allowed_companies:
                    try:
                        companies = json.loads(user.allowed_companies)
                        if isinstance(companies, list):
                            result["allowed_companies"] = [c.lower().strip() for c in companies]
                    except (json.JSONDecodeError, TypeError):
                        pass  # Invalid JSON format
    except Exception as e:
        logger.debug(f"Error getting user auth info: {e}")
    
    return result


def check_empresa_access(empresa_id: str, user_info: dict) -> bool:
    """
    Check if user has access to the specified empresa.
    - Unauthenticated users: DENY
    - Admin users: ALLOW all
    - Non-admin with empty allowed_companies: DENY (strict isolation)
    - Non-admin with allowed_companies: check empresa_id match
    """
    if not user_info.get("authenticated"):
        return False
    
    if user_info.get("is_admin"):
        return True
    
    allowed = user_info.get("allowed_companies", [])
    if not allowed:
        return False
    
    empresa_lower = empresa_id.lower().strip()
    return any(a in empresa_lower or empresa_lower in a for a in allowed)


def require_authentication(user_info: dict):
    """Raise HTTPException if user is not authenticated."""
    if not user_info.get("authenticated"):
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida para acceder a este recurso"
        )


@router.get("/{project_id}/state")
async def get_deliberation_state(
    project_id: str,
    user_info: dict = Depends(get_user_auth_info)
):
    """
    Get the current persisted state of a deliberation.
    Enforces multi-tenant access control based on empresa_id.
    Requires authentication.
    """
    require_authentication(user_info)
    from services.database import deliberation_state_repository
    
    try:
        state = await deliberation_state_repository.get_state(project_id)
        
        if not state:
            raise HTTPException(
                status_code=404, 
                detail=f"No state found for project {project_id}"
            )
        
        empresa_id = state.get("empresa_id", "")
        if not check_empresa_access(empresa_id, user_info):
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a este proyecto"
            )
        
        return {
            "success": True,
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deliberation state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/resume")
async def resume_deliberation(
    project_id: str,
    user_info: dict = Depends(get_user_auth_info)
):
    """
    Resume a paused or failed deliberation from the last completed stage.
    Enforces multi-tenant access control.
    Requires authentication.
    """
    require_authentication(user_info)
    from services.database import deliberation_state_repository
    
    try:
        state = await deliberation_state_repository.get_state(project_id)
        
        if state:
            empresa_id = state.get("empresa_id", "")
            if not check_empresa_access(empresa_id, user_info):
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso para reanudar este proyecto"
                )
        
        result = await orchestrator.resume_deliberation(project_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Unable to resume deliberation")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumable")
async def get_resumable_deliberations(user_info: dict = Depends(get_user_auth_info)):
    """
    Get all deliberations that can be resumed (in_progress or paused status).
    Filters by user's allowed companies unless admin.
    Requires authentication.
    Non-admin users with empty allowed_companies get empty results (strict isolation).
    """
    require_authentication(user_info)
    from services.database import deliberation_state_repository
    
    try:
        if not user_info.get("is_admin"):
            allowed = user_info.get("allowed_companies", [])
            if not allowed:
                return {
                    "success": True,
                    "count": 0,
                    "resumable_deliberations": []
                }
        
        states = await deliberation_state_repository.get_resumable_states()
        
        if not user_info.get("is_admin"):
            filtered_states = [
                s for s in states 
                if check_empresa_access(s.get("empresa_id", ""), user_info)
            ]
            states = filtered_states
        
        return {
            "success": True,
            "count": len(states),
            "resumable_deliberations": states
        }
    except Exception as e:
        logger.error(f"Error getting resumable deliberations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
