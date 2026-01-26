"""
Defense Files - Módulo de Integración con Agentes
Sistema de documentación automática para expedientes de defensa Revisar.IA

Este módulo proporciona herramientas para que los agentes de IA
documenten automáticamente sus acciones en los expedientes de defensa.
"""
from .decorators import documentar_accion, obtener_defense_file_id
from .agent_helper import AgentDocumentor
from .agent_integration import (
    FacturarIADocumentor,
    BibliotecaIADocumentor,
    RevisarIADocumentor,
    TraficoIADocumentor,
    DisenarIADocumentor
)

__all__ = [
    "documentar_accion",
    "obtener_defense_file_id",
    "AgentDocumentor",
    "FacturarIADocumentor",
    "BibliotecaIADocumentor",
    "RevisarIADocumentor",
    "TraficoIADocumentor",
    "DisenarIADocumentor"
]

__version__ = "1.0.0"
