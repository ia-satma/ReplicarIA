"""
Rutas API para verificación de lista 69-B del SAT.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from services.verificacion_69b import (
    verificar_rfc,
    verificar_multiples,
    obtener_estadisticas,
    buscar_por_nombre
)

router = APIRouter(prefix="/api/lista-69b", tags=["Lista 69-B"])


class VerificacionRequest(BaseModel):
    rfc: str
    contexto: Optional[str] = None
    empresa_id: Optional[int] = None
    proveedor_id: Optional[int] = None


class VerificacionMultipleRequest(BaseModel):
    rfcs: List[str]


@router.get("/verificar/{rfc}")
async def verificar_rfc_endpoint(
    rfc: str,
    contexto: str = Query(None, description="Contexto: alta_proveedor, verificacion_cfdi, dd_proveedor")
):
    """
    Verifica un RFC contra la lista 69-B del SAT.
    
    Retorna:
    - encontrado: Si el RFC está en la lista
    - situacion: Definitivo, Presunto, Desvirtuado, Sentencia Favorable
    - nivel_riesgo: CRITICO, ALTO, BAJO, OK
    - accion_recomendada: Qué hacer según el resultado
    """
    if not rfc or len(rfc) < 12:
        raise HTTPException(status_code=400, detail="RFC inválido. Debe tener 12-13 caracteres.")
    
    resultado = verificar_rfc(rfc, contexto=contexto)
    return resultado


@router.post("/verificar")
async def verificar_rfc_post(request: VerificacionRequest):
    """Verifica un RFC (método POST para más opciones)"""
    resultado = verificar_rfc(
        request.rfc,
        contexto=request.contexto,
        empresa_id=request.empresa_id,
        proveedor_id=request.proveedor_id
    )
    return resultado


@router.post("/verificar-multiples")
async def verificar_multiples_endpoint(request: VerificacionMultipleRequest):
    """
    Verifica múltiples RFCs a la vez (máximo 100).
    Útil para verificar todos los proveedores de un proyecto.
    """
    if len(request.rfcs) > 100:
        raise HTTPException(status_code=400, detail="Máximo 100 RFCs por consulta")
    
    resultados = verificar_multiples(request.rfcs)
    
    resumen = {
        'total': len(request.rfcs),
        'en_lista': sum(1 for r in resultados.values() if r['encontrado']),
        'definitivos': sum(1 for r in resultados.values() if r.get('situacion') == 'Definitivo'),
        'presuntos': sum(1 for r in resultados.values() if r.get('situacion') == 'Presunto'),
        'limpios': sum(1 for r in resultados.values() if not r['encontrado'])
    }
    
    return {
        'resumen': resumen,
        'resultados': resultados
    }


@router.get("/estadisticas")
async def estadisticas_endpoint():
    """
    Obtiene estadísticas de la lista 69-B cargada.
    - Total de registros
    - Distribución por situación
    - Fecha de última actualización
    """
    return obtener_estadisticas()


@router.get("/buscar")
async def buscar_endpoint(
    nombre: str = Query(..., min_length=3, description="Nombre a buscar (mínimo 3 caracteres)"),
    limite: int = Query(20, le=100, description="Límite de resultados")
):
    """
    Busca contribuyentes por nombre en la lista 69-B.
    Útil para verificar si un proveedor potencial está en la lista.
    """
    resultados = buscar_por_nombre(nombre, limite)
    return {
        'total_encontrados': len(resultados),
        'resultados': resultados
    }


@router.get("/status")
async def status_endpoint():
    """Verifica el estado del servicio de lista 69-B"""
    try:
        stats = obtener_estadisticas()
        return {
            'status': 'activo',
            'registros_cargados': stats['total_registros'],
            'ultima_actualizacion': stats['ultima_actualizacion'],
            'mensaje': 'Lista 69-B disponible para consultas' if stats['total_registros'] > 0 else 'Lista 69-B vacía - ejecutar ingesta'
        }
    except Exception as e:
        return {
            'status': 'error',
            'mensaje': str(e)
        }
