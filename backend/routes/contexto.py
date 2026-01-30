"""
API Routes para el Contexto Global - Revisar.IA

Endpoints para acceder al contexto normativo, tipologías, umbrales y POE.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List

import sys
sys.path.insert(0, '..')

from context import (
    CONTEXTO_GLOBAL,
    CONTEXTO_NORMATIVO,
    TIPOLOGIAS_SERVICIO,
    UMBRALES_REVISION_HUMANA,
    POE_FASES,
    obtener_normativa,
    obtener_tipologia,
    obtener_config_fase,
    requiere_revision_humana,
    es_candado_duro,
    get_bloqueos_fase,
    listar_fases,
    listar_tipologias,
    contexto_service
)

router = APIRouter(prefix="/api/contexto", tags=["contexto"])


@router.get("")
async def get_contexto_global():
    """Obtiene el contexto global completo."""
    return {
        "normativo_keys": list(CONTEXTO_NORMATIVO.keys()),
        "tipologias_count": len(TIPOLOGIAS_SERVICIO),
        "fases_count": len(POE_FASES),
        "umbrales_monto": UMBRALES_REVISION_HUMANA["por_monto"]["umbral_obligatorio"],
        "status": "ok"
    }


@router.get("/normativo")
async def get_normativa_fiscal(ley: Optional[str] = None, articulo: Optional[str] = None):
    """
    Obtiene la normativa fiscal.
    
    Args:
        ley: CFF, LISR, NOM_151, RMF (opcional)
        articulo: artículo específico (opcional)
    """
    if ley is None:
        return CONTEXTO_NORMATIVO
    
    result = obtener_normativa(ley, articulo)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Normativa no encontrada: {ley}/{articulo}")
    return result


@router.get("/tipologias")
async def get_tipologias():
    """Lista todas las tipologías de servicio disponibles."""
    return {
        "tipologias": list(TIPOLOGIAS_SERVICIO.keys()),
        "detalle": {
            codigo: {
                "nombre": tipologia["nombre"],
                "riesgo_fiscal_inherente": tipologia["riesgo_fiscal_inherente"],
                "revision_humana_obligatoria": tipologia.get("revision_humana_obligatoria", False)
            }
            for codigo, tipologia in TIPOLOGIAS_SERVICIO.items()
        }
    }


@router.get("/tipologias/{codigo}")
async def get_tipologia_detalle(codigo: str):
    """Obtiene el detalle de una tipología específica."""
    tipologia = obtener_tipologia(codigo)
    if tipologia is None:
        raise HTTPException(status_code=404, detail=f"Tipología no encontrada: {codigo}")
    return tipologia


@router.get("/fases")
async def get_fases():
    """Lista todas las fases POE."""
    return {
        "fases": listar_fases(),
        "detalle": {
            fase: {
                "nombre": config["nombre"],
                "objetivo": config["objetivo"],
                "es_candado_duro": config.get("es_candado_duro", False),
                "agentes_obligatorios": config.get("agentes_obligatorios", [])
            }
            for fase, config in POE_FASES.items()
        }
    }


@router.get("/fases/{fase}")
async def get_fase_detalle(fase: str):
    """Obtiene el detalle de una fase específica."""
    config = obtener_config_fase(fase)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Fase no encontrada: {fase}")
    return config


@router.get("/umbrales")
async def get_umbrales():
    """Obtiene los umbrales de revisión humana."""
    return UMBRALES_REVISION_HUMANA


@router.post("/evaluar-revision-humana")
async def evaluar_revision_humana_endpoint(
    proyecto: Dict[str, Any],
    risk_score: float,
    proveedor: Dict[str, Any]
):
    """
    Evalúa si un proyecto requiere revisión humana obligatoria.
    
    Body:
    {
        "proyecto": {"monto": 6000000, "tipologia": "MARKETING_BRANDING"},
        "risk_score": 65,
        "proveedor": {"tipo_relacion": "TERCERO_INDEPENDIENTE", "alerta_efos": false}
    }
    """
    resultado = requiere_revision_humana(proyecto, risk_score, proveedor)
    return resultado.to_dict()


@router.get("/agente/{agente}/fase/{fase}")
async def get_contexto_agente(agente: str, fase: str, tipologia: Optional[str] = None):
    """
    Obtiene el contexto específico para un agente en una fase.
    
    Útil para preparar el prompt de los agentes IA.
    """
    contexto = contexto_service.get_contexto_para_agente(agente, fase, tipologia)
    return contexto


@router.post("/validar-documentos")
async def validar_documentos_fase_endpoint(fase: str, documentos_presentes: List[str]):
    """
    Valida si los documentos presentes cumplen con los mínimos de una fase.
    
    Body:
    {
        "fase": "F6",
        "documentos_presentes": ["MATRIZ_MATERIALIDAD", "CONTRATO", "VBC_FISCAL"]
    }
    """
    resultado = contexto_service.validar_documentos_fase(fase, documentos_presentes)
    return resultado


@router.post("/puede-avanzar")
async def puede_avanzar_endpoint(
    fase_actual: str,
    deliberaciones_agentes: Dict[str, str],
    documentos_presentes: List[str]
):
    """
    Evalúa si un proyecto puede avanzar de fase.
    
    Body:
    {
        "fase_actual": "F0",
        "deliberaciones_agentes": {"A1_SPONSOR": "APROBAR", "A3_FISCAL": "APROBAR"},
        "documentos_presentes": ["SIB_BEE", "EVALUACION_RIESGO"]
    }
    """
    resultado = contexto_service.puede_avanzar_fase(
        fase_actual, deliberaciones_agentes, documentos_presentes
    )
    return resultado


@router.get("/candados-duros")
async def get_candados_duros():
    """Obtiene las fases que son candados duros."""
    from context import get_candados_duros
    candados = get_candados_duros()
    return {
        "candados_duros": candados,
        "detalle": {
            fase: POE_FASES[fase].get("candado_descripcion", "")
            for fase in candados
        }
    }
