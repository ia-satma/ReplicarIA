# backend/config/agents_registry.py
"""
FUENTE ÚNICA DE VERDAD - Registro Unificado de Agentes ReplicarIA

Este archivo define TODOS los agentes del sistema. Cualquier otro archivo
que necesite información de agentes DEBE importar de aquí.

Última actualización: 2026-02-02
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel


class AgentType(str, Enum):
    """Tipos de agentes en el sistema"""
    PRINCIPAL = "principal"      # Agentes principales del flujo F0-F9
    ESPECIALIZADO = "especializado"  # Agentes con funciones específicas
    SUBAGENTE = "subagente"      # Subagentes que apoyan a principales


class AgentCategory(str, Enum):
    """Categorías funcionales de agentes"""
    ESTRATEGIA = "estrategia"
    FISCAL = "fiscal"
    FINANZAS = "finanzas"
    LEGAL = "legal"
    OPERACIONES = "operaciones"
    AUDITORIA = "auditoria"
    CONOCIMIENTO = "conocimiento"
    CONTROL = "control"


class AgentConfig(BaseModel):
    """Configuración completa de un agente"""
    id: str
    name: str                    # Nombre de la persona/agente
    role: str                    # Rol funcional
    department: str              # Departamento
    description: str             # Descripción breve
    icon: str                    # Emoji para UI
    color: str                   # Color para UI (tailwind)
    type: AgentType
    category: AgentCategory
    phases: List[str]            # Fases donde participa (F0-F9)
    can_block: bool              # Puede bloquear avance de fase
    blocking_phases: List[str]   # Fases donde puede bloquear
    parent_agent: Optional[str]  # ID del agente padre (para subagentes)
    llm_model: str               # Modelo LLM a usar
    pcloud_folder: Optional[str] # Carpeta en pCloud para RAG


# =============================================================================
# REGISTRO MAESTRO DE AGENTES
# =============================================================================

AGENTS_REGISTRY: Dict[str, AgentConfig] = {

    # =========================================================================
    # AGENTES PRINCIPALES (Flujo F0-F9)
    # =========================================================================

    "A1_SPONSOR": AgentConfig(
        id="A1_SPONSOR",
        name="María Rodríguez",
        role="Sponsor / Evaluador Estratégico",
        department="Dirección Estratégica",
        description="Evalúa razón de negocios y beneficio económico esperado (BEE)",
        icon="🎯",
        color="indigo",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.ESTRATEGIA,
        phases=["F0", "F4", "F5", "F9"],
        can_block=True,
        blocking_phases=["F0"],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A1_ESTRATEGIA"
    ),

    "A2_PMO": AgentConfig(
        id="A2_PMO",
        name="Carlos Mendoza",
        role="Orquestador del Proceso F0-F9",
        department="PMO",
        description="Controla flujo de fases, verifica checklists y candados",
        icon="📋",
        color="blue",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.OPERACIONES,
        phases=["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
        can_block=True,
        blocking_phases=["F2", "F6", "F8"],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A2_PMO"
    ),

    "A3_FISCAL": AgentConfig(
        id="A3_FISCAL",
        name="Laura Sánchez",
        role="Especialista en Cumplimiento Fiscal",
        department="Fiscal",
        description="Evalúa 4 pilares fiscales y emite VBC Fiscal (CFF, LISR, LIVA)",
        icon="⚖️",
        color="purple",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.FISCAL,
        phases=["F0", "F1", "F4", "F6"],
        can_block=True,
        blocking_phases=["F0", "F6"],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A3_FISCAL"
    ),

    "A4_LEGAL": AgentConfig(
        id="A4_LEGAL",
        name="Ana García",
        role="Especialista en Contratos y Trazabilidad",
        department="Legal",
        description="Revisa contratos, SOW y emite VBC Legal",
        icon="📜",
        color="red",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.LEGAL,
        phases=["F1", "F6"],
        can_block=True,
        blocking_phases=["F1", "F6"],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A4_LEGAL"
    ),

    "A5_FINANZAS": AgentConfig(
        id="A5_FINANZAS",
        name="Roberto Sánchez",
        role="Director Financiero / Controller",
        department="Finanzas",
        description="Evalúa proporción económica, presupuesto y 3-way match",
        icon="💰",
        color="emerald",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.FINANZAS,
        phases=["F2", "F4", "F8"],
        can_block=True,
        blocking_phases=["F2", "F8"],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A5_FINANZAS"
    ),

    "A6_PROVEEDOR": AgentConfig(
        id="A6_PROVEEDOR",
        name="Agente Due Diligence",
        role="Validador de Proveedores",
        department="Validación de Proveedores",
        description="Gestiona entregables y evidencias de ejecución del proveedor",
        icon="🔍",
        color="yellow",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.OPERACIONES,
        phases=["F3", "F4", "F5"],
        can_block=False,
        blocking_phases=[],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A6_PROVEEDOR"
    ),

    "A7_DEFENSA": AgentConfig(
        id="A7_DEFENSA",
        name="Laura Vázquez",
        role="Directora de Defense File",
        department="Defensa Fiscal",
        description="Consolida expediente de defensa y evalúa defendibilidad",
        icon="🛡️",
        color="orange",
        type=AgentType.PRINCIPAL,
        category=AgentCategory.AUDITORIA,
        phases=["F6", "F7", "F9"],
        can_block=False,
        blocking_phases=[],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A7_DEFENSA"
    ),

    # =========================================================================
    # AGENTES ESPECIALIZADOS
    # =========================================================================

    "A8_AUDITOR": AgentConfig(
        id="A8_AUDITOR",
        name="Diego Ramírez",
        role="Auditor Documental",
        department="Auditoría Documental",
        description="Verifica estructura y completitud de documentos",
        icon="📊",
        color="cyan",
        type=AgentType.ESPECIALIZADO,
        category=AgentCategory.AUDITORIA,
        phases=["F4", "F6", "F8"],
        can_block=False,
        blocking_phases=[],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="A8_AUDITOR"
    ),

    "KB_CURATOR": AgentConfig(
        id="KB_CURATOR",
        name="Dra. Elena Vázquez",
        role="Curadora de Conocimiento",
        department="Gestión del Conocimiento",
        description="Fuente normativa RAG para todos los agentes",
        icon="📚",
        color="violet",
        type=AgentType.ESPECIALIZADO,
        category=AgentCategory.CONOCIMIENTO,
        phases=[],  # Siempre disponible
        can_block=False,
        blocking_phases=[],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder="KNOWLEDGE_BASE"
    ),

    "DEVILS_ADVOCATE": AgentConfig(
        id="DEVILS_ADVOCATE",
        name="Abogado del Diablo",
        role="Control Interno y Aprendizaje",
        department="Control Interno",
        description="Cuestiona sistemáticamente, detecta patrones de riesgo",
        icon="😈",
        color="gray",
        type=AgentType.ESPECIALIZADO,
        category=AgentCategory.CONTROL,
        phases=[],  # Solo admin
        can_block=False,
        blocking_phases=[],
        parent_agent=None,
        llm_model="claude-sonnet",
        pcloud_folder=None
    ),

    # =========================================================================
    # SUBAGENTES FISCALES (Reportan a A3_FISCAL)
    # =========================================================================

    "S1_TIPIFICACION": AgentConfig(
        id="S1_TIPIFICACION",
        name="Patricia López",
        role="Clasificador de Tipología",
        department="Tipificación",
        description="Asigna tipología correcta al servicio",
        icon="🏷️",
        color="pink",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.FISCAL,
        phases=["F0"],
        can_block=False,
        blocking_phases=[],
        parent_agent="A3_FISCAL",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S2_MATERIALIDAD": AgentConfig(
        id="S2_MATERIALIDAD",
        name="Fernando Ruiz",
        role="Especialista en Materialidad",
        department="Materialidad",
        description="Verifica evidencias de ejecución (Art. 69-B CFF)",
        icon="📎",
        color="teal",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.FISCAL,
        phases=["F5", "F6"],
        can_block=False,
        blocking_phases=[],
        parent_agent="A3_FISCAL",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S3_RIESGOS": AgentConfig(
        id="S3_RIESGOS",
        name="Gabriela Vega",
        role="Detector de Riesgos Especiales",
        department="Riesgos Especiales",
        description="Identifica señales EFOS, precios de transferencia, esquemas",
        icon="⚠️",
        color="red",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.FISCAL,
        phases=["F0", "F2", "F6"],
        can_block=False,
        blocking_phases=[],
        parent_agent="A3_FISCAL",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    # =========================================================================
    # SUBAGENTES PMO (Reportan a A2_PMO)
    # =========================================================================

    "S_ANALIZADOR": AgentConfig(
        id="S_ANALIZADOR",
        name="Subagente Analizador",
        role="Análisis de Datos",
        department="PMO",
        description="Extrae y analiza datos de documentos",
        icon="🔬",
        color="blue",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.OPERACIONES,
        phases=[],
        can_block=False,
        blocking_phases=[],
        parent_agent="A2_PMO",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S_CLASIFICADOR": AgentConfig(
        id="S_CLASIFICADOR",
        name="Subagente Clasificador",
        role="Clasificación por Severidad",
        department="PMO",
        description="Clasifica issues por severidad y tipo",
        icon="📁",
        color="blue",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.OPERACIONES,
        phases=[],
        can_block=False,
        blocking_phases=[],
        parent_agent="A2_PMO",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S_RESUMIDOR": AgentConfig(
        id="S_RESUMIDOR",
        name="Subagente Resumidor",
        role="Compresión y Resumen",
        department="PMO",
        description="Genera resúmenes ejecutivos",
        icon="📝",
        color="blue",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.OPERACIONES,
        phases=[],
        can_block=False,
        blocking_phases=[],
        parent_agent="A2_PMO",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S_VERIFICADOR": AgentConfig(
        id="S_VERIFICADOR",
        name="Subagente Verificador",
        role="Control de Calidad",
        department="PMO",
        description="Verifica completitud y calidad de outputs",
        icon="✅",
        color="green",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.OPERACIONES,
        phases=[],
        can_block=False,
        blocking_phases=[],
        parent_agent="A2_PMO",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),

    "S_REDACTOR": AgentConfig(
        id="S_REDACTOR",
        name="Subagente Redactor",
        role="Redacción de Documentos",
        department="PMO",
        description="Genera documentos formales y comunicaciones",
        icon="✍️",
        color="blue",
        type=AgentType.SUBAGENTE,
        category=AgentCategory.OPERACIONES,
        phases=[],
        can_block=False,
        blocking_phases=[],
        parent_agent="A2_PMO",
        llm_model="gpt-4o-mini",
        pcloud_folder=None
    ),
}


# =============================================================================
# FUNCIONES HELPER
# =============================================================================

def get_agent(agent_id: str) -> Optional[AgentConfig]:
    """Obtiene configuración de un agente por ID"""
    return AGENTS_REGISTRY.get(agent_id)


def get_all_agents() -> Dict[str, AgentConfig]:
    """Retorna todos los agentes"""
    return AGENTS_REGISTRY


def get_agents_by_type(agent_type: AgentType) -> List[AgentConfig]:
    """Retorna agentes filtrados por tipo"""
    return [a for a in AGENTS_REGISTRY.values() if a.type == agent_type]


def get_principal_agents() -> List[AgentConfig]:
    """Retorna solo agentes principales"""
    return get_agents_by_type(AgentType.PRINCIPAL)


def get_specialized_agents() -> List[AgentConfig]:
    """Retorna solo agentes especializados"""
    return get_agents_by_type(AgentType.ESPECIALIZADO)


def get_subagents() -> List[AgentConfig]:
    """Retorna solo subagentes"""
    return get_agents_by_type(AgentType.SUBAGENTE)


def get_subagents_of(parent_id: str) -> List[AgentConfig]:
    """Retorna subagentes de un agente padre"""
    return [a for a in AGENTS_REGISTRY.values() if a.parent_agent == parent_id]


def get_agents_for_phase(phase: str) -> List[AgentConfig]:
    """Retorna agentes activos en una fase específica"""
    return [a for a in AGENTS_REGISTRY.values() if phase in a.phases]


def get_blocking_agents_for_phase(phase: str) -> List[AgentConfig]:
    """Retorna agentes que pueden bloquear una fase específica"""
    return [a for a in AGENTS_REGISTRY.values() if phase in a.blocking_phases]


def get_agent_ids() -> List[str]:
    """Retorna lista de todos los IDs de agentes"""
    return list(AGENTS_REGISTRY.keys())


def get_agent_for_api(agent_id: str) -> Optional[Dict[str, Any]]:
    """Retorna agente en formato para API response"""
    agent = get_agent(agent_id)
    if not agent:
        return None
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "department": agent.department,
        "description": agent.description,
        "icon": agent.icon,
        "color": agent.color,
        "type": agent.type.value,
        "category": agent.category.value,
        "phases": agent.phases,
        "can_block": agent.can_block,
        "parent_agent": agent.parent_agent,
    }


def get_all_agents_for_api() -> List[Dict[str, Any]]:
    """Retorna todos los agentes en formato para API"""
    return [get_agent_for_api(aid) for aid in AGENTS_REGISTRY.keys()]


def get_agents_for_frontend() -> List[Dict[str, Any]]:
    """Retorna agentes en formato optimizado para frontend"""
    result = []
    for agent in AGENTS_REGISTRY.values():
        result.append({
            "id": agent.id,
            "shortId": agent.id.split("_")[0] if "_" in agent.id else agent.id,
            "name": agent.name,
            "role": agent.role,
            "icon": agent.icon,
            "color": agent.color,
            "type": agent.type.value,
            "description": agent.description,
            "parentAgent": agent.parent_agent,
        })
    return result


# =============================================================================
# MAPEOS PARA COMPATIBILIDAD CON CÓDIGO LEGACY
# =============================================================================

# Aliases para IDs legacy que se usan en el código existente
AGENT_ID_ALIASES = {
    # Demo flow aliases
    "A1_ESTRATEGIA": "A1_SPONSOR",
    "A1_RECEPCION": "A1_SPONSOR",
    "A2_ANALISIS": "A3_FISCAL",
    "A3_NORMATIVO": "A3_FISCAL",
    "A4_CONTABLE": "A5_FINANZAS",
    "A5_OPERATIVO": "A6_PROVEEDOR",
    "A6_FINANCIERO": "A5_FINANZAS",
    "A7_LEGAL": "A4_LEGAL",
    "A8_REDTEAM": "DEVILS_ADVOCATE",
    "A9_SINTESIS": "A7_DEFENSA",
    "A10_ARCHIVO": "KB_CURATOR",
    "LEGAL": "A4_LEGAL",
    "PROVEEDOR_IA": "A6_PROVEEDOR",
    # Subagent aliases
    "SUB_TIPIFICACION": "S1_TIPIFICACION",
    "SUB_MATERIALIDAD": "S2_MATERIALIDAD",
    "SUB_RIESGOS": "S3_RIESGOS",
    "SUB_RIESGOS_ESPECIALES": "S3_RIESGOS",
}


def resolve_agent_id(agent_id: str) -> str:
    """Resuelve un ID de agente, aplicando aliases si es necesario"""
    return AGENT_ID_ALIASES.get(agent_id, agent_id)


def get_agent_with_alias(agent_id: str) -> Optional[AgentConfig]:
    """Obtiene agente resolviendo aliases primero"""
    resolved_id = resolve_agent_id(agent_id)
    return get_agent(resolved_id)


# =============================================================================
# ESTADÍSTICAS DEL REGISTRO
# =============================================================================

def get_registry_stats() -> Dict[str, Any]:
    """Retorna estadísticas del registro de agentes"""
    agents = list(AGENTS_REGISTRY.values())
    return {
        "total_agents": len(agents),
        "by_type": {
            "principal": len([a for a in agents if a.type == AgentType.PRINCIPAL]),
            "especializado": len([a for a in agents if a.type == AgentType.ESPECIALIZADO]),
            "subagente": len([a for a in agents if a.type == AgentType.SUBAGENTE]),
        },
        "by_category": {
            cat.value: len([a for a in agents if a.category == cat])
            for cat in AgentCategory
        },
        "can_block": len([a for a in agents if a.can_block]),
        "with_pcloud": len([a for a in agents if a.pcloud_folder]),
    }
