"""
Agents module for Revisar.IA Multi-Agent System.
Contains specialized autonomous agents that complement the main workflow.

Includes:
- A1-A6: Agentes principales (configurados en config/)
- A7_DEFENSA: Agente de Defense File
- SUB_TIPIFICACION: Subagente de clasificación
- SUB_MATERIALIDAD: Subagente de monitoreo de materialidad
- SUB_RIESGOS_ESPECIALES: Subagente de detección de riesgos
"""

from .strategy_agent import StrategyAgent, strategy_agent
from .pmo_integration import (
    validate_pmo_response,
    PMOSafetyLayer,
    pmo_safety_layer
)

from .sub_tipificacion import (
    SUB_TIPIFICACION_CONFIG,
    clasificar_proyecto,
    TIPOLOGIA_KEYWORDS,
    TIPOLOGIAS_REVISION_HUMANA,
    TIPOLOGIAS_ALTO_ESCRUTINIO,
    CHECKLIST_POR_TIPOLOGIA
)

from .sub_materialidad import (
    SUB_MATERIALIDAD_CONFIG,
    evaluar_materialidad,
    verificar_umbral_vbc,
    UMBRAL_VBC
)

from .sub_riesgos_especiales import (
    SUB_RIESGOS_ESPECIALES_CONFIG,
    detectar_riesgos,
    UMBRAL_MONTO_ALTO,
    UMBRAL_TP_REQUERIDO
)

from .a7_defensa import (
    A7_DEFENSA_CONFIG,
    evaluar_defendibilidad,
    DOCUMENTOS_CLAVE
)

SUBAGENT_CONFIGS = {
    "SUB_TIPIFICACION": SUB_TIPIFICACION_CONFIG,
    "SUB_MATERIALIDAD": SUB_MATERIALIDAD_CONFIG,
    "SUB_RIESGOS_ESPECIALES": SUB_RIESGOS_ESPECIALES_CONFIG,
    "A7_DEFENSA": A7_DEFENSA_CONFIG
}


def get_subagent_config(agent_id: str):
    """Obtiene la configuración de un subagente"""
    return SUBAGENT_CONFIGS.get(agent_id)


def get_agentes_para_fase(fase: str) -> list:
    """Obtiene los agentes que participan en una fase específica"""
    return [
        {"id": agent_id, **config}
        for agent_id, config in SUBAGENT_CONFIGS.items()
        if fase in config.get("fases_participacion", [])
    ]


def get_subagentes() -> list:
    """Obtiene solo los subagentes (SUB_*)"""
    return [
        {"id": agent_id, **config}
        for agent_id, config in SUBAGENT_CONFIGS.items()
        if agent_id.startswith("SUB_")
    ]


def get_agentes_que_bloquean() -> list:
    """Obtiene los agentes que pueden bloquear avance"""
    return [
        {"id": agent_id, **config}
        for agent_id, config in SUBAGENT_CONFIGS.items()
        if config.get("puede_bloquear_avance", False)
    ]


__all__ = [
    "StrategyAgent",
    "strategy_agent",
    "validate_pmo_response",
    "PMOSafetyLayer",
    "pmo_safety_layer",
    "SUB_TIPIFICACION_CONFIG",
    "SUB_MATERIALIDAD_CONFIG",
    "SUB_RIESGOS_ESPECIALES_CONFIG",
    "A7_DEFENSA_CONFIG",
    "clasificar_proyecto",
    "evaluar_materialidad",
    "detectar_riesgos",
    "evaluar_defendibilidad",
    "SUBAGENT_CONFIGS",
    "get_subagent_config",
    "get_agentes_para_fase",
    "get_subagentes",
    "get_agentes_que_bloquean"
]
