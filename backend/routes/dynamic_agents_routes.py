"""
dynamic_agents_routes.py - API Routes para Sistema de Agentes Dinámicos

Endpoints para:
- CRUD de agentes y subagentes
- Carga dinámica de configuraciones
- Feedback y aprendizaje
- Sincronización con pCloud
- Métricas y auditoría

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/dynamic", tags=["Dynamic Agents"])


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class AgentCreateModel(BaseModel):
    agent_id: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=100)
    rol: str = Field(..., min_length=2, max_length=200)
    descripcion: str = Field(default="")
    personalidad: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    tipo: str = Field(default="principal")
    capabilities: List[str] = Field(default=[])
    fases_activas: List[str] = Field(default=[])
    puede_bloquear: bool = False
    fases_bloqueo: List[str] = Field(default=[])
    agente_padre_id: Optional[str] = None
    pcloud_path: Optional[str] = None
    puede_crear_agentes: bool = False
    puede_editar_agentes: bool = False
    puede_eliminar_agentes: bool = False
    puede_crear_documentos: bool = True
    puede_editar_documentos: bool = True
    puede_eliminar_documentos: bool = False


class AgentUpdateModel(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    descripcion: Optional[str] = None
    personalidad: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[List[str]] = None
    fases_activas: Optional[List[str]] = None
    puede_bloquear: Optional[bool] = None
    fases_bloqueo: Optional[List[str]] = None
    pcloud_path: Optional[str] = None
    es_activo: Optional[bool] = None
    puede_crear_agentes: Optional[bool] = None
    puede_editar_agentes: Optional[bool] = None
    puede_eliminar_agentes: Optional[bool] = None
    puede_crear_documentos: Optional[bool] = None
    puede_editar_documentos: Optional[bool] = None
    puede_eliminar_documentos: Optional[bool] = None


class SubagentCreateModel(BaseModel):
    subagent_id: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=100)
    funcion: str = Field(..., min_length=2, max_length=200)
    descripcion: str = Field(default="")
    system_prompt: str = Field(..., min_length=10)
    tipo: str = Field(...)  # tipificacion, materialidad, riesgos, etc.
    agente_padre_id: Optional[str] = None
    capabilities: List[str] = Field(default=[])
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None
    trigger_conditions: List[Dict] = Field(default=[])
    priority: int = Field(default=5, ge=1, le=10)


class DocumentCreateModel(BaseModel):
    agent_id: str
    document_type: str = Field(...)  # metodologia, training, feedback, ejemplo
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=1)
    file_type: str = Field(default="md")
    pcloud_path: Optional[str] = None


class FeedbackModel(BaseModel):
    agent_id: str
    empresa_id: UUID
    user_id: UUID
    feedback_type: str = Field(...)  # positive, negative, correction, suggestion
    rating: int = Field(..., ge=1, le=5)
    feedback_content: str = Field(default="")
    decision_id: Optional[UUID] = None
    suggested_decision: Optional[str] = None


class DecisionRecordModel(BaseModel):
    agent_id: str
    empresa_id: UUID
    project_id: UUID
    decision_type: str
    decision_value: str
    reasoning: str
    confidence: float = Field(..., ge=0, le=1)
    context_used: Optional[Dict] = None
    fase: Optional[str] = None


class OutcomeRecordModel(BaseModel):
    decision_id: UUID
    actual_outcome: str
    was_correct: bool
    validated_by: str = "user"
    lessons_learned: Optional[str] = None


# ============================================================================
# ENDPOINTS DE AGENTES
# ============================================================================

@router.get("/agents")
async def list_agents(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: principal, subagente, orquestador, codigo"),
    include_inactive: bool = Query(False, description="Incluir agentes inactivos")
):
    """Listar todos los agentes configurados."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()
        agents = await loader.load_all_agents(tipo=tipo)

        return {
            "success": True,
            "count": len(agents),
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "nombre": a.nombre,
                    "rol": a.rol,
                    "tipo": a.tipo,
                    "es_activo": a.es_activo,
                    "capabilities": a.capabilities,
                    "fases_activas": a.fases_activas,
                    "puede_bloquear": a.puede_bloquear,
                    "version": a.version
                }
                for a in agents
            ]
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    include_learnings: bool = Query(True, description="Incluir aprendizajes"),
    include_metrics: bool = Query(True, description="Incluir métricas")
):
    """Obtener configuración completa de un agente."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()
        agent = await loader.load_agent(agent_id, include_learnings=include_learnings)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
            "success": True,
            "agent": {
                "id": str(agent.id),
                "agent_id": agent.agent_id,
                "nombre": agent.nombre,
                "rol": agent.rol,
                "descripcion": agent.descripcion,
                "personalidad": agent.personalidad,
                "system_prompt": agent.system_prompt,
                "tipo": agent.tipo,
                "capabilities": agent.capabilities,
                "fases_activas": agent.fases_activas,
                "puede_bloquear": agent.puede_bloquear,
                "fases_bloqueo": agent.fases_bloqueo,
                "pcloud_path": agent.pcloud_path,
                "es_activo": agent.es_activo,
                "version": agent.version,
                "permisos": {
                    "puede_crear_agentes": agent.puede_crear_agentes,
                    "puede_editar_agentes": agent.puede_editar_agentes,
                    "puede_eliminar_agentes": agent.puede_eliminar_agentes,
                    "puede_crear_documentos": agent.puede_crear_documentos,
                    "puede_editar_documentos": agent.puede_editar_documentos,
                    "puede_eliminar_documentos": agent.puede_eliminar_documentos,
                },
                "learnings": agent.learnings if include_learnings else None,
                "metrics": agent.metrics if include_metrics else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/prompt")
async def get_agent_prompt(
    agent_id: str,
    include_learnings: bool = Query(True),
    context: Optional[Dict] = Body(None)
):
    """Obtener prompt dinámico de un agente con contexto opcional."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()
        prompt = await loader.get_dynamic_prompt(
            agent_id,
            context=context,
            include_learnings=include_learnings
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "prompt": prompt,
            "prompt_length": len(prompt)
        }
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents")
async def create_agent(
    data: AgentCreateModel,
    created_by_agent: Optional[str] = Query(None, description="ID del agente que crea"),
    created_by_user: Optional[UUID] = Query(None, description="UUID del usuario que crea")
):
    """Crear un nuevo agente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service, AgentCreateRequest
        crud = await get_agent_crud_service()

        request = AgentCreateRequest(
            agent_id=data.agent_id,
            nombre=data.nombre,
            rol=data.rol,
            descripcion=data.descripcion,
            personalidad=data.personalidad,
            system_prompt=data.system_prompt,
            tipo=data.tipo,
            capabilities=data.capabilities,
            fases_activas=data.fases_activas,
            puede_bloquear=data.puede_bloquear,
            fases_bloqueo=data.fases_bloqueo,
            agente_padre_id=data.agente_padre_id,
            pcloud_path=data.pcloud_path,
            puede_crear_agentes=data.puede_crear_agentes,
            puede_editar_agentes=data.puede_editar_agentes,
            puede_eliminar_agentes=data.puede_eliminar_agentes,
            puede_crear_documentos=data.puede_crear_documentos,
            puede_editar_documentos=data.puede_editar_documentos,
            puede_eliminar_documentos=data.puede_eliminar_documentos
        )

        result = await crud.create_agent(
            request,
            created_by_agent=created_by_agent,
            created_by_user=created_by_user
        )

        if not result:
            raise HTTPException(status_code=400, detail="Failed to create agent")

        return {"success": True, **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    data: AgentUpdateModel,
    updated_by_agent: Optional[str] = Query(None),
    updated_by_user: Optional[UUID] = Query(None),
    reason: Optional[str] = Query(None, description="Razón del cambio")
):
    """Actualizar un agente existente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service, AgentUpdateRequest
        crud = await get_agent_crud_service()

        request = AgentUpdateRequest(
            nombre=data.nombre,
            rol=data.rol,
            descripcion=data.descripcion,
            personalidad=data.personalidad,
            system_prompt=data.system_prompt,
            capabilities=data.capabilities,
            fases_activas=data.fases_activas,
            puede_bloquear=data.puede_bloquear,
            fases_bloqueo=data.fases_bloqueo,
            pcloud_path=data.pcloud_path,
            es_activo=data.es_activo,
            puede_crear_agentes=data.puede_crear_agentes,
            puede_editar_agentes=data.puede_editar_agentes,
            puede_eliminar_agentes=data.puede_eliminar_agentes,
            puede_crear_documentos=data.puede_crear_documentos,
            puede_editar_documentos=data.puede_editar_documentos,
            puede_eliminar_documentos=data.puede_eliminar_documentos
        )

        result = await crud.update_agent(
            agent_id,
            request,
            updated_by_agent=updated_by_agent,
            updated_by_user=updated_by_user,
            reason=reason
        )

        if not result:
            raise HTTPException(status_code=400, detail="Failed to update agent")

        return {"success": True, **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    deleted_by_agent: Optional[str] = Query(None),
    deleted_by_user: Optional[UUID] = Query(None),
    hard_delete: bool = Query(False, description="Eliminación permanente (peligroso)"),
    reason: Optional[str] = Query(None)
):
    """Eliminar (desactivar) un agente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service
        crud = await get_agent_crud_service()

        success = await crud.delete_agent(
            agent_id,
            deleted_by_agent=deleted_by_agent,
            deleted_by_user=deleted_by_user,
            hard_delete=hard_delete,
            reason=reason
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete agent")

        return {"success": True, "agent_id": agent_id, "deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE SUBAGENTES
# ============================================================================

@router.get("/subagents")
async def list_subagents(
    agente_padre_id: Optional[str] = Query(None, description="Filtrar por agente padre"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo")
):
    """Listar subagentes."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()
        subagents = await loader.load_subagents(agente_padre_id=agente_padre_id)

        if tipo:
            subagents = [s for s in subagents if s.tipo == tipo]

        return {
            "success": True,
            "count": len(subagents),
            "subagents": [
                {
                    "subagent_id": s.subagent_id,
                    "nombre": s.nombre,
                    "funcion": s.funcion,
                    "tipo": s.tipo,
                    "priority": s.priority,
                    "es_activo": s.es_activo
                }
                for s in subagents
            ]
        }
    except Exception as e:
        logger.error(f"Error listing subagents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subagents")
async def create_subagent(
    data: SubagentCreateModel,
    created_by_agent: Optional[str] = Query(None),
    created_by_user: Optional[UUID] = Query(None)
):
    """Crear un nuevo subagente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service, SubagentCreateRequest
        crud = await get_agent_crud_service()

        request = SubagentCreateRequest(
            subagent_id=data.subagent_id,
            nombre=data.nombre,
            funcion=data.funcion,
            descripcion=data.descripcion,
            system_prompt=data.system_prompt,
            tipo=data.tipo,
            agente_padre_id=data.agente_padre_id,
            capabilities=data.capabilities,
            input_schema=data.input_schema,
            output_schema=data.output_schema,
            trigger_conditions=data.trigger_conditions,
            priority=data.priority
        )

        result = await crud.create_subagent(
            request,
            created_by_agent=created_by_agent,
            created_by_user=created_by_user
        )

        if not result:
            raise HTTPException(status_code=400, detail="Failed to create subagent")

        return {"success": True, **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subagent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE DOCUMENTOS
# ============================================================================

@router.post("/documents")
async def create_document(
    data: DocumentCreateModel,
    created_by_agent: Optional[str] = Query(None),
    created_by_user: Optional[UUID] = Query(None)
):
    """Crear un documento para un agente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service, DocumentCreateRequest
        crud = await get_agent_crud_service()

        request = DocumentCreateRequest(
            agent_id=data.agent_id,
            document_type=data.document_type,
            title=data.title,
            content=data.content,
            file_type=data.file_type,
            pcloud_path=data.pcloud_path
        )

        result = await crud.create_document(
            request,
            created_by_agent=created_by_agent,
            created_by_user=created_by_user
        )

        if not result:
            raise HTTPException(status_code=400, detail="Failed to create document")

        return {"success": True, **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE FEEDBACK Y APRENDIZAJE
# ============================================================================

@router.post("/decisions")
async def record_decision(data: DecisionRecordModel):
    """Registrar una decisión de un agente."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()

        decision_id = await loader.record_decision(
            agent_id=data.agent_id,
            empresa_id=data.empresa_id,
            project_id=data.project_id,
            decision_type=data.decision_type,
            decision_value=data.decision_value,
            reasoning=data.reasoning,
            confidence=data.confidence,
            context_used=data.context_used,
            fase=data.fase
        )

        if not decision_id:
            raise HTTPException(status_code=400, detail="Failed to record decision")

        return {"success": True, "decision_id": str(decision_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outcomes")
async def record_outcome(data: OutcomeRecordModel):
    """Registrar el outcome real de una decisión (feedback loop)."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()

        success = await loader.record_outcome(
            decision_id=data.decision_id,
            actual_outcome=data.actual_outcome,
            was_correct=data.was_correct,
            validated_by=data.validated_by,
            lessons_learned=data.lessons_learned
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to record outcome")

        return {"success": True, "message": "Outcome recorded and learning generated if applicable"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_feedback(data: FeedbackModel):
    """Registrar feedback de usuario sobre un agente."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()

        success = await loader.record_feedback(
            agent_id=data.agent_id,
            empresa_id=data.empresa_id,
            user_id=data.user_id,
            feedback_type=data.feedback_type,
            rating=data.rating,
            feedback_content=data.feedback_content,
            decision_id=data.decision_id,
            suggested_decision=data.suggested_decision
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to record feedback")

        return {"success": True, "message": "Feedback recorded"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE SINCRONIZACIÓN
# ============================================================================

@router.post("/agents/{agent_id}/sync-pcloud")
async def sync_agent_pcloud(agent_id: str):
    """Sincronizar documentos de un agente desde pCloud."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()

        nuevos, actualizados = await loader.sync_agent_documents_from_pcloud(agent_id)

        return {
            "success": True,
            "agent_id": agent_id,
            "documents_created": nuevos,
            "documents_updated": actualizados
        }

    except Exception as e:
        logger.error(f"Error syncing pcloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all-pcloud")
async def sync_all_agents_pcloud():
    """Sincronizar documentos de todos los agentes desde pCloud."""
    try:
        from ..services.dynamic_agent_loader import get_agent_loader
        loader = await get_agent_loader()
        agents = await loader.load_all_agents()

        results = {}
        total_nuevos = 0
        total_actualizados = 0

        for agent in agents:
            if agent.pcloud_path:
                nuevos, actualizados = await loader.sync_agent_documents_from_pcloud(agent.agent_id)
                results[agent.agent_id] = {"new": nuevos, "updated": actualizados}
                total_nuevos += nuevos
                total_actualizados += actualizados

        return {
            "success": True,
            "total_documents_created": total_nuevos,
            "total_documents_updated": total_actualizados,
            "details": results
        }

    except Exception as e:
        logger.error(f"Error syncing all pcloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE AUDITORÍA
# ============================================================================

@router.get("/agents/{agent_id}/audit")
async def get_agent_audit(
    agent_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """Obtener historial de cambios de un agente."""
    try:
        from ..services.agent_crud_service import get_agent_crud_service
        crud = await get_agent_crud_service()

        history = await crud.get_agent_audit_history(agent_id, limit=limit)

        return {
            "success": True,
            "agent_id": agent_id,
            "count": len(history),
            "audit_log": history
        }

    except Exception as e:
        logger.error(f"Error getting audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
