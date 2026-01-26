"""
Módulo de Contexto Global - Revisar.IA

Exporta todos los componentes del contexto global del sistema.
"""

from .contexto_normativo_fiscal import (
    CONTEXTO_NORMATIVO,
    obtener_normativa,
    obtener_criterios_evaluacion,
    obtener_normativa_por_pilar
)

from .tipologias_servicio import (
    TIPOLOGIAS_SERVICIO,
    obtener_tipologia,
    obtener_riesgo_inherente,
    requiere_revision_humana_por_tipologia,
    obtener_documentos_tipicos,
    obtener_alertas_especiales,
    listar_tipologias,
    obtener_tipologias_alto_riesgo
)

from .umbrales_revision import (
    UMBRALES_REVISION_HUMANA,
    ResultadoRevision,
    requiere_revision_humana,
    es_fase_critica,
    obtener_umbral_monto,
    obtener_umbral_risk_score,
    obtener_tipologias_siempre_humano,
    clasificar_por_risk_score
)

from .poe_fases import (
    POE_FASES,
    obtener_config_fase,
    es_candado_duro,
    get_bloqueos_fase,
    get_agentes_obligatorios,
    get_documentos_minimos,
    get_condicion_avance,
    listar_fases,
    get_candados_duros,
    get_fase_siguiente,
    get_fase_anterior
)

from .contexto_global import (
    CONTEXTO_GLOBAL,
    ContextoGlobalService,
    contexto_service
)

__all__ = [
    "CONTEXTO_NORMATIVO",
    "obtener_normativa",
    "obtener_criterios_evaluacion",
    "obtener_normativa_por_pilar",
    "TIPOLOGIAS_SERVICIO",
    "obtener_tipologia",
    "obtener_riesgo_inherente",
    "requiere_revision_humana_por_tipologia",
    "obtener_documentos_tipicos",
    "obtener_alertas_especiales",
    "listar_tipologias",
    "obtener_tipologias_alto_riesgo",
    "UMBRALES_REVISION_HUMANA",
    "ResultadoRevision",
    "requiere_revision_humana",
    "es_fase_critica",
    "obtener_umbral_monto",
    "obtener_umbral_risk_score",
    "obtener_tipologias_siempre_humano",
    "clasificar_por_risk_score",
    "POE_FASES",
    "obtener_config_fase",
    "es_candado_duro",
    "get_bloqueos_fase",
    "get_agentes_obligatorios",
    "get_documentos_minimos",
    "get_condicion_avance",
    "listar_fases",
    "get_candados_duros",
    "get_fase_siguiente",
    "get_fase_anterior",
    "CONTEXTO_GLOBAL",
    "ContextoGlobalService",
    "contexto_service"
]
