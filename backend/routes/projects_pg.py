"""
Projects API Routes - PostgreSQL Backend.
New endpoints using the consolidated PostgreSQL database.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid
import os
import shutil
from pathlib import Path

from middleware.tenant_context import get_current_empresa_id, get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class ProjectCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=500)
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    proveedor_rfc: Optional[str] = None
    proveedor_nombre: Optional[str] = None
    monto_total: Optional[float] = None
    datos_sib: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    estado: Optional[str] = None
    fase_actual: Optional[int] = None
    proveedor_rfc: Optional[str] = None
    proveedor_nombre: Optional[str] = None
    monto_total: Optional[float] = None
    risk_score: Optional[int] = None
    compliance_score: Optional[int] = None


class DeliberationCreate(BaseModel):
    fase: int = Field(..., ge=0, le=9)
    agente_id: str
    tipo: str = "opinion"
    contenido: str
    resumen: Optional[str] = None
    decision: Optional[Dict[str, Any]] = None


from jose import jwt, exceptions as jose_exceptions
import asyncio
from enum import Enum

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


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class PhaseUpdate(BaseModel):
    estado: str
    aprobado_por: Optional[Dict[str, Any]] = None


@router.get("")
async def list_projects(
    request: Request,
    estado: Optional[str] = None,
    fase: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
):
    """Listar proyectos (PostgreSQL). Admin ve TODOS los proyectos."""
    from services.database_pg import get_project_service

    # Check if user is admin
    tenant = get_current_tenant()
    is_admin = tenant.is_admin if tenant else False

    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")

    # Admin can see all projects without empresa_id
    if not empresa_id and not is_admin:
        raise HTTPException(status_code=400, detail="empresa_id requerido")

    try:
        service = await get_project_service()
        # Pass None for admin to see all projects
        projects = await service.list_projects(
            empresa_id=empresa_id if empresa_id else None,
            estado=estado,
            fase=fase,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "limit": limit,
            "offset": offset,
            "is_admin": is_admin
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_project(
    project_data: ProjectSubmitRequest,
    request: Request
):
    """
    Enviar un nuevo proyecto e iniciar deliberación agéntica automática.
    Ported from legacy projects.py to work with Postgres router.
    """
    from services.defense_file_service import defense_file_service
    from services.deliberation_orchestrator import orchestrator
    from services.event_stream import event_emitter
    from routes.projects import processing_state, ProcessingStatus
    from services.auth_service import get_secret_key, get_current_user

    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    
    # Auth user extraction similar to projects.py
    user_id = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            SECRET_KEY = get_secret_key()
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if not empresa_id:
                empresa_id = payload.get("empresa_id")
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
            "submitted_at": datetime.now().isoformat(),
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
                
                logger.info(f"Starting agentic deliberation for project {project_id}")
                result = await orchestrator.run_agentic_deliberation(project_for_deliberation)
                
                final_status = result.get('final_status', 'unknown')
                
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
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting project: {str(e)}")
        raise HTTPException(status_code=503, detail="Error processing project")


@router.post("")
async def create_project(
    request: Request,
    project: ProjectCreate
):
    """Crear nuevo proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        created = await service.create_project(
            empresa_id=empresa_id,
            nombre=project.nombre,
            descripcion=project.descripcion,
            tipo=project.tipo,
            proveedor_rfc=project.proveedor_rfc,
            proveedor_nombre=project.proveedor_nombre,
            monto_total=project.monto_total,
            datos_sib=project.datos_sib
        )
        
        return {
            "success": True,
            "project": created,
            "message": "Proyecto creado exitosamente"
        }
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(
    request: Request,
    project_id: str
):
    """Obtener proyecto por ID (PostgreSQL). Admin puede ver cualquier proyecto."""
    from services.database_pg import get_project_service

    # Check if user is admin
    tenant = get_current_tenant()
    is_admin = tenant.is_admin if tenant else False

    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")

    # Admin can access any project without empresa_id
    if not empresa_id and not is_admin:
        raise HTTPException(status_code=400, detail="empresa_id requerido")

    try:
        service = await get_project_service()
        # Pass None for admin to access any project
        project = await service.get_project(project_id, empresa_id if empresa_id else None)

        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        return {
            "success": True,
            "project": project
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}")
async def update_project(
    request: Request,
    project_id: str,
    updates: ProjectUpdate
):
    """Actualizar proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="No hay cambios para aplicar")
        
        updated = await service.update_project(project_id, empresa_id, update_dict)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {
            "success": True,
            "project": updated,
            "message": "Proyecto actualizado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    request: Request,
    project_id: str
):
    """Eliminar proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        deleted = await service.delete_project(project_id, empresa_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {
            "success": True,
            "message": "Proyecto eliminado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/phases")
async def get_project_phases(
    request: Request,
    project_id: str
):
    """Obtener estado de fases del proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        phases = await service.get_phase_status(project_id, empresa_id)
        
        return {
            "success": True,
            "phases": phases
        }
    except Exception as e:
        logger.error(f"Error getting phases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}/phases/{fase}")
async def update_project_phase(
    request: Request,
    project_id: str,
    fase: int,
    update: PhaseUpdate
):
    """Actualizar estado de una fase (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        await service.update_phase_status(
            project_id, 
            empresa_id, 
            fase, 
            update.estado,
            update.aprobado_por
        )
        
        return {
            "success": True,
            "message": f"Fase {fase} actualizada a '{update.estado}'"
        }
    except Exception as e:
        logger.error(f"Error updating phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/deliberations")
async def get_project_deliberations(
    request: Request,
    project_id: str,
    fase: Optional[int] = None,
    agente_id: Optional[str] = None
):
    """Obtener deliberaciones del proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        deliberations = await service.get_deliberations(
            project_id, empresa_id, fase, agente_id
        )
        
        return {
            "success": True,
            "deliberations": deliberations
        }
    except Exception as e:
        logger.error(f"Error getting deliberations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/deliberations")
async def add_project_deliberation(
    request: Request,
    project_id: str,
    deliberation: DeliberationCreate
):
    """Agregar deliberación al proyecto (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        
        project = await service.get_project(project_id, empresa_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        created = await service.add_deliberation(
            project_id=project_id,
            empresa_id=empresa_id,
            fase=deliberation.fase,
            agente_id=deliberation.agente_id,
            tipo=deliberation.tipo,
            contenido=deliberation.contenido,
            resumen=deliberation.resumen,
            decision=deliberation.decision
        )
        
        return {
            "success": True,
            "deliberation": created,
            "message": "Deliberación agregada exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{query}")
async def search_projects(
    request: Request,
    query: str,
    limit: int = 20
):
    """Buscar proyectos (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        projects = await service.search_projects(empresa_id, query, limit)
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "query": query
        }
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_project_stats(request: Request):
    """Obtener estadísticas de proyectos (PostgreSQL). Admin ve estadísticas globales."""
    from services.database_pg import get_project_service

    # Check if user is admin
    tenant = get_current_tenant()
    is_admin = tenant.is_admin if tenant else False

    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")

    # Admin can see global stats without empresa_id
    if not empresa_id and not is_admin:
        raise HTTPException(status_code=400, detail="empresa_id requerido")

    try:
        service = await get_project_service()
        stats = await service.get_project_stats(empresa_id if empresa_id else None)

        return {
            "success": True,
            "stats": stats,
            "is_global": is_admin and not empresa_id
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processing-status/{project_id}")
async def get_processing_status(project_id: str):
    """
    Get the real-time processing status of a project.
    Used for the demo polling.
    """
    # Import from the legacy projects module where the state is stored
    # This ensures we share the same state object as deliberation_routes
    from routes.projects import processing_state
    
    status = await processing_state.get_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
        
    return {
        "success": True,
        "data": status
    }


from services.auth_service import get_current_user

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a file for project attachments.
    Securely saves to local disk AND ingests into Knowledge Repository for RAG.
    """
    try:
        # 1. Get Context
        empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
        if not empresa_id:
            # Fallback to user's empresa if not in header
            empresa_id = current_user.get("empresa_id")
            
        if not empresa_id:
             raise HTTPException(status_code=400, detail="Empresa ID required for upload")

        # 2. Read Content (buffer)
        content = await file.read()
        
        # 3. Local Save (Legacy Support)
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"
        filepath = UPLOAD_DIR / filename
        
        with open(filepath, "wb") as f:
            f.write(content)
            
        file_url = f"/uploads/{filename}"
        
        # 4. Knowledge Repo Ingestion (RAG)
        try:
            from services.knowledge_service import KnowledgeService
            service = KnowledgeService()
            
            # ingest into specific projects folder
            await service.upload_file(
                empresa_id=empresa_id,
                path="/projects/attachments",
                filename=file.filename,
                content=content,
                mime_type=file.content_type,
                user_id=current_user.get("id") or current_user.get("user_id")
            )
            logger.info(f"File {file.filename} ingested to KnowledgeService for RAG")
        except Exception as ks_error:
            # Non-blocking error for legacy flow, but critical for RAG
            logger.error(f"Failed to ingest to KnowledgeService: {ks_error}")
            # We don't raise here to preserve legacy behavior, but we log critically
            
        return {
            "success": True,
            "file_url": file_url,
            "filename": file.filename,
            "saved_as": filename,
            "rag_ingested": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
