"""
Middleware de Candados Duros - Revisar.IA
Verifica automáticamente los candados F2, F6, F8 antes de permitir avance de fase.
"""

from fastapi import HTTPException
from functools import wraps
from typing import Callable, Dict, Any, List
import logging

from services.fase_service import (
    verificar_candado_f2,
    verificar_candado_f6,
    verificar_candado_f8
)

logger = logging.getLogger(__name__)

CANDADOS_DUROS = {
    "F2": verificar_candado_f2,
    "F6": verificar_candado_f6,
    "F8": verificar_candado_f8
}


class CandadoBlockedException(Exception):
    """Excepción cuando un candado bloquea el avance"""
    def __init__(self, fase: str, bloqueos: List[str], mensaje: str = None):
        self.fase = fase
        self.bloqueos = bloqueos
        self.mensaje = mensaje or f"Candado {fase} bloquea el avance"
        super().__init__(self.mensaje)


async def verificar_candado_antes_de_avanzar(
    proyecto: Dict[str, Any],
    fase_destino: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Verifica si el proyecto puede avanzar a la fase destino.
    Lanza CandadoBlockedException si hay bloqueos.
    
    Args:
        proyecto: Diccionario con datos del proyecto
        fase_destino: Fase a la que se quiere avanzar (F2, F6, F8, etc.)
        context: Contexto adicional (deliberaciones, documentos, etc.)
    
    Returns:
        dict con puede_avanzar=True si pasa
    
    Raises:
        CandadoBlockedException si hay bloqueos
    """
    
    if fase_destino not in CANDADOS_DUROS:
        return {"puede_avanzar": True, "bloqueos": []}
    
    verificar_candado = CANDADOS_DUROS[fase_destino]
    
    ctx = context or {}
    
    resultado = verificar_candado(proyecto, ctx)
    
    liberado = resultado.get("liberado", False)
    
    if not liberado:
        bloqueos = resultado.get("bloqueos", ["Candado bloqueado"])
        
        logger.warning(
            f"CANDADO {fase_destino} BLOQUEÓ AVANCE - "
            f"Proyecto: {proyecto.get('id')} - "
            f"Bloqueos: {bloqueos}"
        )
        
        raise CandadoBlockedException(
            fase=fase_destino,
            bloqueos=bloqueos,
            mensaje=f"No se puede avanzar a {fase_destino}: {'; '.join(bloqueos)}"
        )
    
    logger.info(
        f"CANDADO {fase_destino} VERIFICADO OK - "
        f"Proyecto: {proyecto.get('id')}"
    )
    
    return {"puede_avanzar": True, "bloqueos": []}


def candado_requerido(fase_destino: str):
    """
    Decorador para proteger endpoints que avanzan a fases con candado.
    
    Uso:
        @router.post("/proyectos/{id}/avanzar-a-f2")
        @candado_requerido("F2")
        async def avanzar_a_f2(id: str, proyecto: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            proyecto = kwargs.get('proyecto')
            context = kwargs.get('context', {})
            
            if proyecto:
                try:
                    await verificar_candado_antes_de_avanzar(proyecto, fase_destino, context)
                except CandadoBlockedException as e:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "CANDADO_BLOQUEADO",
                            "fase": e.fase,
                            "bloqueos": e.bloqueos,
                            "mensaje": e.mensaje
                        }
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def obtener_acciones_para_bloqueos(bloqueos: List[str]) -> List[str]:
    """Mapea bloqueos a acciones requeridas"""
    acciones = []
    
    for bloqueo in bloqueos:
        bloqueo_lower = bloqueo.lower()
        
        if "f0" in bloqueo_lower and "completada" in bloqueo_lower:
            acciones.append("Completar fase F0 (Aprobación BEE)")
        elif "f1" in bloqueo_lower and "completada" in bloqueo_lower:
            acciones.append("Completar fase F1 (SOW)")
        elif "f5" in bloqueo_lower and "completada" in bloqueo_lower:
            acciones.append("Completar fase F5 (Aceptación técnica)")
        elif "f6" in bloqueo_lower and "completada" in bloqueo_lower:
            acciones.append("Completar fase F6 (VBC)")
        elif "f7" in bloqueo_lower and "completada" in bloqueo_lower:
            acciones.append("Completar fase F7 (Auditoría interna)")
        elif "presupuesto" in bloqueo_lower:
            acciones.append("Confirmar presupuesto del proyecto con Finanzas (A5)")
        elif "revisión humana" in bloqueo_lower:
            acciones.append("Obtener aprobación de revisión humana")
        elif "materialidad" in bloqueo_lower:
            acciones.append("Completar matriz de materialidad al 80% mínimo")
        elif "vbc fiscal" in bloqueo_lower:
            acciones.append("Obtener VBC (Visto Bueno de Cumplimiento) de Fiscal (A3)")
        elif "vbc legal" in bloqueo_lower:
            acciones.append("Obtener VBC (Visto Bueno de Cumplimiento) de Legal (A4)")
        elif "cfdi" in bloqueo_lower and "genéric" in bloqueo_lower:
            acciones.append("Asegurar que el CFDI tenga descripción específica del servicio")
        elif "cfdi" in bloqueo_lower:
            acciones.append("Cargar CFDI del proveedor")
        elif "3-way" in bloqueo_lower or "match" in bloqueo_lower:
            acciones.append("Verificar que diferencia de 3-way match sea menor a 5%")
        elif "tp" in bloqueo_lower or "transferencia" in bloqueo_lower:
            acciones.append("Agregar estudio de Precios de Transferencia vigente")
        elif "a1" in bloqueo_lower and "sponsor" in bloqueo_lower:
            acciones.append("Obtener aprobación de A1-Sponsor")
        elif "a3" in bloqueo_lower and "fiscal" in bloqueo_lower:
            acciones.append("Obtener aprobación de A3-Fiscal")
        elif "a4" in bloqueo_lower and "legal" in bloqueo_lower:
            acciones.append("Obtener aprobación de A4-Legal")
        elif "a5" in bloqueo_lower and "finanzas" in bloqueo_lower:
            acciones.append("Obtener validación de A5-Finanzas")
        else:
            acciones.append(f"Resolver: {bloqueo}")
    
    return list(set(acciones))
