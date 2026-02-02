from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import uuid
import shutil
from pathlib import Path
import logging
import asyncio
from enum import Enum

from middleware.tenant_context import get_current_empresa_id, get_current_user_id
from services.auth_service import get_secret_key, get_current_user
from services.error_handler import handle_route_error, AppError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


class ProcessingStatus(str, Enum):
    """Status for async project processing"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingState:
    """In-memory state for tracking async project processing"""
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def set_status(
        self, 
        project_id: str, 
        status: ProcessingStatus,
        message: str = "",
        progress: int = 0,
        agent_statuses: Optional[List[Dict]] = None,
        error: Optional[str] = None
    ):
        async with self._lock:
            self._states[project_id] = {
                "project_id": project_id,
                "status": status.value,
                "message": message,
                "progress": progress,
                "agent_statuses": agent_statuses or [],
                "error": error,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._states.get(project_id)
    
    async def remove_status(self, project_id: str):
        async with self._lock:
            if project_id in self._states:
                del self._states[project_id]


processing_state = ProcessingState()

from services.auth_service import security

# Usar el servicio de autenticación centralizado
get_current_user_for_projects = get_current_user

ROOT_DIR = Path(__file__).parent.parent
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class ProjectSubmitRequest(BaseModel):
    project_name: str
    sponsor_name: str
    sponsor_email: str
    company_name: Optional[str] = ""
    department: str = ""
    description: str
    strategic_alignment: Optional[str] = ""
    expected_economic_benefit: float = 0
    budget_estimate: float
    duration_months: int = 12
    urgency_level: Optional[str] = "Normal"
    requires_human: Optional[str] = "No"
    attachments: List[str] = []
    is_modification: bool = False
    parent_folio: Optional[str] = ""
    modification_notes: Optional[str] = ""


class AdjustmentSubmitRequest(BaseModel):
    adjustment_notes: str
    updated_description: Optional[str] = None
    updated_budget: Optional[float] = None
    updated_benefit: Optional[float] = None
    attachments: List[str] = []


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Subir archivos adjuntos del formulario"""
    empresa_id = get_current_empresa_id()
    prefix = empresa_id if empresa_id else "temp"
    
    try:
        # Null check for filename
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        filename = file.filename.strip()
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")

        file_extension = Path(filename).suffix
        unique_filename = f"{prefix}_{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_url = f"/api/files/uploads/{unique_filename}"

        return {
            "success": True,
            "file_url": file_url,
            "filename": file.filename,
            "size": file_path.stat().st_size
        }
    except HTTPException:
        raise
    except IOError as e:
        logger.error(f"I/O error uploading file: {e}")
        raise HTTPException(status_code=507, detail="Insufficient storage space")
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Error uploading file")


@router.post("/submit")
async def submit_project(
    project_data: ProjectSubmitRequest,
    request: Request
):
    """
    Enviar un nuevo proyecto e iniciar deliberación agéntica automática.
    X-Empresa-ID header es opcional - puede inferirse del formulario.
    
    Returns immediately with project_id - processing happens asynchronously.
    Use /processing-status/{project_id} to poll for completion.
    """
    from services.defense_file_service import defense_file_service
    from services.deliberation_orchestrator import orchestrator
    from services.event_stream import event_emitter
    from jose import jwt, exceptions as jose_exceptions
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    user_id = get_current_user_id()
    
    # Fallback: extraer empresa_id directamente del token si no está en el contexto
    if not empresa_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                from services.auth_service import get_secret_key
                SECRET_KEY = get_secret_key()
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                empresa_id = payload.get("empresa_id")
                if not user_id:
                    user_id = payload.get("user_id")
            except jose_exceptions.JWTError:
                pass
    
    project_id = f"PROJ-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        data = project_data.model_dump()
        
        project_for_deliberation = {
            "id": project_id,
            "empresa_id": empresa_id,
            "created_by": user_id,
            "name": data["project_name"],
            "client_name": data["company_name"] or data["sponsor_name"],
            "description": data["description"],
            "amount": data["budget_estimate"],
            "service_type": data.get("strategic_alignment", "Consultoría"),
            "sponsor_name": data["sponsor_name"],
            "sponsor_email": data["sponsor_email"],
            "department": data["department"],
            "expected_benefit": data["expected_economic_benefit"],
            "duration_months": data["duration_months"],
            "urgency_level": data["urgency_level"],
            "requires_human": data["requires_human"],
            "attachments": data["attachments"],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "is_modification": data.get("is_modification", False),
            "parent_folio": data.get("parent_folio", ""),
            "modification_notes": data.get("modification_notes", "")
        }
        
        event_emitter.create_session(project_id)
        
        await processing_state.set_status(
            project_id=project_id,
            status=ProcessingStatus.INITIALIZING,
            message="Proyecto recibido, iniciando procesamiento...",
            progress=5,
            agent_statuses=[
                {"name": "María Rodríguez", "role": "Estrategia", "status": "Pendiente"},
                {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
            ]
        )
        
        try:
            defense_file = defense_file_service.get_or_create(project_id)
            defense_file.project_data = project_for_deliberation
            defense_file.empresa_id = empresa_id
            defense_file.save()
            logger.info(f"Defense file created for project {project_id}")
        except Exception as df_error:
            logger.warning(f"Could not pre-create defense file: {df_error}")
        
        async def run_deliberation_async():
            """Run deliberation in background without blocking the response"""
            try:
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.PROCESSING,
                    message="Agentes IA analizando el proyecto...",
                    progress=10,
                    agent_statuses=[
                        {"name": "María Rodríguez", "role": "Estrategia", "status": "En proceso"},
                        {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                        {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                        {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
                    ]
                )
                
                logger.info(f"Starting agentic deliberation for project {project_id} (empresa: {empresa_id})")
                result = await orchestrator.run_agentic_deliberation(project_for_deliberation)
                
                final_status = result.get('final_status', 'unknown')
                logger.info(f"Deliberation completed for {project_id}: {final_status}")
                
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.COMPLETED,
                    message=f"Análisis completado: {final_status}",
                    progress=100,
                    agent_statuses=[
                        {"name": "María Rodríguez", "role": "Estrategia", "status": "Completado"},
                        {"name": "Laura Sánchez", "role": "Fiscal", "status": "Completado"},
                        {"name": "Roberto Torres", "role": "Finanzas", "status": "Completado"},
                        {"name": "Equipo Legal", "role": "Legal", "status": "Completado"}
                    ]
                )
                
            except Exception as e:
                error_msg = str(e)[:200]
                logger.error(f"Error in deliberation for {project_id}: {error_msg}")
                await processing_state.set_status(
                    project_id=project_id,
                    status=ProcessingStatus.FAILED,
                    message="Error durante el procesamiento",
                    progress=0,
                    error=error_msg
                )
        
        asyncio.create_task(run_deliberation_async())
        
        return {
            "success": True,
            "message": "¡Proyecto recibido! Los agentes IA están analizando con inteligencia artificial.",
            "project_id": project_id,
            "empresa_id": empresa_id,
            "processing": True,
            "poll_url": f"/api/projects/processing-status/{project_id}",
            "project_data": {
                "project_name": data["project_name"],
                "sponsor_name": data["sponsor_name"],
                "budget": data["budget_estimate"],
                "expected_benefit": data["expected_economic_benefit"]
            },
            "agentic_workflow": {
                "status": "INICIADO",
                "agents": [
                    {"name": "María Rodríguez", "role": "Estrategia", "status": "En cola"},
                    {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                    {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                    {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
                ],
                "model": "Claude",
                "estimated_time": "30-60 segundos"
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error submitting project: {str(e)}")
        await processing_state.set_status(
            project_id=project_id,
            status=ProcessingStatus.FAILED,
            message="Datos del proyecto inválidos",
            error=str(e)[:200]
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting project: {str(e)}")
        await processing_state.set_status(
            project_id=project_id,
            status=ProcessingStatus.FAILED,
            message="Error al crear el proyecto",
            error=str(e)[:200]
        )
        raise HTTPException(status_code=503, detail="Error processing project. Try again later.")


@router.get("/processing-status/{project_id}")
async def get_processing_status(project_id: str):
    """
    Poll for async processing status of a project.
    Frontend can use this to track the progress of project creation/analysis.
    """
    from services.defense_file_service import defense_file_service
    
    status = await processing_state.get_status(project_id)
    
    if status:
        if status["status"] == ProcessingStatus.COMPLETED.value:
            defense_file = defense_file_service.get_defense_file(project_id)
            if defense_file:
                status["defense_file_ready"] = True
                status["final_decision"] = defense_file.get("final_decision")
                status["deliberation_count"] = len(defense_file.get("deliberations", []))
        
        return {
            "success": True,
            "data": status
        }
    
    defense_file = defense_file_service.get_defense_file(project_id)
    if defense_file:
        deliberations = defense_file.get("deliberations", [])
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "status": ProcessingStatus.COMPLETED.value,
                "message": "Proyecto ya procesado",
                "progress": 100,
                "defense_file_ready": True,
                "final_decision": defense_file.get("final_decision"),
                "deliberation_count": len(deliberations)
            }
        }
    
    return {
        "success": False,
        "data": {
            "project_id": project_id,
            "status": "not_found",
            "message": "Proyecto no encontrado o aún no iniciado"
        }
    }


@router.get("/folios")
async def list_project_folios(request: Request):
    """List all projects with their folios for modification dropdown - filtered by empresa"""
    from services.defense_file_service import defense_file_service
    from services.durezza_database import durezza_db
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        return {"success": True, "folios": [], "message": "Selecciona una empresa para ver proyectos"}
    
    try:
        folios = []
        seen_ids = set()
        
        defense_files = defense_file_service.list_all()
        
        for df in defense_files:
            project_id = df.get("project_id")
            project_data = df.get("project_data", {})
            
            df_empresa = project_data.get("empresa_id") or df.get("empresa_id")
            if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
                continue
            
            if project_id and project_id not in seen_ids:
                seen_ids.add(project_id)
                folios.append({
                    "folio": project_id,
                    "project_name": project_data.get("name", project_data.get("project_name", "Sin nombre")),
                    "company_name": project_data.get("client_name", project_data.get("company_name", "N/A")),
                    "sponsor_name": project_data.get("sponsor_name", ""),
                    "sponsor_email": project_data.get("sponsor_email", ""),
                    "amount": project_data.get("amount", project_data.get("budget_estimate", 0)),
                    "description": project_data.get("description", ""),
                    "status": "approved" if df.get("final_decision") == "approve" else "in_review",
                    "created_at": df.get("created_at"),
                    "deliberation_count": df.get("deliberation_count", 0)
                })
        
        try:
            durezza_projects = await durezza_db.get_projects(empresa_id=empresa_id, limit=500)
            for proj in durezza_projects:
                project_id = proj.get("id")
                if project_id and project_id not in seen_ids:
                    seen_ids.add(project_id)
                    folios.append({
                        "folio": project_id,
                        "project_name": proj.get("nombre", proj.get("project_name", "Sin nombre")),
                        "company_name": proj.get("empresa", proj.get("company_name", "N/A")),
                        "sponsor_name": proj.get("sponsor_name", ""),
                        "sponsor_email": proj.get("sponsor_email", ""),
                        "amount": proj.get("monto_contrato", proj.get("budget_estimate", 0)),
                        "description": proj.get("descripcion", proj.get("description", "")),
                        "status": proj.get("estado_global", "in_review"),
                        "created_at": proj.get("created_at"),
                        "deliberation_count": 0
                    })
        except Exception as db_error:
            logger.warning(f"Could not fetch from durezza_db: {db_error}")
        
        def get_sort_key(x):
            created = x.get("created_at")
            if created is None:
                return ""
            if hasattr(created, 'isoformat'):
                return created.isoformat()
            return str(created)
        
        folios.sort(key=get_sort_key, reverse=True)
        
        return {
            "success": True,
            "count": len(folios),
            "empresa_id": empresa_id,
            "folios": folios
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing project folios: {str(e)}")
        # 503 for database issues
        raise HTTPException(status_code=503, detail="Unable to retrieve projects. Service temporarily unavailable.")


@router.get("")
async def list_projects():
    """Listar todos los proyectos con deliberaciones - filtrado por empresa (admins ven todo)"""
    from services.defense_file_service import defense_file_service
    from middleware.tenant_context import get_current_tenant
    
    empresa_id = get_current_empresa_id()
    context = get_current_tenant()
    is_admin = context.is_admin if context else False
    
    if not empresa_id and not is_admin:
        raise HTTPException(status_code=400, detail="X-Empresa-ID requerido")
    
    try:
        defense_files = defense_file_service.list_all()
        
        projects = []
        
        for df in defense_files:
            full_df = defense_file_service.get_defense_file(df["project_id"])
            if full_df:
                project_data = full_df.get("project_data", {})
                
                df_empresa = project_data.get("empresa_id") or full_df.get("empresa_id")
                
                if not is_admin:
                    if df_empresa and empresa_id and df_empresa.lower().strip() != empresa_id.lower().strip():
                        continue
                
                projects.append({
                    "id": df.get("project_id"),
                    "name": project_data.get("name", "Sin nombre"),
                    "client_name": project_data.get("client_name", "N/A"),
                    "amount": project_data.get("amount", 0),
                    "status": "approved" if df.get("final_decision") == "approve" else "in_review",
                    "deliberation_count": full_df.get("deliberation_count", 0),
                    "created_at": df.get("created_at"),
                    "compliance_score": df.get("compliance_score", 0),
                    "empresa_id": df_empresa
                })
        
        return {
            "success": True,
            "count": len(projects),
            "empresa_id": empresa_id or "admin-all",
            "is_admin": is_admin,
            "projects": projects
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        # 503 for service/database issues
        raise HTTPException(status_code=503, detail="Unable to retrieve projects. Service temporarily unavailable.")


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Obtener detalles de un proyecto con su Defense File y historial de versiones"""
    from services.defense_file_service import defense_file_service
    from services.project_serializer import flatten_project_for_frontend
    
    empresa_id = get_current_empresa_id()
    if not empresa_id:
        raise HTTPException(status_code=400, detail="X-Empresa-ID requerido")
    
    try:
        # Null check for project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID is required")

        defense_file = defense_file_service.get_defense_file(project_id)

        if not defense_file:
            raise HTTPException(status_code=404, detail=f"Proyecto {project_id} no encontrado")
        
        project_data = defense_file.get("project_data", {})
        df_empresa = project_data.get("empresa_id") or defense_file.get("empresa_id")
        if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
            raise HTTPException(status_code=403, detail="No tienes acceso a este proyecto")
        
        flattened_project = flatten_project_for_frontend(defense_file, include_deliberations=False)
        deliberations = defense_file.get("deliberations", [])
        
        versions = []
        base_project_id = project_id.split("-V")[0] if "-V" in project_id else project_id
        
        all_defense_files = defense_file_service.list_all()
        
        for df in all_defense_files:
            df_project_id = df.get("project_id", "")
            df_project_data = df.get("project_data", {})
            
            version_empresa = df_project_data.get("empresa_id") or df.get("empresa_id")
            if version_empresa and version_empresa.lower().strip() != empresa_id.lower().strip():
                continue
            
            is_related = (
                df_project_id == base_project_id or 
                df_project_id.startswith(f"{base_project_id}-V") or 
                df_project_data.get("parent_project_id") == base_project_id or
                df_project_data.get("parent_project_id", "").startswith(base_project_id)
            )
            
            if is_related:
                versions.append({
                    "project_id": df_project_id,
                    "version": df_project_data.get("version", 1),
                    "is_adjustment": df_project_data.get("is_adjustment", False),
                    "parent_project_id": df_project_data.get("parent_project_id"),
                    "adjustment_notes": df_project_data.get("adjustment_notes"),
                    "created_at": df.get("created_at"),
                    "final_decision": df.get("final_decision"),
                    "is_current": df_project_id == project_id
                })
        
        versions.sort(key=lambda x: x.get("version", 1))
        
        return {
            "success": True,
            "project": flattened_project,
            "defense_file": defense_file,
            "interactions": deliberations,
            "version_history": {
                "base_project_id": base_project_id,
                "version_count": len(versions),
                "versions": versions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {str(e)}")
        # 503 for service issues
        raise HTTPException(status_code=503, detail="Unable to retrieve project details. Service temporarily unavailable.")


@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    """Obtener estado actual de deliberación de un proyecto"""
    from services.deliberation_orchestrator import orchestrator
    from services.defense_file_service import defense_file_service
    
    empresa_id = get_current_empresa_id()
    if not empresa_id:
        raise HTTPException(status_code=400, detail="X-Empresa-ID requerido")
    
    try:
        # Null check
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID is required")

        defense_file = defense_file_service.get_defense_file(project_id)
        if defense_file:
            project_data = defense_file.get("project_data", {})
            if not project_data:
                raise HTTPException(status_code=404, detail="Project data is malformed")

            df_empresa = project_data.get("empresa_id") or defense_file.get("empresa_id")
            if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
                raise HTTPException(status_code=403, detail="No tienes acceso a este proyecto")

        status = orchestrator.get_project_status(project_id)
        if not status:
            raise HTTPException(status_code=404, detail="Project status not found")

        return {
            "success": True,
            "data": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for {project_id}: {str(e)}")
        raise HTTPException(status_code=503, detail="Unable to retrieve project status. Service temporarily unavailable.")


@router.post("/{project_id}/adjustment")
async def submit_adjustment(
    project_id: str,
    adjustment_data: AdjustmentSubmitRequest,
    current_user: dict = Depends(get_current_user_for_projects)
):
    """
    Enviar ajustes para un proyecto existente.
    Crea una nueva versión del proyecto con los ajustes aplicados.
    Requiere autenticación y validación de empresa.
    
    Returns immediately with new project_id - processing happens asynchronously.
    Use /processing-status/{project_id} to poll for completion.
    """
    from services.defense_file_service import defense_file_service
    from services.deliberation_orchestrator import orchestrator
    from services.event_stream import event_emitter
    
    empresa_id = get_current_empresa_id()
    if not empresa_id:
        raise HTTPException(status_code=400, detail="X-Empresa-ID requerido")
    
    base_project_id = project_id.split("-V")[0] if "-V" in project_id else project_id
    new_project_id: Optional[str] = None
    
    try:
        original_defense_file = defense_file_service.get_defense_file(project_id)
        
        if not original_defense_file:
            original_defense_file = defense_file_service.get_defense_file(base_project_id)
        
        if not original_defense_file:
            raise HTTPException(
                status_code=404, 
                detail=f"Proyecto {project_id} no encontrado"
            )
        
        original_project = original_defense_file.get("project_data", {})
        df_empresa = original_project.get("empresa_id") or original_defense_file.get("empresa_id")
        if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
            raise HTTPException(status_code=403, detail="No tienes acceso a este proyecto")
        
        current_version = original_project.get("version", 1)
        new_version = current_version + 1
        
        timestamp = datetime.now(timezone.utc).strftime('%H%M%S')
        new_project_id = f"{base_project_id}-V{new_version}-{timestamp}"
        
        data = adjustment_data.model_dump()
        
        adjusted_project = {
            "id": new_project_id,
            "empresa_id": empresa_id,
            "name": original_project.get("name", "Sin nombre"),
            "client_name": original_project.get("client_name", ""),
            "description": data.get("updated_description") or original_project.get("description", ""),
            "amount": data.get("updated_budget") or original_project.get("amount", 0),
            "service_type": original_project.get("service_type", "Consultoría"),
            "sponsor_name": original_project.get("sponsor_name", ""),
            "sponsor_email": original_project.get("sponsor_email", original_project.get("email", "")),
            "email": original_project.get("sponsor_email", original_project.get("email", "")),
            "department": original_project.get("department", ""),
            "expected_benefit": data.get("updated_benefit") or original_project.get("expected_benefit", 0),
            "duration_months": original_project.get("duration_months", 12),
            "urgency_level": original_project.get("urgency_level", "Normal"),
            "requires_human": original_project.get("requires_human", "No"),
            "attachments": data.get("attachments", []) + original_project.get("attachments", []),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "submitted_by": current_user.get("email", ""),
            "version": new_version,
            "parent_project_id": base_project_id,
            "is_adjustment": True,
            "adjustment_notes": data.get("adjustment_notes", "")
        }
        
        event_emitter.create_session(new_project_id)
        
        await processing_state.set_status(
            project_id=new_project_id,
            status=ProcessingStatus.INITIALIZING,
            message="Ajuste recibido, iniciando re-evaluación...",
            progress=5,
            agent_statuses=[
                {"name": "María Rodríguez", "role": "Estrategia", "status": "Pendiente"},
                {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
            ]
        )
        
        try:
            defense_file = defense_file_service.get_or_create(new_project_id)
            defense_file.project_data = adjusted_project
            defense_file.empresa_id = empresa_id
            defense_file.save()
            logger.info(f"Created defense file for adjustment project {new_project_id}")
        except Exception as df_error:
            logger.warning(f"Could not pre-create defense file for adjustment: {df_error}")
        
        async def run_adjustment_deliberation_async():
            """Run adjustment deliberation in background without blocking"""
            try:
                await processing_state.set_status(
                    project_id=new_project_id,
                    status=ProcessingStatus.PROCESSING,
                    message="Agentes IA re-evaluando ajustes...",
                    progress=10,
                    agent_statuses=[
                        {"name": "María Rodríguez", "role": "Estrategia", "status": "En proceso"},
                        {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                        {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                        {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
                    ]
                )
                
                logger.info(f"Starting adjustment deliberation for project {new_project_id} (parent: {base_project_id})")
                result = await orchestrator.run_agentic_deliberation(adjusted_project)
                
                final_status = result.get('final_status', 'unknown')
                logger.info(f"Adjustment deliberation completed for {new_project_id}: {final_status}")
                
                await processing_state.set_status(
                    project_id=new_project_id,
                    status=ProcessingStatus.COMPLETED,
                    message=f"Re-evaluación completada: {final_status}",
                    progress=100,
                    agent_statuses=[
                        {"name": "María Rodríguez", "role": "Estrategia", "status": "Completado"},
                        {"name": "Laura Sánchez", "role": "Fiscal", "status": "Completado"},
                        {"name": "Roberto Torres", "role": "Finanzas", "status": "Completado"},
                        {"name": "Equipo Legal", "role": "Legal", "status": "Completado"}
                    ]
                )
                
            except Exception as e:
                error_msg = str(e)[:200]
                logger.error(f"Error in adjustment deliberation for {new_project_id}: {error_msg}")
                await processing_state.set_status(
                    project_id=new_project_id,
                    status=ProcessingStatus.FAILED,
                    message="Error durante la re-evaluación",
                    progress=0,
                    error=error_msg
                )
        
        asyncio.create_task(run_adjustment_deliberation_async())
        
        return {
            "success": True,
            "message": "¡Ajuste recibido! Los agentes IA están re-evaluando el proyecto con los ajustes.",
            "project_id": new_project_id,
            "parent_project_id": base_project_id,
            "version": new_version,
            "is_adjustment": True,
            "processing": True,
            "poll_url": f"/api/projects/processing-status/{new_project_id}",
            "adjustment_notes": data.get("adjustment_notes"),
            "agentic_workflow": {
                "status": "INICIADO",
                "agents": [
                    {"name": "María Rodríguez", "role": "Estrategia", "status": "En cola"},
                    {"name": "Laura Sánchez", "role": "Fiscal", "status": "Pendiente"},
                    {"name": "Roberto Torres", "role": "Finanzas", "status": "Pendiente"},
                    {"name": "Equipo Legal", "role": "Legal", "status": "Pendiente"}
                ],
                "model": "Claude",
                "estimated_time": "30-60 segundos"
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error submitting adjustment for {project_id}: {str(e)}")
        error_project_id = new_project_id if new_project_id else project_id
        try:
            await processing_state.set_status(
                project_id=error_project_id,
                status=ProcessingStatus.FAILED,
                message="Datos del ajuste inválidos",
                error=str(e)[:200]
            )
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting adjustment for {project_id}: {str(e)}")
        error_project_id = new_project_id if new_project_id else project_id
        try:
            await processing_state.set_status(
                project_id=error_project_id,
                status=ProcessingStatus.FAILED,
                message="Error al crear el ajuste",
                error=str(e)[:200]
            )
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="Error processing adjustment. Try again later.")


@router.get("/{project_id}/versions")
async def get_project_versions(project_id: str):
    """Obtener historial de versiones de un proyecto"""
    from services.defense_file_service import defense_file_service
    
    empresa_id = get_current_empresa_id()
    if not empresa_id:
        raise HTTPException(status_code=400, detail="X-Empresa-ID requerido")
    
    try:
        versions = []
        
        base_project_id = project_id.split("-V")[0] if "-V" in project_id else project_id
        
        all_defense_files = defense_file_service.list_all()
        
        for df in all_defense_files:
            df_project_id = df.get("project_id", "")
            project_data = df.get("project_data", {})
            
            version_empresa = project_data.get("empresa_id") or df.get("empresa_id")
            if version_empresa and version_empresa.lower().strip() != empresa_id.lower().strip():
                continue
            
            is_related = (
                df_project_id == base_project_id or 
                df_project_id.startswith(f"{base_project_id}-V") or 
                project_data.get("parent_project_id") == base_project_id or
                project_data.get("parent_project_id", "").startswith(base_project_id)
            )
            
            if is_related:
                deliberations = df.get("deliberations", [])
                agent_states = []
                approved_count = 0
                total_agents = len(deliberations)
                
                for delib in deliberations:
                    decision = delib.get("decision", "pending")
                    is_approved = decision in ["approve", "approved"]
                    if is_approved:
                        approved_count += 1
                    agent_states.append({
                        "agent_id": delib.get("agent_id", ""),
                        "stage": delib.get("stage", ""),
                        "decision": decision,
                        "timestamp": delib.get("timestamp")
                    })
                
                dynamic_compliance = round((approved_count / total_agents) * 100) if total_agents > 0 else 0
                
                versions.append({
                    "project_id": df_project_id,
                    "version": project_data.get("version", 1),
                    "is_adjustment": project_data.get("is_adjustment", False),
                    "parent_project_id": project_data.get("parent_project_id"),
                    "adjustment_notes": project_data.get("adjustment_notes"),
                    "created_at": df.get("created_at"),
                    "final_decision": df.get("final_decision"),
                    "name": project_data.get("name", "Sin nombre"),
                    "amount": project_data.get("amount", 0),
                    "deliberation_count": total_agents,
                    "compliance_score": dynamic_compliance,
                    "agent_states": agent_states
                })
        
        versions.sort(key=lambda x: x.get("version", 1))
        
        return {
            "success": True,
            "base_project_id": base_project_id,
            "empresa_id": empresa_id,
            "version_count": len(versions),
            "versions": versions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting versions for {project_id}: {str(e)}")
        # 503 for service issues
        raise HTTPException(status_code=503, detail="Unable to retrieve project versions. Service temporarily unavailable.")
