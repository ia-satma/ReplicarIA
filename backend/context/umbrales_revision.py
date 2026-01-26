"""
Umbrales de Revisión Humana - Revisar.IA
Sistema de Auditoría de Intangibles

Este módulo define los umbrales que determinan cuándo un proyecto
requiere revisión humana obligatoria.
"""

from typing import Dict, List, Any, Optional

UMBRALES_REVISION_HUMANA: Dict[str, Any] = {
    
    "por_monto": {
        "umbral_obligatorio": 5000000,
        "descripcion": "Proyectos con monto >= 5 millones MXN requieren revisión humana obligatoria de Fiscal y Legal antes de F2 y F6.",
        "moneda": "MXN"
    },
    
    "por_risk_score": {
        "obligatorio": {
            "umbral": 60,
            "descripcion": "Proyectos con risk_score >= 60 requieren revisión humana obligatoria."
        },
        "discrecional": {
            "rango_min": 40,
            "rango_max": 59,
            "descripcion": "Proyectos con risk_score entre 40-59 quedan a discreción del PMO según tipo de servicio."
        },
        "automatizado": {
            "umbral_max": 39,
            "descripcion": "Proyectos con risk_score < 40 pueden procesarse de forma automatizada, salvo excepciones por tipo."
        }
    },
    
    "por_tipologia": {
        "siempre_humano": [
            "INTRAGRUPO_MANAGEMENT_FEE",
            "REESTRUCTURAS"
        ],
        "descripcion": "Estos tipos de servicio SIEMPRE requieren revisión humana de Fiscal y Legal, independientemente de monto o score."
    },
    
    "por_proveedor": {
        "parte_relacionada": {
            "requiere_revision": True,
            "descripcion": "Cualquier operación con parte relacionada requiere revisión humana adicional y validación de TP."
        },
        "alerta_efos": {
            "requiere_revision": True,
            "descripcion": "Proveedores con alerta EFOS activa requieren revisión humana y análisis de riesgo especial."
        },
        "primera_vez": {
            "requiere_revision": True,
            "umbral_monto": 1000000,
            "descripcion": "Primera operación con un proveedor nuevo por monto > 1M requiere validación adicional."
        }
    },
    
    "fases_criticas": {
        "F2": {
            "descripcion": "Antes de iniciar ejecución",
            "requiere_revision_si": ["monto >= umbral", "risk_score >= 60", "tipologia en siempre_humano", "parte_relacionada"]
        },
        "F6": {
            "descripcion": "Antes de emitir VBC y autorizar pago",
            "requiere_revision_si": ["siempre", "es la puerta antes del compromiso fiscal"]
        }
    }
}


class ResultadoRevision:
    """Resultado del análisis de revisión humana."""
    
    def __init__(self, requiere: bool, razon: Optional[str] = None, razones: Optional[List[str]] = None):
        self.requiere = requiere
        self.razon = razon
        self.razones = razones or []
        if razon and razon not in self.razones:
            self.razones.append(razon)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requiere": self.requiere,
            "razon": self.razon,
            "razones": self.razones
        }


def requiere_revision_humana(
    proyecto: Dict[str, Any],
    risk_score: float,
    proveedor: Dict[str, Any]
) -> ResultadoRevision:
    """
    Determina si un proyecto requiere revisión humana obligatoria.
    
    Args:
        proyecto: Diccionario con datos del proyecto (monto, tipologia, etc.)
        risk_score: Score de riesgo calculado (0-100)
        proveedor: Diccionario con datos del proveedor
    
    Returns:
        ResultadoRevision con la decisión y razones
    """
    razones = []
    
    monto = proyecto.get("monto", 0)
    tipologia = proyecto.get("tipologia", "")
    tipo_relacion = proveedor.get("tipo_relacion", "TERCERO_INDEPENDIENTE")
    alerta_efos = proveedor.get("alerta_efos", False)
    es_primera_vez = proveedor.get("es_primera_operacion", False)
    
    if monto >= UMBRALES_REVISION_HUMANA["por_monto"]["umbral_obligatorio"]:
        razones.append(f"Monto >= {UMBRALES_REVISION_HUMANA['por_monto']['umbral_obligatorio']:,} MXN")
    
    if risk_score >= UMBRALES_REVISION_HUMANA["por_risk_score"]["obligatorio"]["umbral"]:
        razones.append(f"Risk score >= {UMBRALES_REVISION_HUMANA['por_risk_score']['obligatorio']['umbral']}")
    
    if tipologia in UMBRALES_REVISION_HUMANA["por_tipologia"]["siempre_humano"]:
        razones.append(f"Tipología {tipologia} requiere revisión humana obligatoria")
    
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        razones.append(f"Operación con parte relacionada: {tipo_relacion}")
    
    if alerta_efos:
        razones.append("Proveedor con alerta EFOS activa")
    
    if es_primera_vez and monto > UMBRALES_REVISION_HUMANA["por_proveedor"]["primera_vez"]["umbral_monto"]:
        razones.append(f"Primera operación con proveedor nuevo por monto > {UMBRALES_REVISION_HUMANA['por_proveedor']['primera_vez']['umbral_monto']:,} MXN")
    
    if razones:
        return ResultadoRevision(
            requiere=True,
            razon=razones[0],
            razones=razones
        )
    
    return ResultadoRevision(requiere=False)


def es_fase_critica(fase: str) -> bool:
    """
    Determina si una fase es crítica para revisión humana.
    """
    return fase in UMBRALES_REVISION_HUMANA["fases_criticas"]


def obtener_umbral_monto() -> int:
    """
    Obtiene el umbral de monto para revisión humana obligatoria.
    """
    return UMBRALES_REVISION_HUMANA["por_monto"]["umbral_obligatorio"]


def obtener_umbral_risk_score() -> int:
    """
    Obtiene el umbral de risk_score para revisión humana obligatoria.
    """
    return UMBRALES_REVISION_HUMANA["por_risk_score"]["obligatorio"]["umbral"]


def obtener_tipologias_siempre_humano() -> List[str]:
    """
    Obtiene las tipologías que siempre requieren revisión humana.
    """
    return UMBRALES_REVISION_HUMANA["por_tipologia"]["siempre_humano"]


def clasificar_por_risk_score(risk_score: float) -> str:
    """
    Clasifica un proyecto según su risk_score.
    
    Returns:
        "OBLIGATORIO", "DISCRECIONAL", o "AUTOMATIZADO"
    """
    if risk_score >= UMBRALES_REVISION_HUMANA["por_risk_score"]["obligatorio"]["umbral"]:
        return "OBLIGATORIO"
    elif risk_score >= UMBRALES_REVISION_HUMANA["por_risk_score"]["discrecional"]["rango_min"]:
        return "DISCRECIONAL"
    else:
        return "AUTOMATIZADO"
