"""
Projects API Routes - PostgreSQL Backend.
New endpoints using the consolidated PostgreSQL database.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from middleware.tenant_context import get_current_empresa_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/pg", tags=["projects-postgresql"])


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
    """Listar proyectos (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        projects = await service.list_projects(
            empresa_id=empresa_id,
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
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    """Obtener proyecto por ID (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        project = await service.get_project(project_id, empresa_id)
        
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
    """Obtener estadísticas de proyectos (PostgreSQL)."""
    from services.database_pg import get_project_service
    
    empresa_id = get_current_empresa_id() or request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    try:
        service = await get_project_service()
        stats = await service.get_project_stats(empresa_id)
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
