"""
Workflow Routes - Endpoints para ejecutar las etapas del flujo de proyectos
===========================================================================

Estos endpoints permiten avanzar proyectos a través de las 5 etapas:
- Stage 1: Intake y Validación (ya existe en webhooks)
- Stage 2: Formalización Legal y Financiera
- Stage 3: Ejecución y Monitoreo
- Stage 4: Entrega y Auditoría
- Stage 5: Cierre y Medición de Impacto
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from services.auth_service import get_current_user
from services.error_handler import handle_route_error, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["Workflow Stages"])


# ============================================================
# Request/Response Models
# ============================================================

class Stage2Request(BaseModel):
    """Request para Stage 2 - Formalización Legal"""
    vendor_id: Optional[str] = Field(None, description="ID del proveedor seleccionado")
    contract_type: Optional[str] = Field("standard", description="Tipo de contrato")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class Stage3Request(BaseModel):
    """Request para Stage 3 - Ejecución"""
    start_execution: bool = Field(True, description="Iniciar ejecución inmediatamente")
    assigned_team: Optional[List[str]] = Field(None, description="IDs del equipo asignado")


class Stage4Request(BaseModel):
    """Request para Stage 4 - Entrega y Auditoría"""
    deliverables: List[str] = Field(..., description="Lista de entregables a auditar")
    delivery_notes: Optional[str] = Field(None, description="Notas de entrega")


class Stage5Request(BaseModel):
    """Request para Stage 5 - Cierre"""
    final_approval: bool = Field(True, description="Aprobación final para cierre")
    impact_notes: Optional[str] = Field(None, description="Notas sobre impacto medido")


class StageResponse(BaseModel):
    """Respuesta estándar de ejecución de stage"""
    success: bool
    project_id: str
    stage: int
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    next_stage: Optional[int] = None


# ============================================================
# Dependency para obtener el WorkflowService
# ============================================================

async def get_workflow_service():
    """Obtiene instancia del WorkflowService"""
    try:
        from services.workflow_service import WorkflowService
        service = WorkflowService()
        await service.initialize()
        return service
    except Exception as e:
        logger.error(f"Error initializing WorkflowService: {e}")
        raise HTTPException(status_code=500, detail="Error inicializando servicio de workflow")


# ============================================================
# Stage 2: Formalización Legal y Financiera
# ============================================================

@router.post("/projects/{project_id}/stage2", response_model=StageResponse)
async def execute_stage_2(
    project_id: str,
    request: Stage2Request = None,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Ejecuta Stage 2: Formalización Legal y Financiera

    Este stage incluye:
    - Selección de proveedor
    - Verificación presupuestal (A5-Finanzas)
    - Generación de PO (Purchase Order)
    - Generación contractual
    """
    try:
        logger.info(f"Executing Stage 2 for project {project_id} by user {current_user.get('sub')}")

        result = await workflow_service.stage_2_legal_and_financial(project_id)

        if result.get("status") == "error":
            return StageResponse(
                success=False,
                project_id=project_id,
                stage=2,
                status="error",
                message=result.get("error", "Error en Stage 2"),
                data=result
            )

        return StageResponse(
            success=True,
            project_id=project_id,
            stage=2,
            status="completed",
            message="Stage 2 completado - Formalización legal y financiera",
            data=result,
            next_stage=3
        )

    except Exception as e:
        logger.error(f"Error in Stage 2 for project {project_id}: {e}")
        return handle_route_error(e, f"Stage 2 - Proyecto {project_id}")


# ============================================================
# Stage 3: Ejecución y Monitoreo
# ============================================================

@router.post("/projects/{project_id}/stage3", response_model=StageResponse)
async def execute_stage_3(
    project_id: str,
    request: Stage3Request = None,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Ejecuta Stage 3: Ejecución y Monitoreo

    Este stage incluye:
    - Ejecución del servicio (Proveedor)
    - Monitoreo de materialidad (A3-Fiscal)
    - Gestión de cronograma (A2-PMO)
    - Generación de evidencia digital
    """
    try:
        logger.info(f"Executing Stage 3 for project {project_id} by user {current_user.get('sub')}")

        result = await workflow_service.stage_3_execution_monitoring(project_id)

        if result.get("status") == "error":
            return StageResponse(
                success=False,
                project_id=project_id,
                stage=3,
                status="error",
                message=result.get("error", "Error en Stage 3"),
                data=result
            )

        return StageResponse(
            success=True,
            project_id=project_id,
            stage=3,
            status="completed",
            message="Stage 3 completado - Ejecución y monitoreo",
            data=result,
            next_stage=4
        )

    except Exception as e:
        logger.error(f"Error in Stage 3 for project {project_id}: {e}")
        return handle_route_error(e, f"Stage 3 - Proyecto {project_id}")


# ============================================================
# Stage 4: Entrega y Auditoría
# ============================================================

@router.post("/projects/{project_id}/stage4", response_model=StageResponse)
async def execute_stage_4(
    project_id: str,
    request: Stage4Request,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Ejecuta Stage 4: Entrega y Auditoría

    Este stage incluye:
    - Recepción de entregables
    - Validación técnica (A1-Sponsor)
    - Auditoría de cumplimiento (A3-Fiscal)
    - Generación de VBC (Visto Bueno de Cumplimiento)

    Requiere lista de entregables a auditar.
    """
    try:
        logger.info(f"Executing Stage 4 for project {project_id} by user {current_user.get('sub')}")

        if not request.deliverables:
            raise HTTPException(
                status_code=400,
                detail="Se requiere al menos un entregable para auditar"
            )

        result = await workflow_service.stage_4_delivery_audit(
            project_id=project_id,
            deliverables=request.deliverables
        )

        if result.get("status") == "error":
            return StageResponse(
                success=False,
                project_id=project_id,
                stage=4,
                status="error",
                message=result.get("error", "Error en Stage 4"),
                data=result
            )

        return StageResponse(
            success=True,
            project_id=project_id,
            stage=4,
            status="completed",
            message="Stage 4 completado - Entrega auditada y VBC generado",
            data=result,
            next_stage=5
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Stage 4 for project {project_id}: {e}")
        return handle_route_error(e, f"Stage 4 - Proyecto {project_id}")


# ============================================================
# Stage 5: Cierre y Medición de Impacto
# ============================================================

@router.post("/projects/{project_id}/stage5", response_model=StageResponse)
async def execute_stage_5(
    project_id: str,
    request: Stage5Request = None,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Ejecuta Stage 5: Cierre y Medición de Impacto

    Este stage incluye:
    - 3-Way Match (A5-Finanzas)
    - Proceso de pago
    - Medición de impacto real vs. esperado
    - Validación de trazabilidad posterior
    - Cierre del proyecto
    """
    try:
        logger.info(f"Executing Stage 5 for project {project_id} by user {current_user.get('sub')}")

        result = await workflow_service.stage_5_closure_impact(project_id)

        if result.get("status") == "error":
            return StageResponse(
                success=False,
                project_id=project_id,
                stage=5,
                status="error",
                message=result.get("error", "Error en Stage 5"),
                data=result
            )

        return StageResponse(
            success=True,
            project_id=project_id,
            stage=5,
            status="closed",
            message="Proyecto cerrado exitosamente - Pago liberado",
            data=result,
            next_stage=None  # Proyecto terminado
        )

    except Exception as e:
        logger.error(f"Error in Stage 5 for project {project_id}: {e}")
        return handle_route_error(e, f"Stage 5 - Proyecto {project_id}")


# ============================================================
# Endpoints de consulta
# ============================================================

@router.get("/projects/{project_id}/current-stage")
async def get_current_stage(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Obtiene el stage actual de un proyecto y las acciones disponibles.
    """
    try:
        # Obtener proyecto de la BD
        project = await workflow_service.db.projects.find_one({"project_id": project_id})

        if not project:
            raise NotFoundError(f"Proyecto {project_id} no encontrado")

        current_phase = project.get("current_phase", "phase_0")
        status = project.get("status", "unknown")

        # Mapear fase a stage
        phase_to_stage = {
            "phase_0": 1,
            "phase_1": 2,
            "phase_2": 2,
            "phase_3": 3,
            "phase_4": 3,
            "phase_5": 4,
            "phase_6": 4,
            "phase_7": 4,
            "phase_8": 5,
            "phase_9": 5,
            "closed": 5
        }

        current_stage = phase_to_stage.get(current_phase, 1)

        # Determinar acciones disponibles
        available_actions = []
        if status not in ["closed", "rejected", "cancelled"]:
            if current_stage < 5:
                available_actions.append(f"Execute Stage {current_stage + 1}")
            if current_stage == 5:
                available_actions.append("Close Project")

        return {
            "project_id": project_id,
            "current_stage": current_stage,
            "current_phase": current_phase,
            "status": status,
            "available_actions": available_actions,
            "project_name": project.get("project_name", ""),
            "updated_at": project.get("updated_at", "")
        }

    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Proyecto {project_id} no encontrado")
    except Exception as e:
        logger.error(f"Error getting stage for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado del proyecto")


@router.get("/projects/{project_id}/timeline")
async def get_project_timeline(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    workflow_service = Depends(get_workflow_service)
):
    """
    Obtiene el timeline completo del proyecto con todas las interacciones de agentes.
    """
    try:
        # Obtener interacciones ordenadas por timestamp
        interactions = await workflow_service.db.agent_interactions.find(
            {"project_id": project_id}
        ).sort("timestamp", 1).to_list(500)

        # Agrupar por fase
        phases = {}
        for interaction in interactions:
            phase = interaction.get("phase", "unknown")
            if phase not in phases:
                phases[phase] = []
            phases[phase].append({
                "timestamp": interaction.get("timestamp"),
                "from_agent": interaction.get("from_agent"),
                "to_agent": interaction.get("to_agent"),
                "interaction_type": interaction.get("interaction_type"),
                "summary": interaction.get("content", "")[:200] + "..." if len(interaction.get("content", "")) > 200 else interaction.get("content", "")
            })

        return {
            "project_id": project_id,
            "total_interactions": len(interactions),
            "phases": phases
        }

    except Exception as e:
        logger.error(f"Error getting timeline for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo timeline del proyecto")
