"""
DocAgent Service for Revisar.IA Platform Documentation System.

Orchestrates inventory detection, extraction, and publication of system documentation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
import logging

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

logger = logging.getLogger(__name__)

MAIN_AGENTS_DATA = [
    {
        "agent_id": "A1_SPONSOR",
        "name": "Estrategia",
        "persona": "María",
        "type": AgentType.PRINCIPAL,
        "role": "Validador Estratégico",
        "description": "Valida alineación estratégica del proyecto con objetivos de negocio. Define BEE (Beneficio Económico Esperado) y asegura que cada proyecto tenga razón de negocios documentada.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_bee", "name": "Definición BEE", "description": "Define y valida el Beneficio Económico Esperado", "can_block": False},
            {"id": "cap_strategy", "name": "Alineación Estratégica", "description": "Valida alineación con plan estratégico", "can_block": False},
            {"id": "cap_approval", "name": "Aprobación Inicial", "description": "Aprueba o rechaza proyectos en F0", "can_block": True}
        ],
        "controls": [
            {"id": "ctrl_f0_approval", "name": "Aprobación F0", "phase": "F0", "condition": "Debe aprobar antes de avanzar a F1"}
        ],
        "phases": ["F0", "F4", "F5", "F9"],
        "can_block": True,
        "source_refs": [{"file": "config_agentes/a1_sponsor.py", "type": "config"}]
    },
    {
        "agent_id": "A2_PMO",
        "name": "PMO",
        "persona": "Carlos",
        "type": AgentType.PRINCIPAL,
        "role": "Orquestador Central",
        "description": "Orquesta el flujo de trabajo entre agentes, consolida dictámenes y gestiona la comunicación con el usuario. Es el punto central de coordinación del sistema.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_orchestration", "name": "Orquestación", "description": "Coordina flujo entre agentes", "can_block": False},
            {"id": "cap_consolidation", "name": "Consolidación", "description": "Consolida dictámenes de todos los agentes", "can_block": False},
            {"id": "cap_audit", "name": "Auditoría Interna", "description": "Realiza auditoría en F7", "can_block": False}
        ],
        "controls": [
            {"id": "ctrl_f7_audit", "name": "Auditoría F7", "phase": "F7", "condition": "Realiza auditoría interna antes de pago"}
        ],
        "phases": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
        "can_block": False,
        "source_refs": [{"file": "config_agentes/a2_pmo.py", "type": "config"}]
    },
    {
        "agent_id": "A3_FISCAL",
        "name": "Fiscal",
        "persona": "Laura",
        "type": AgentType.PRINCIPAL,
        "role": "Motor de Cumplimiento",
        "description": "Evalúa riesgos fiscales, emite VBC Fiscal, y asegura cumplimiento con normativa SAT. Detecta operaciones que podrían ser cuestionadas.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_risk_eval", "name": "Evaluación de Riesgo", "description": "Calcula risk_score fiscal", "can_block": False},
            {"id": "cap_vbc_fiscal", "name": "VBC Fiscal", "description": "Emite Visto Bueno de Cumplimiento Fiscal", "can_block": True},
            {"id": "cap_sat_compliance", "name": "Cumplimiento SAT", "description": "Verifica cumplimiento con normativa SAT", "can_block": True}
        ],
        "controls": [
            {"id": "ctrl_f0_approval", "name": "Aprobación F0", "phase": "F0", "condition": "Debe aprobar riesgo fiscal inicial"},
            {"id": "ctrl_f6_vbc", "name": "VBC F6", "phase": "F6", "condition": "Debe emitir VBC Fiscal antes de CFDI"}
        ],
        "phases": ["F0", "F6"],
        "can_block": True,
        "source_refs": [{"file": "config_agentes/a3_fiscal.py", "type": "config"}]
    },
    {
        "agent_id": "A4_LEGAL",
        "name": "Legal",
        "persona": "Gestor IA",
        "type": AgentType.PRINCIPAL,
        "role": "Validador Contractual",
        "description": "Valida contratos, SOWs, y documentación legal. Emite VBC Legal asegurando que la operación tenga sustento contractual adecuado.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_contract_review", "name": "Revisión Contractual", "description": "Revisa contratos y SOWs", "can_block": False},
            {"id": "cap_vbc_legal", "name": "VBC Legal", "description": "Emite Visto Bueno de Cumplimiento Legal", "can_block": True},
            {"id": "cap_tp_review", "name": "Revisión TP", "description": "Revisa estudios de precios de transferencia", "can_block": False}
        ],
        "controls": [
            {"id": "ctrl_f1_sow", "name": "SOW F1", "phase": "F1", "condition": "Valida SOW antes de contratación"},
            {"id": "ctrl_f6_vbc", "name": "VBC F6", "phase": "F6", "condition": "Debe emitir VBC Legal antes de CFDI"}
        ],
        "phases": ["F1", "F6"],
        "can_block": True,
        "source_refs": [{"file": "config_agentes/a4_legal.py", "type": "config"}]
    },
    {
        "agent_id": "A5_FINANZAS",
        "name": "Finanzas",
        "persona": "Roberto",
        "type": AgentType.PRINCIPAL,
        "role": "Controlador Financiero",
        "description": "Confirma presupuesto, valida 3-way match (Contrato=CFDI=Pago), y autoriza liberación de pagos.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_budget", "name": "Confirmación Presupuesto", "description": "Confirma disponibilidad presupuestal", "can_block": True},
            {"id": "cap_3way", "name": "3-Way Match", "description": "Valida Contrato=CFDI=Pago", "can_block": True},
            {"id": "cap_payment", "name": "Autorización Pago", "description": "Autoriza liberación de pago", "can_block": True}
        ],
        "controls": [
            {"id": "ctrl_f2_budget", "name": "Presupuesto F2", "phase": "F2", "condition": "Debe confirmar presupuesto antes de inicio"},
            {"id": "ctrl_f8_payment", "name": "Pago F8", "phase": "F8", "condition": "Debe validar 3-way match antes de pago"}
        ],
        "phases": ["F2", "F8"],
        "can_block": True,
        "source_refs": [{"file": "config_agentes/a5_finanzas.py", "type": "config"}]
    },
    {
        "agent_id": "A6_PROVEEDOR",
        "name": "Proveedor",
        "persona": "Ana",
        "type": AgentType.PRINCIPAL,
        "role": "Ejecutor del Servicio",
        "description": "Gestiona la relación con proveedores, supervisa ejecución del servicio, y valida entregables.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_execution", "name": "Supervisión Ejecución", "description": "Supervisa ejecución del servicio", "can_block": False},
            {"id": "cap_deliverables", "name": "Validación Entregables", "description": "Valida entregables del proveedor", "can_block": False},
            {"id": "cap_vendor_mgmt", "name": "Gestión Proveedor", "description": "Gestiona relación con proveedor", "can_block": False}
        ],
        "controls": [
            {"id": "ctrl_f3_kickoff", "name": "Kick-off F3", "phase": "F3", "condition": "Inicia ejecución con proveedor"},
            {"id": "ctrl_f4_review", "name": "Revisión F4", "phase": "F4", "condition": "Revisa iteraciones de entregables"}
        ],
        "phases": ["F3", "F4"],
        "can_block": False,
        "source_refs": [{"file": "config_agentes/a6_proveedor.py", "type": "config"}]
    },
    {
        "agent_id": "A7_DEFENSA",
        "name": "Defensa",
        "persona": "Sistema",
        "type": AgentType.PRINCIPAL,
        "role": "Generador Defense File",
        "description": "Consolida toda la documentación en un Defense File estructurado, evalúa defendibilidad ante auditoría SAT o juicio TFJA.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_defense_file", "name": "Generación Defense File", "description": "Genera expediente de defensa completo", "can_block": False},
            {"id": "cap_defendibility", "name": "Evaluación Defendibilidad", "description": "Evalúa fortaleza del expediente", "can_block": False},
            {"id": "cap_recommendations", "name": "Recomendaciones Refuerzo", "description": "Genera recomendaciones para fortalecer expediente", "can_block": False}
        ],
        "controls": [
            {"id": "ctrl_f6_defense", "name": "Defense File F6", "phase": "F6", "condition": "Genera Defense File antes de VBC"},
            {"id": "ctrl_f9_final", "name": "Evaluación Final F9", "phase": "F9", "condition": "Evaluación final post-implementación"}
        ],
        "phases": ["F6", "F9"],
        "can_block": False,
        "source_refs": [{"file": "agents/a7_defensa.py", "type": "source"}]
    }
]

SUBAGENTS_DATA = [
    {
        "agent_id": "SUB_TIPIFICACION",
        "name": "Tipificación",
        "persona": None,
        "type": AgentType.SUBAGENT,
        "role": "Clasificador de Proyectos",
        "description": "Clasifica cada proyecto nuevo en la tipología correcta (CONSULTORIA_MACRO_MERCADO, SOFTWARE_SAAS_DESARROLLO, INTRAGRUPO_MANAGEMENT_FEE, etc.) basándose en descripción, objetivo y características del servicio.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_classify", "name": "Clasificación Tipología", "description": "Clasifica proyectos en tipologías predefinidas", "can_block": False},
            {"id": "cap_checklist", "name": "Asignación Checklist", "description": "Asigna checklist según tipología", "can_block": False}
        ],
        "controls": [],
        "phases": ["F0"],
        "parent_id": None,
        "can_block": False,
        "source_refs": [{"file": "agents/sub_tipificacion.py", "type": "source"}]
    },
    {
        "agent_id": "SUB_MATERIALIDAD",
        "name": "Materialidad",
        "persona": None,
        "type": AgentType.SUBAGENT,
        "role": "Monitor de Evidencia Documental",
        "description": "Monitorea continuamente la matriz de materialidad del proyecto, verificando que cada hecho relevante tenga evidencia documental asociada. Calcula porcentaje de completitud y alerta sobre brechas críticas.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_matrix", "name": "Matriz Materialidad", "description": "Evalúa matriz de materialidad", "can_block": True},
            {"id": "cap_gaps", "name": "Detección Brechas", "description": "Detecta brechas documentales críticas", "can_block": True},
            {"id": "cap_vbc_check", "name": "Verificación VBC", "description": "Verifica umbral para VBC (80%)", "can_block": True}
        ],
        "controls": [
            {"id": "ctrl_vbc_threshold", "name": "Umbral VBC", "phase": "F6", "condition": "Completitud >= 80% para emitir VBC"}
        ],
        "phases": ["F5", "F6"],
        "parent_id": None,
        "can_block": True,
        "source_refs": [{"file": "agents/sub_materialidad.py", "type": "source"}]
    },
    {
        "agent_id": "SUB_RIESGOS_ESPECIALES",
        "name": "Riesgos Especiales",
        "persona": None,
        "type": AgentType.SUBAGENT,
        "role": "Detector de Riesgos Especiales",
        "description": "Detecta alertas de riesgo que requieren atención especial: operaciones con EFOS potenciales, partes relacionadas sin documentación de TP, posibles esquemas reportables, y señales de simulación o planeación fiscal agresiva.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_efos", "name": "Detección EFOS", "description": "Detecta operaciones con EFOS potenciales", "can_block": True},
            {"id": "cap_related", "name": "Partes Relacionadas", "description": "Detecta riesgos de partes relacionadas", "can_block": True},
            {"id": "cap_reportable", "name": "Esquemas Reportables", "description": "Detecta posibles esquemas reportables", "can_block": True},
            {"id": "cap_tp", "name": "TP Pendiente", "description": "Detecta operaciones sin estudio TP", "can_block": True}
        ],
        "controls": [
            {"id": "ctrl_efos_block", "name": "Bloqueo EFOS", "phase": "F0", "condition": "RFC en lista 69-B bloquea operación"},
            {"id": "ctrl_tp_block", "name": "Bloqueo TP", "phase": "F6", "condition": "Intra-grupo >$1M sin TP bloquea VBC"}
        ],
        "phases": ["F0", "F6"],
        "parent_id": None,
        "can_block": True,
        "source_refs": [{"file": "agents/sub_riesgos_especiales.py", "type": "source"}]
    },
    {
        "agent_id": "A7_DEFENSA_SUB",
        "name": "Generador Defensa",
        "persona": None,
        "type": AgentType.SUBAGENT,
        "role": "Generador de Defense File",
        "description": "Subagente auxiliar que genera componentes del Defense File: evalúa razón de negocios, beneficio económico, materialidad, trazabilidad y coherencia global del expediente.",
        "version": "4.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": [
            {"id": "cap_eval_razon", "name": "Evaluación Razón Negocios", "description": "Evalúa documentación de razón de negocios", "can_block": False},
            {"id": "cap_eval_beneficio", "name": "Evaluación Beneficio", "description": "Evalúa documentación de beneficio económico", "can_block": False},
            {"id": "cap_indice", "name": "Índice Defendibilidad", "description": "Calcula índice de defendibilidad", "can_block": False}
        ],
        "controls": [],
        "phases": ["F6", "F9"],
        "parent_id": "A7_DEFENSA",
        "can_block": False,
        "source_refs": [{"file": "agents/a7_defensa.py", "type": "source"}]
    }
]

PHASES_DATA = [
    {
        "phase_id": "F0",
        "name": "Aprobación - Definir BEE",
        "description": "Fase inicial donde se define el Beneficio Económico Esperado y se obtiene aprobación estratégica y fiscal inicial.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A1_SPONSOR", "A3_FISCAL"],
        "order": 0
    },
    {
        "phase_id": "F1",
        "name": "Pre-contratación / SOW",
        "description": "Elaboración y validación del Statement of Work con entregables específicos y cronograma.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A4_LEGAL"],
        "order": 1
    },
    {
        "phase_id": "F2",
        "name": "Validación previa al inicio",
        "description": "CANDADO DURO: No puede iniciarse ejecución sin aprobación completa de F0 y F1, confirmación de presupuesto, y revisión humana si aplica.",
        "is_hard_lock": True,
        "lock_condition": "No puede iniciarse ejecución sin aprobación completa",
        "required_agents": ["A5_FINANZAS"],
        "order": 2
    },
    {
        "phase_id": "F3",
        "name": "Ejecución inicial",
        "description": "Kick-off del proyecto con proveedor, inicio de ejecución del servicio.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A6_PROVEEDOR"],
        "order": 3
    },
    {
        "phase_id": "F4",
        "name": "Revisión iterativa",
        "description": "Revisiones iterativas de entregables con el proveedor hasta alcanzar versión aceptable.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A1_SPONSOR", "A6_PROVEEDOR"],
        "order": 4
    },
    {
        "phase_id": "F5",
        "name": "Entrega final / Aceptación técnica",
        "description": "Entrega del entregable final y firma de acta de aceptación técnica.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A1_SPONSOR"],
        "order": 5
    },
    {
        "phase_id": "F6",
        "name": "VBC Fiscal/Legal",
        "description": "CANDADO DURO: No puede emitirse CFDI/pago sin VBC de Fiscal y Legal. Requiere matriz de materialidad >= 80%.",
        "is_hard_lock": True,
        "lock_condition": "No puede emitirse CFDI/pago sin VBC de Fiscal y Legal",
        "required_agents": ["A3_FISCAL", "A4_LEGAL"],
        "order": 6
    },
    {
        "phase_id": "F7",
        "name": "Auditoría interna",
        "description": "Auditoría interna del expediente por PMO antes de autorizar pago.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A2_PMO"],
        "order": 7
    },
    {
        "phase_id": "F8",
        "name": "CFDI y pago",
        "description": "CANDADO DURO: No puede liberarse pago sin 3-way match validado (Contrato=CFDI=Pago).",
        "is_hard_lock": True,
        "lock_condition": "No puede liberarse pago sin 3-way match validado",
        "required_agents": ["A5_FINANZAS"],
        "order": 8
    },
    {
        "phase_id": "F9",
        "name": "Post-implementación",
        "description": "Evaluación post-implementación, seguimiento de beneficios, y cierre del expediente.",
        "is_hard_lock": False,
        "lock_condition": None,
        "required_agents": ["A1_SPONSOR"],
        "order": 9
    }
]

PILLARS_DATA = [
    {
        "pillar_id": "P1_RAZON_NEGOCIOS",
        "name": "Razón de Negocios",
        "max_points": 25,
        "description": "Evalúa la justificación económica y estratégica de la operación según Art. 5-A del CFF.",
        "evaluation_criteria": [
            "SIB con objetivo económico específico documentado",
            "Vinculación con plan estratégico",
            "Explicación clara de necesidad del servicio",
            "Coherencia con operaciones habituales"
        ]
    },
    {
        "pillar_id": "P2_BENEFICIO_ECONOMICO",
        "name": "Beneficio Económico Esperado",
        "max_points": 25,
        "description": "Evalúa la documentación del beneficio económico esperado (BEE) según Art. 5-A del CFF.",
        "evaluation_criteria": [
            "BEE con ROI documentado",
            "Usos concretos del servicio identificados",
            "Evidencia de seguimiento post-implementación",
            "Métricas de éxito definidas"
        ]
    },
    {
        "pillar_id": "P3_MATERIALIDAD",
        "name": "Materialidad",
        "max_points": 25,
        "description": "Evalúa la existencia de evidencia documental tangible según Art. 69-B del CFF.",
        "evaluation_criteria": [
            "Contrato con entregables específicos",
            "Entregables tangibles verificables",
            "Sesiones de trabajo reconstruibles",
            "CFDI específico que coincide con contrato"
        ]
    },
    {
        "pillar_id": "P4_TRAZABILIDAD",
        "name": "Trazabilidad",
        "max_points": 25,
        "description": "Evalúa la integridad y trazabilidad del expediente según NOM-151.",
        "evaluation_criteria": [
            "Documentos con fecha cierta",
            "Timeline completo reconstruible",
            "Integridad documental verificable",
            "Cadena de custodia clara"
        ]
    }
]


class InventoryAgent:
    """
    Agent that scans the codebase to detect and inventory all agents and subagents.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    async def scan_agents(self) -> List[AgentInventoryItem]:
        """Scan and return all main agents."""
        agents = []
        for agent_data in MAIN_AGENTS_DATA:
            capabilities = [CapabilityModel(**cap) for cap in agent_data.get("capabilities", [])]
            controls = [ControlModel(**ctrl) for ctrl in agent_data.get("controls", [])]
            
            agent = AgentInventoryItem(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                persona=agent_data.get("persona"),
                type=agent_data["type"],
                role=agent_data["role"],
                description=agent_data["description"],
                version=agent_data.get("version", "4.0.0"),
                status=agent_data.get("status", AgentStatus.ACTIVE),
                capabilities=capabilities,
                controls=controls,
                phases=agent_data.get("phases", []),
                parent_id=agent_data.get("parent_id"),
                can_block=agent_data.get("can_block", False),
                source_refs=agent_data.get("source_refs", [])
            )
            agents.append(agent)
        
        return agents
    
    async def scan_subagents(self) -> List[AgentInventoryItem]:
        """Scan and return all subagents."""
        subagents = []
        for agent_data in SUBAGENTS_DATA:
            capabilities = [CapabilityModel(**cap) for cap in agent_data.get("capabilities", [])]
            controls = [ControlModel(**ctrl) for ctrl in agent_data.get("controls", [])]
            
            agent = AgentInventoryItem(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                persona=agent_data.get("persona"),
                type=agent_data["type"],
                role=agent_data["role"],
                description=agent_data["description"],
                version=agent_data.get("version", "4.0.0"),
                status=agent_data.get("status", AgentStatus.ACTIVE),
                capabilities=capabilities,
                controls=controls,
                phases=agent_data.get("phases", []),
                parent_id=agent_data.get("parent_id"),
                can_block=agent_data.get("can_block", False),
                source_refs=agent_data.get("source_refs", [])
            )
            subagents.append(agent)
        
        return subagents
    
    async def get_full_inventory(self) -> List[AgentInventoryItem]:
        """Get complete inventory of all agents and subagents."""
        agents = await self.scan_agents()
        subagents = await self.scan_subagents()
        return agents + subagents


class ExtractionAgent:
    """
    Agent that extracts metadata from agent files and generates documentation.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    async def extract_phases(self) -> List[PhaseModel]:
        """Extract phases documentation from fase_service.py."""
        phases = []
        for phase_data in PHASES_DATA:
            phase = PhaseModel(
                phase_id=phase_data["phase_id"],
                name=phase_data["name"],
                description=phase_data["description"],
                is_hard_lock=phase_data.get("is_hard_lock", False),
                lock_condition=phase_data.get("lock_condition"),
                required_agents=phase_data.get("required_agents", []),
                order=phase_data["order"]
            )
            phases.append(phase)
        return phases
    
    async def extract_pillars(self) -> List[PillarModel]:
        """Extract pillars documentation."""
        pillars = []
        for pillar_data in PILLARS_DATA:
            pillar = PillarModel(
                pillar_id=pillar_data["pillar_id"],
                name=pillar_data["name"],
                max_points=pillar_data.get("max_points", 25),
                description=pillar_data["description"],
                evaluation_criteria=pillar_data.get("evaluation_criteria", [])
            )
            pillars.append(pillar)
        return pillars
    
    def generate_markdown(self, agent: AgentInventoryItem) -> str:
        """Generate markdown documentation for an agent."""
        md = f"# {agent.name}\n\n"
        md += f"**ID:** `{agent.agent_id}`\n\n"
        
        if agent.persona:
            md += f"**Persona:** {agent.persona}\n\n"
        
        md += f"**Tipo:** {agent.type.value.capitalize()}\n\n"
        md += f"**Rol:** {agent.role}\n\n"
        md += f"## Descripción\n\n{agent.description}\n\n"
        
        if agent.phases:
            md += f"## Fases de Participación\n\n"
            md += ", ".join(agent.phases) + "\n\n"
        
        if agent.capabilities:
            md += f"## Capacidades\n\n"
            for cap in agent.capabilities:
                blocking = " ⛔" if cap.can_block else ""
                md += f"- **{cap.name}**: {cap.description}{blocking}\n"
            md += "\n"
        
        if agent.controls:
            md += f"## Controles\n\n"
            for ctrl in agent.controls:
                md += f"- **{ctrl.name}** ({ctrl.phase}): {ctrl.condition}\n"
            md += "\n"
        
        if agent.can_block:
            md += f"⚠️ **Este agente puede bloquear el avance del proyecto.**\n\n"
        
        return md


class DocAgentService:
    """
    Main documentation agent that orchestrates inventory detection,
    extraction, and publication of system documentation.
    """
    
    def __init__(self):
        self.inventory_agent = InventoryAgent()
        self.extraction_agent = ExtractionAgent()
        self._snapshots: List[DocumentationSnapshot] = []
    
    async def generate_full_documentation(self) -> DocumentationSnapshot:
        """Generate a complete documentation snapshot."""
        agents = await self.get_agent_inventory()
        phases = await self.get_phases_documentation()
        pillars = await self.get_pillars_documentation()
        
        version = f"4.0.{len(self._snapshots)}"
        
        snapshot = DocumentationSnapshot(
            version=version,
            agents=agents,
            phases=phases,
            pillars=pillars,
            changelog=f"Documentation snapshot generated at {datetime.utcnow().isoformat()}"
        )
        
        self._snapshots.append(snapshot)
        
        return snapshot
    
    async def get_agent_inventory(self) -> List[AgentInventoryItem]:
        """Get full agent inventory."""
        return await self.inventory_agent.get_full_inventory()
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentInventoryItem]:
        """Get a specific agent by ID."""
        inventory = await self.get_agent_inventory()
        for agent in inventory:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    async def get_phases_documentation(self) -> List[PhaseModel]:
        """Get all phases documentation."""
        return await self.extraction_agent.extract_phases()
    
    async def get_pillars_documentation(self) -> List[PillarModel]:
        """Get all pillars documentation."""
        return await self.extraction_agent.extract_pillars()
    
    async def detect_changes(self, previous_snapshot: DocumentationSnapshot) -> Dict[str, Any]:
        """Detect changes between current state and previous snapshot."""
        current = await self.generate_full_documentation()
        
        changes = {
            "agents_added": [],
            "agents_removed": [],
            "agents_modified": [],
            "phases_changed": False,
            "pillars_changed": False
        }
        
        prev_agent_ids = {a.agent_id for a in previous_snapshot.agents}
        curr_agent_ids = {a.agent_id for a in current.agents}
        
        changes["agents_added"] = list(curr_agent_ids - prev_agent_ids)
        changes["agents_removed"] = list(prev_agent_ids - curr_agent_ids)
        
        for curr_agent in current.agents:
            for prev_agent in previous_snapshot.agents:
                if curr_agent.agent_id == prev_agent.agent_id:
                    if curr_agent.version != prev_agent.version or \
                       curr_agent.description != prev_agent.description or \
                       len(curr_agent.capabilities) != len(prev_agent.capabilities):
                        changes["agents_modified"].append(curr_agent.agent_id)
                    break
        
        if len(current.phases) != len(previous_snapshot.phases):
            changes["phases_changed"] = True
        
        if len(current.pillars) != len(previous_snapshot.pillars):
            changes["pillars_changed"] = True
        
        return changes
    
    def get_snapshots(self) -> List[DocumentationSnapshot]:
        """Get all stored snapshots."""
        return self._snapshots
    
    def generate_agent_markdown(self, agent: AgentInventoryItem) -> str:
        """Generate markdown documentation for an agent."""
        return self.extraction_agent.generate_markdown(agent)


doc_agent_service = DocAgentService()
