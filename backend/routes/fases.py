"""
Rutas de API para Gestión de Fases - Revisar.IA

Endpoints para verificar estado de fases, candados duros y avance de proyectos.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from services.fase_service import (
    ORDEN_FASES,
    CANDADOS_DUROS,
    FASES_CONFIG,
    puede_avanzar_fase,
    avanzar_fase,
    get_estado_proyecto,
    get_resumen_candados,
    verificar_candado_f2,
    verificar_candado_f6,
    verificar_candado_f8,
    get_config_fase,
    get_siguiente_fase
)

from middleware.candados_middleware import (
    verificar_candado_antes_de_avanzar,
    CandadoBlockedException,
    candado_requerido,
    obtener_acciones_para_bloqueos
)

router = APIRouter(prefix="/api/fases", tags=["Fases y Candados Revisar.IA"])


class ProyectoInput(BaseModel):
    id: str
    fase_actual: str = "F0"
    monto: float = 0
    risk_score_total: int = 0
    tipologia: str = "CONSULTORIA_MACRO_MERCADO"
    revision_humana_obtenida: bool = False


class ContextoInput(BaseModel):
    fases_completadas: List[str] = []
    deliberaciones: Dict[str, Dict[str, Dict[str, Any]]] = {}
    defense_file: Dict[str, Any] = {}
    proveedor: Dict[str, Any] = {}
    documentos: List[Dict[str, Any]] = []


class VerificarFaseRequest(BaseModel):
    proyecto: ProyectoInput
    contexto: ContextoInput


@router.get("")
async def get_todas_fases() -> Dict[str, Any]:
    """Lista todas las fases del POE con su configuración"""
    return {
        "orden": ORDEN_FASES,
        "candados_duros": CANDADOS_DUROS,
        "fases": FASES_CONFIG
    }


@router.get("/candados")
async def get_candados_info() -> Dict[str, Any]:
    """Obtiene información detallada de los tres candados duros"""
    return get_resumen_candados()


@router.get("/fase/{fase}")
async def get_fase_config(fase: str) -> Dict[str, Any]:
    """Obtiene la configuración de una fase específica"""
    config = get_config_fase(fase.upper())
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Fase '{fase}' no encontrada. Opciones: {ORDEN_FASES}"
        )
    return {
        "fase": fase.upper(),
        "config": config,
        "siguiente": get_siguiente_fase(fase.upper()),
        "es_candado_duro": fase.upper() in CANDADOS_DUROS
    }


@router.post("/verificar")
async def verificar_puede_avanzar(request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Verifica si un proyecto puede avanzar a la siguiente fase.
    
    Evalúa:
    - Deliberaciones de agentes requeridos
    - Candados duros (F2, F6, F8)
    - Requisitos de revisión humana
    """
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    resultado = puede_avanzar_fase(proyecto, proyecto["fase_actual"], contexto)
    
    return resultado


@router.post("/avanzar")
async def intentar_avanzar_fase(request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Intenta avanzar el proyecto a la siguiente fase.
    
    Solo avanza si todos los bloqueos están resueltos.
    """
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    resultado = avanzar_fase(proyecto, contexto)
    
    if not resultado["exito"]:
        raise HTTPException(status_code=400, detail=resultado)
    
    return resultado


@router.post("/estado")
async def get_estado_completo(request: VerificarFaseRequest) -> Dict[str, Any]:
    """Obtiene el estado completo del proyecto en el flujo de fases"""
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    return get_estado_proyecto(proyecto, contexto)


@router.post("/validar/iniciar-ejecucion")
async def validar_iniciar_ejecucion(request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Valida si el proyecto puede iniciar ejecución (candado F2).
    
    Este endpoint debe llamarse antes de permitir que el proveedor
    comience trabajos (entrada a F3).
    """
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    try:
        resultado = await verificar_candado_antes_de_avanzar(proyecto, "F2", contexto)
        return {"permitido": True, "fase": "F2", "bloqueos": []}
    except CandadoBlockedException as e:
        raise HTTPException(
            status_code=403, 
            detail={
                "permitido": False,
                "fase": e.fase,
                "bloqueos": e.bloqueos,
                "acciones_requeridas": obtener_acciones_para_bloqueos(e.bloqueos)
            }
        )


@router.post("/validar/emitir-cfdi")
async def validar_emitir_cfdi(request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Valida si el proyecto puede recibir CFDI (candado F6).
    
    Este endpoint debe llamarse antes de permitir la carga
    de facturas al sistema.
    """
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    try:
        resultado = await verificar_candado_antes_de_avanzar(proyecto, "F6", contexto)
        return {"permitido": True, "fase": "F6", "bloqueos": []}
    except CandadoBlockedException as e:
        raise HTTPException(
            status_code=403, 
            detail={
                "permitido": False,
                "fase": e.fase,
                "bloqueos": e.bloqueos,
                "acciones_requeridas": obtener_acciones_para_bloqueos(e.bloqueos)
            }
        )


@router.post("/validar/liberar-pago")
async def validar_liberar_pago(request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Valida si el proyecto puede liberar pago (candado F8).
    
    Este endpoint debe llamarse antes de autorizar cualquier
    transferencia bancaria.
    """
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    try:
        resultado = await verificar_candado_antes_de_avanzar(proyecto, "F8", contexto)
        return {"permitido": True, "fase": "F8", "bloqueos": []}
    except CandadoBlockedException as e:
        raise HTTPException(
            status_code=403, 
            detail={
                "permitido": False,
                "fase": e.fase,
                "bloqueos": e.bloqueos,
                "acciones_requeridas": obtener_acciones_para_bloqueos(e.bloqueos)
            }
        )


@router.post("/candado/{fase}")
async def verificar_candado_especifico(fase: str, request: VerificarFaseRequest) -> Dict[str, Any]:
    """
    Verifica un candado específico (F2, F6 o F8).
    
    Retorna el estado del candado y los bloqueos activos.
    """
    fase_upper = fase.upper()
    if fase_upper not in CANDADOS_DUROS:
        raise HTTPException(
            status_code=400,
            detail=f"'{fase}' no es un candado duro. Opciones: {CANDADOS_DUROS}"
        )
    
    proyecto = request.proyecto.model_dump()
    contexto = request.contexto.model_dump()
    
    if fase_upper == "F2":
        return verificar_candado_f2(proyecto, contexto)
    elif fase_upper == "F6":
        return verificar_candado_f6(proyecto, contexto)
    else:
        return verificar_candado_f8(proyecto, contexto)


