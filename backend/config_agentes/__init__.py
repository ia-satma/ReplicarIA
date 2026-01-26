"""
Índice de Configuraciones de Agentes - Revisar.IA
Exporta todas las configuraciones y proporciona funciones auxiliares
"""

from typing import Dict, Any, List, Optional

from .a1_sponsor import A1_SPONSOR_CONFIG
from .a2_pmo import A2_PMO_CONFIG
from .a3_fiscal import A3_FISCAL_CONFIG
from .a4_legal import A4_LEGAL_CONFIG
from .a5_finanzas import A5_FINANZAS_CONFIG
from .a6_proveedor import A6_PROVEEDOR_CONFIG
from .a7_defensa import A7_DEFENSA_CONFIG
from .a8_auditor import A8_AUDITOR_CONFIG
from .knowledge_base import KNOWLEDGE_BASE_CONFIG
from .archivo import ARCHIVO_CONFIG

AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "A1_ESTRATEGIA": A1_SPONSOR_CONFIG,
    "A2_PMO": A2_PMO_CONFIG,
    "A3_FISCAL": A3_FISCAL_CONFIG,
    "A4_LEGAL": A4_LEGAL_CONFIG,
    "A5_FINANZAS": A5_FINANZAS_CONFIG,
    "A6_PROVEEDOR": A6_PROVEEDOR_CONFIG,
    "A7_DEFENSA": A7_DEFENSA_CONFIG,
    "A8_AUDITOR": A8_AUDITOR_CONFIG,
    "KNOWLEDGE_BASE": KNOWLEDGE_BASE_CONFIG,
    "ARCHIVO": ARCHIVO_CONFIG
}


def get_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de un agente específico.
    
    Args:
        agent_id: ID del agente (ej: "A3_FISCAL")
        
    Returns:
        Configuración del agente o None si no existe
    """
    return AGENT_CONFIGS.get(agent_id)


def get_agentes_para_fase(fase: str) -> List[Dict[str, Any]]:
    """
    Obtiene todos los agentes que participan en una fase específica.
    
    Args:
        fase: Fase del POE (ej: "F6")
        
    Returns:
        Lista de configuraciones de agentes que participan en esa fase
    """
    return [
        config for config in AGENT_CONFIGS.values()
        if fase in config.get("fases_participacion", [])
    ]


def get_agentes_que_bloquean() -> List[Dict[str, Any]]:
    """
    Obtiene todos los agentes que pueden bloquear el avance de un proyecto.
    
    Returns:
        Lista de configuraciones de agentes con puede_bloquear_avance=True
    """
    return [
        config for config in AGENT_CONFIGS.values()
        if config.get("puede_bloquear_avance", False)
    ]


def get_agentes_que_emiten_vbc() -> List[Dict[str, Any]]:
    """
    Obtiene todos los agentes que pueden emitir Visto Bueno Crítico (VBC).
    
    Returns:
        Lista de configuraciones de agentes con emite_vbc=True
    """
    return [
        config for config in AGENT_CONFIGS.values()
        if config.get("emite_vbc", False)
    ]


def get_normativa_requerida_por_agente(agent_id: str) -> List[str]:
    """
    Obtiene la lista de normativa que un agente necesita conocer.
    
    Args:
        agent_id: ID del agente
        
    Returns:
        Lista de IDs de normativa relevante
    """
    config = get_agent_config(agent_id)
    if config:
        return config.get("normativa_relevante", [])
    return []


def get_output_schema(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el schema de output estructurado de un agente.
    
    Args:
        agent_id: ID del agente
        
    Returns:
        Schema de output o None si no existe
    """
    config = get_agent_config(agent_id)
    if config:
        return config.get("output_schema")
    return None


def get_contexto_requerido(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los campos de contexto que un agente necesita recibir.
    
    Args:
        agent_id: ID del agente
        
    Returns:
        Dict con campos obligatorio, deseable, no_necesita
    """
    config = get_agent_config(agent_id)
    if config:
        return config.get("contexto_requerido")
    return None


def listar_todos_los_agentes() -> List[str]:
    """
    Lista todos los IDs de agentes disponibles.
    
    Returns:
        Lista de IDs de agentes
    """
    return list(AGENT_CONFIGS.keys())


def get_plantilla_respuesta(agent_id: str) -> Optional[str]:
    """
    Obtiene la plantilla de respuesta de un agente.
    
    Args:
        agent_id: ID del agente
        
    Returns:
        Plantilla Handlebars o None
    """
    config = get_agent_config(agent_id)
    if config:
        return config.get("plantilla_respuesta")
    return None


__all__ = [
    "AGENT_CONFIGS",
    "A1_SPONSOR_CONFIG",
    "A2_PMO_CONFIG", 
    "A3_FISCAL_CONFIG",
    "A4_LEGAL_CONFIG",
    "A5_FINANZAS_CONFIG",
    "A6_PROVEEDOR_CONFIG",
    "A7_DEFENSA_CONFIG",
    "A8_AUDITOR_CONFIG",
    "KNOWLEDGE_BASE_CONFIG",
    "ARCHIVO_CONFIG",
    "get_agent_config",
    "get_agentes_para_fase",
    "get_agentes_que_bloquean",
    "get_agentes_que_emiten_vbc",
    "get_normativa_requerida_por_agente",
    "get_output_schema",
    "get_contexto_requerido",
    "listar_todos_los_agentes",
    "get_plantilla_respuesta"
]
