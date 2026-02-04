"""
Workers Webhook Routes
Endpoints para recibir callbacks de Cloudflare Workers.

Última actualización: 2026-02-04
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional, Dict, Any
from datetime import datetime

from services.workers_hub_service import workers_hub_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Workers Webhooks"])


@router.post("/worker-callback")
async def worker_callback(
    request: Request,
    x_worker_callback: Optional[str] = Header(None),
    x_empresa_id: Optional[str] = Header(None)
):
    """
    Endpoint para recibir callbacks de Workers completados.

    Los Workers envían aquí los resultados de tareas asíncronas.
    """
    try:
        payload = await request.json()

        logger.info(f"Worker callback recibido: {payload.get('tarea', 'unknown')}")

        # Validar que viene de un Worker
        if x_worker_callback != "true":
            logger.warning("Callback sin header X-Worker-Callback")

        # Procesar callback
        result = await workers_hub_service.handle_worker_callback(payload)

        return {
            "status": "ok",
            "processed": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error procesando worker callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/status")
async def get_workers_status():
    """
    Obtiene el estado de todos los Workers del Hub.
    """
    try:
        status = await workers_hub_service.get_workers_status()
        return status
    except Exception as e:
        logger.error(f"Error obteniendo status de workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/capabilities")
async def get_workers_capabilities():
    """
    Obtiene las capacidades disponibles en los Workers.
    """
    try:
        capabilities = await workers_hub_service.get_available_capabilities()
        return {
            "capabilities": capabilities,
            "count": len(capabilities)
        }
    except Exception as e:
        logger.error(f"Error obteniendo capacidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/execute")
async def execute_worker_task(
    request: Request,
    x_empresa_id: Optional[str] = Header(None),
    x_agent_id: Optional[str] = Header(None)
):
    """
    Endpoint para ejecutar una tarea en un Worker desde el frontend o agentes.

    Body:
    {
        "tarea": "investigacion",
        "parametros": {...},
        "proyecto_id": "PROJ-123",
        "async": false  // Si true, retorna inmediatamente y usa callback
    }
    """
    try:
        body = await request.json()

        tarea = body.get("tarea")
        parametros = body.get("parametros", {})
        proyecto_id = body.get("proyecto_id")
        is_async = body.get("async", False)

        if not tarea:
            raise HTTPException(status_code=400, detail="Tarea requerida")

        # Construir callback URL si es async
        callback_url = None
        if is_async:
            # Usar la URL base del request para construir callback
            base_url = str(request.base_url).rstrip("/")
            callback_url = f"{base_url}/webhooks/worker-callback"

        # Ejecutar tarea
        result = await workers_hub_service.ejecutar_tarea(
            tarea=tarea,
            parametros=parametros,
            agente_id=x_agent_id,
            empresa_id=x_empresa_id,
            proyecto_id=proyecto_id,
            callback_url=callback_url
        )

        return {
            "success": result.success,
            "worker_id": result.worker_id,
            "tarea": result.tarea,
            "resultado": result.resultado,
            "error": result.error,
            "timestamp": result.timestamp
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando tarea de worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/pipeline")
async def execute_worker_pipeline(
    request: Request,
    x_empresa_id: Optional[str] = Header(None),
    x_agent_id: Optional[str] = Header(None)
):
    """
    Ejecuta un pipeline de múltiples tareas en Workers.

    Body:
    {
        "pasos": [
            {"tarea": "scraping", "parametros": {"url": "..."}},
            {"tarea": "investigacion", "parametros": {"empresa": "..."}},
            {"tarea": "materialidad", "parametros": {...}}
        ]
    }
    """
    try:
        body = await request.json()
        pasos = body.get("pasos", [])

        if not pasos:
            raise HTTPException(status_code=400, detail="Se requieren pasos")

        # Callback URL
        base_url = str(request.base_url).rstrip("/")
        callback_url = f"{base_url}/webhooks/worker-callback"

        result = await workers_hub_service.ejecutar_pipeline(
            pasos=pasos,
            empresa_id=x_empresa_id,
            agente_id=x_agent_id,
            callback_url=callback_url
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS ESPECÍFICOS PARA AGENTES
# ============================================================================

@router.post("/workers/due-diligence")
async def due_diligence_proveedor(
    request: Request,
    x_empresa_id: Optional[str] = Header(None)
):
    """
    Endpoint específico para due diligence de proveedores.
    Usado por A6_PROVEEDOR.

    Body:
    {
        "empresa": "Nombre de la empresa",
        "rfc": "RFC123456ABC",
        "sitio_web": "https://...",
        "monto": 100000,
        "tipo_servicio": "Consultoría"
    }
    """
    try:
        body = await request.json()

        result = await workers_hub_service.investigar_proveedor(
            empresa=body.get("empresa"),
            rfc=body.get("rfc"),
            sitio_web=body.get("sitio_web"),
            monto=body.get("monto"),
            tipo_servicio=body.get("tipo_servicio"),
            empresa_id=x_empresa_id,
            proyecto_id=body.get("proyecto_id")
        )

        return {
            "success": result.success,
            "resultado": result.resultado,
            "error": result.error
        }

    except Exception as e:
        logger.error(f"Error en due diligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/materialidad")
async def documentar_materialidad(
    request: Request,
    x_empresa_id: Optional[str] = Header(None)
):
    """
    Endpoint específico para documentación de materialidad SAT.
    Usado por S2_MATERIALIDAD.

    Body:
    {
        "empresa": "Nombre proveedor",
        "rfc": "RFC...",
        "servicio": "Descripción del servicio",
        "monto": 100000,
        "sitio_web": "https://..."
    }
    """
    try:
        body = await request.json()

        result = await workers_hub_service.documentar_materialidad(
            empresa=body.get("empresa"),
            rfc=body.get("rfc"),
            servicio=body.get("servicio"),
            monto=body.get("monto"),
            sitio_web=body.get("sitio_web"),
            empresa_id=x_empresa_id,
            proyecto_id=body.get("proyecto_id")
        )

        return {
            "success": result.success,
            "resultado": result.resultado,
            "error": result.error
        }

    except Exception as e:
        logger.error(f"Error en materialidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/verificar-69b")
async def verificar_lista_69b(
    request: Request,
    x_empresa_id: Optional[str] = Header(None)
):
    """
    Verifica un RFC contra la lista 69-B del SAT.

    Body:
    {
        "rfc": "RFC123456ABC"
    }
    """
    try:
        body = await request.json()
        rfc = body.get("rfc")

        if not rfc:
            raise HTTPException(status_code=400, detail="RFC requerido")

        result = await workers_hub_service.verificar_lista_69b(
            rfc=rfc,
            empresa_id=x_empresa_id
        )

        return {
            "success": result.success,
            "rfc": rfc,
            "resultado": result.resultado,
            "error": result.error
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando 69-B: {e}")
        raise HTTPException(status_code=500, detail=str(e))
