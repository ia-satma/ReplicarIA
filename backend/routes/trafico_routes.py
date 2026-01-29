"""
Tráfico.IA - Rutas API para Sistema de Monitoreo de Proyectos
Endpoints para gestión de alertas, métricas y configuración del monitoreo
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

# Auth dependency for protected routes
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

trafico_service = None


def init_trafico_service(db=None):
    """Inicializa el servicio de Tráfico.IA con la base de datos."""
    global trafico_service
    from services.trafico_ia_service import TraficoIAService
    trafico_service = TraficoIAService(db=db)
    logger.info("🚦 Tráfico.IA: Rutas inicializadas")
    return trafico_service


def get_trafico_service():
    """Obtiene la instancia del servicio de Tráfico.IA."""
    global trafico_service
    if trafico_service is None:
        from services.trafico_ia_service import trafico_ia_service
        trafico_service = trafico_ia_service
    return trafico_service


class ConfiguracionRequest(BaseModel):
    """Request para actualizar configuración del monitoreo."""
    frecuencia_monitoreo_minutos: Optional[int] = Field(None, ge=5, le=1440, description="Frecuencia de monitoreo en minutos (5-1440)")
    dias_inactividad_alerta: Optional[int] = Field(None, ge=1, le=30, description="Días sin actividad para generar alerta")
    dias_vencimiento_alerta: Optional[int] = Field(None, ge=1, le=30, description="Días antes de vencimiento para alertar")
    emails_habilitados: Optional[bool] = Field(None, description="Habilitar/deshabilitar emails automáticos")
    destinatarios_alertas: Optional[List[str]] = Field(None, description="Lista de emails para alertas")
    horario_inicio: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="Hora inicio monitoreo (HH:MM)")
    horario_fin: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="Hora fin monitoreo (HH:MM)")


class EnviarResumenRequest(BaseModel):
    """Request para enviar resumen manual."""
    destinatario: Optional[str] = Field(None, description="Email del destinatario (opcional)")


class ResolverAlertaRequest(BaseModel):
    """Request para resolver una alerta."""
    alerta_id: str = Field(..., description="ID de la alerta a resolver")


@router.get("/status")
async def obtener_status():
    """
    Obtiene el estado actual del sistema de monitoreo Tráfico.IA.
    
    Retorna información sobre:
    - Estado del servicio (activo/inactivo)
    - Última ejecución del monitoreo
    - Configuración actual
    - Métricas generales
    """
    try:
        service = get_trafico_service()
        status = service.obtener_status()
        logger.info("🚦 Tráfico.IA: Status consultado")
        return status
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error obteniendo status: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo status: {str(e)}")


@router.get("/alertas")
async def obtener_alertas(
    solo_activas: bool = True,
    limite: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista de alertas del sistema.
    
    Parámetros:
    - solo_activas: Si es True, solo retorna alertas no resueltas
    - limite: Número máximo de alertas a retornar
    
    Tipos de alertas:
    - proyecto_inactivo: Proyectos sin actividad por X días
    - entregable_proximo: Entregables próximos a vencer
    - candado_pendiente: Checkpoints pendientes de aprobación
    - cambio_calificacion: Cambios en calificaciones de agentes
    - vencimiento_critico: Proyectos vencidos
    - fase_bloqueada: Fases bloqueadas por candados
    """
    try:
        service = get_trafico_service()
        alertas = service.obtener_alertas(solo_activas=solo_activas, limite=limite)
        logger.info(f"🚦 Tráfico.IA: {len(alertas)} alertas consultadas")
        return {
            "alertas": alertas,
            "total": len(alertas),
            "solo_activas": solo_activas
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")


@router.get("/metricas")
async def obtener_metricas(current_user: dict = Depends(get_current_user)):
    """
    Obtiene métricas detalladas del sistema de monitoreo.
    
    Retorna:
    - Resumen general de métricas
    - Total de alertas y alertas activas
    - Alertas agrupadas por tipo
    - Alertas agrupadas por prioridad
    """
    try:
        service = get_trafico_service()
        metricas = service.obtener_metricas()
        logger.info("🚦 Tráfico.IA: Métricas consultadas")
        return metricas
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")


@router.post("/configurar")
async def configurar_monitoreo(config: ConfiguracionRequest, current_user: dict = Depends(get_current_user)):
    """
    Configura los parámetros del sistema de monitoreo.
    
    Parámetros configurables:
    - frecuencia_monitoreo_minutos: Cada cuántos minutos revisar proyectos
    - dias_inactividad_alerta: Días sin actividad para alertar
    - dias_vencimiento_alerta: Días antes de vencimiento para alertar
    - emails_habilitados: Activar/desactivar emails automáticos
    - destinatarios_alertas: Lista de emails para recibir alertas
    - horario_inicio/fin: Horario de operación del monitoreo
    """
    try:
        service = get_trafico_service()
        config_dict = config.model_dump(exclude_none=True)
        
        if not config_dict:
            raise HTTPException(status_code=400, detail="No se proporcionaron parámetros de configuración")
        
        resultado = service.configurar(config_dict)
        logger.info(f"🚦 Tráfico.IA: Configuración actualizada: {list(config_dict.keys())}")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error configurando: {e}")
        raise HTTPException(status_code=500, detail=f"Error configurando: {str(e)}")


@router.post("/enviar-resumen")
async def enviar_resumen_manual(request: EnviarResumenRequest, current_user: dict = Depends(get_current_user)):
    """
    Envía un resumen manual de alertas y métricas por email.
    
    Útil para:
    - Obtener un snapshot del estado actual
    - Enviar reportes a supervisores
    - Verificar que el sistema de emails funciona
    """
    try:
        service = get_trafico_service()
        resultado = await service.enviar_resumen_diario(destinatario=request.destinatario)
        
        if resultado.get("success"):
            logger.info(f"🚦 Tráfico.IA: Resumen enviado a {resultado.get('destinatario')}")
            return {
                "success": True,
                "mensaje": f"Resumen enviado exitosamente a {resultado.get('destinatario')}"
            }
        else:
            error = resultado.get("error", "Error desconocido")
            logger.warning(f"⚠️ Tráfico.IA: No se pudo enviar resumen: {error}")
            return {
                "success": False,
                "error": error
            }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error enviando resumen: {e}")
        raise HTTPException(status_code=500, detail=f"Error enviando resumen: {str(e)}")


@router.post("/ejecutar-monitoreo")
async def ejecutar_monitoreo_manual(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """
    Ejecuta un ciclo de monitoreo manualmente.
    
    Útil para:
    - Pruebas del sistema
    - Forzar una revisión inmediata
    - Verificar detección de alertas
    """
    try:
        service = get_trafico_service()
        resultado = await service.ejecutar_monitoreo()
        logger.info(f"🚦 Tráfico.IA: Monitoreo manual ejecutado - {resultado.get('alertas_nuevas', 0)} alertas")
        return {
            "success": True,
            "resultado": resultado
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error en monitoreo manual: {e}")
        raise HTTPException(status_code=500, detail=f"Error en monitoreo: {str(e)}")


@router.post("/iniciar")
async def iniciar_scheduler(current_user: dict = Depends(get_current_user)):
    """
    Inicia el scheduler de monitoreo automático.
    
    El scheduler ejecutará el monitoreo según la frecuencia configurada
    durante el horario de operación definido.
    """
    try:
        service = get_trafico_service()
        await service.iniciar()
        logger.info("🚦 Tráfico.IA: Scheduler iniciado via API")
        return {
            "success": True,
            "mensaje": "Scheduler de monitoreo iniciado",
            "configuracion": service.configuracion
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error iniciando scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando scheduler: {str(e)}")


@router.post("/detener")
async def detener_scheduler(current_user: dict = Depends(get_current_user)):
    """
    Detiene el scheduler de monitoreo automático.
    """
    try:
        service = get_trafico_service()
        await service.detener()
        logger.info("🚦 Tráfico.IA: Scheduler detenido via API")
        return {
            "success": True,
            "mensaje": "Scheduler de monitoreo detenido"
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error deteniendo scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error deteniendo scheduler: {str(e)}")


@router.post("/alertas/resolver")
async def resolver_alerta(request: ResolverAlertaRequest, current_user: dict = Depends(get_current_user)):
    """
    Marca una alerta como resuelta.
    
    Las alertas resueltas se mantienen en el historial pero
    no aparecen en las consultas de alertas activas.
    """
    try:
        service = get_trafico_service()
        resultado = service.resolver_alerta(request.alerta_id)
        
        if resultado:
            logger.info(f"🚦 Tráfico.IA: Alerta {request.alerta_id} resuelta")
            return {
                "success": True,
                "mensaje": f"Alerta {request.alerta_id} marcada como resuelta"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alerta {request.alerta_id} no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error resolviendo alerta: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolviendo alerta: {str(e)}")


@router.post("/alertas/marcar-leida/{alerta_id}")
async def marcar_alerta_leida(alerta_id: str, current_user: dict = Depends(get_current_user)):
    """
    Marca una alerta como leída.
    """
    try:
        service = get_trafico_service()
        resultado = service.marcar_alerta_leida(alerta_id)
        
        if resultado:
            return {"success": True, "mensaje": f"Alerta {alerta_id} marcada como leída"}
        else:
            raise HTTPException(status_code=404, detail=f"Alerta {alerta_id} no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error marcando alerta: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/reiniciar-metricas")
async def reiniciar_metricas_diarias(current_user: dict = Depends(get_current_user)):
    """
    Reinicia los contadores de métricas diarias.
    
    Normalmente esto se hace automáticamente a medianoche,
    pero puede ejecutarse manualmente si es necesario.
    """
    try:
        service = get_trafico_service()
        service.reiniciar_metricas_diarias()
        logger.info("🚦 Tráfico.IA: Métricas diarias reiniciadas via API")
        return {
            "success": True,
            "mensaje": "Métricas diarias reiniciadas"
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error reiniciando métricas: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/dashboard")
async def obtener_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Obtiene datos consolidados para el dashboard de Tráfico.IA.
    
    Combina status, métricas y alertas recientes en una sola respuesta
    optimizada para visualización en frontend.
    """
    try:
        service = get_trafico_service()
        
        status = service.obtener_status()
        metricas = service.obtener_metricas()
        alertas = service.obtener_alertas(solo_activas=True, limite=10)
        
        alertas_criticas = len([a for a in alertas if a.get("prioridad") == "critica"])
        alertas_altas = len([a for a in alertas if a.get("prioridad") == "alta"])
        
        return {
            "status": {
                "activo": status.get("activo", False),
                "ultima_ejecucion": status.get("ultima_ejecucion"),
                "version": status.get("version", "1.0.0")
            },
            "resumen": {
                "proyectos_monitoreados": metricas.get("resumen", {}).get("proyectos_monitoreados", 0),
                "alertas_activas": metricas.get("alertas_activas", 0),
                "alertas_criticas": alertas_criticas,
                "alertas_altas": alertas_altas,
                "emails_enviados_hoy": metricas.get("resumen", {}).get("emails_enviados_hoy", 0)
            },
            "alertas_recientes": alertas[:5],
            "distribucion_alertas": {
                "por_tipo": metricas.get("alertas_por_tipo", {}),
                "por_prioridad": metricas.get("alertas_por_prioridad", {})
            },
            "configuracion": status.get("configuracion", {})
        }
    except Exception as e:
        logger.error(f"❌ Tráfico.IA: Error obteniendo dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo dashboard: {str(e)}")
