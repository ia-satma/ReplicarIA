"""
Documentation module for Revisar.IA Platform.

Provides automated documentation for agents, subagents, phases, and capabilities.
"""

from .models import (
    AgentType,
    AgentStatus,
    CapabilityModel,
    ControlModel,
    AgentInventoryItem,
    PhaseModel,
    PillarModel,
    DocumentationSnapshot
)

from .doc_agent import (
    DocAgentService,
    InventoryAgent,
    ExtractionAgent
)

__all__ = [
    "AgentType",
    "AgentStatus",
    "CapabilityModel",
    "ControlModel",
    "AgentInventoryItem",
    "PhaseModel",
    "PillarModel",
    "DocumentationSnapshot",
    "DocAgentService",
    "InventoryAgent",
    "ExtractionAgent"
]
