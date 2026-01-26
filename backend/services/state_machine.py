from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class ProjectState(str, Enum):
    """Estados de la máquina de estados para proyectos"""
    INTAKE = "INTAKE"
    VALIDACION_PARALELA = "VALIDACION_PARALELA"
    CONSOLIDACION = "CONSOLIDACION"
    REVISION_ITERATIVA = "REVISION_ITERATIVA"
    APROBADO_F0 = "APROBADO_F0"
    RECHAZADO_F0 = "RECHAZADO_F0"
    ESCALADO_HUMANO = "ESCALADO_HUMANO"
    
    # Estados de fases posteriores
    FORMALIZACION_LEGAL = "FORMALIZACION_LEGAL"
    EJECUCION = "EJECUCION"
    ENTREGA = "ENTREGA"
    PAGO = "PAGO"
    CERRADO = "CERRADO"

class AgentDecision(str, Enum):
    """Decisiones posibles de los agentes"""
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    CONDICIONAL = "CONDICIONAL"  # Aprueba con condiciones
    PENDIENTE = "PENDIENTE"

class ProjectStateMachine:
    """Máquina de estados para gestionar el flujo de proyectos"""
    
    def __init__(self):
        self.max_revision_cycles = 2  # Máximo 2 ciclos de revisión iterativa
        
    def get_initial_state(self) -> ProjectState:
        """Estado inicial de todo proyecto"""
        return ProjectState.INTAKE
    
    def can_transition(self, current_state: ProjectState, next_state: ProjectState) -> bool:
        """Valida si una transición de estado es permitida"""
        valid_transitions = {
            # === FASE 0: Intake y Validación ===
            ProjectState.INTAKE: [ProjectState.VALIDACION_PARALELA],
            ProjectState.VALIDACION_PARALELA: [ProjectState.CONSOLIDACION],
            ProjectState.CONSOLIDACION: [
                ProjectState.APROBADO_F0,
                ProjectState.RECHAZADO_F0,
                ProjectState.REVISION_ITERATIVA
            ],
            ProjectState.REVISION_ITERATIVA: [
                ProjectState.CONSOLIDACION,  # Loop back después de revisión
                ProjectState.ESCALADO_HUMANO  # Si alcanza límite de ciclos
            ],
            ProjectState.APROBADO_F0: [ProjectState.FORMALIZACION_LEGAL],
            ProjectState.RECHAZADO_F0: [ProjectState.CERRADO],
            ProjectState.ESCALADO_HUMANO: [
                ProjectState.APROBADO_F0,
                ProjectState.RECHAZADO_F0,
                ProjectState.CERRADO
            ],

            # === FASE 1-2: Formalización Legal y Financiera ===
            ProjectState.FORMALIZACION_LEGAL: [
                ProjectState.EJECUCION,  # Contrato firmado, procede ejecución
                ProjectState.RECHAZADO_F0,  # Legal rechaza contrato
                ProjectState.ESCALADO_HUMANO  # Requiere intervención humana
            ],

            # === FASE 3-4: Ejecución y Monitoreo ===
            ProjectState.EJECUCION: [
                ProjectState.ENTREGA,  # Ejecución completa, procede entrega
                ProjectState.ESCALADO_HUMANO  # Problemas durante ejecución
            ],

            # === FASE 5-6-7: Entrega y Auditoría ===
            ProjectState.ENTREGA: [
                ProjectState.PAGO,  # Entrega aceptada, procede pago
                ProjectState.EJECUCION,  # Entrega rechazada, volver a ejecución
                ProjectState.ESCALADO_HUMANO  # Disputas en entrega
            ],

            # === FASE 8-9: Pago y Cierre ===
            ProjectState.PAGO: [
                ProjectState.CERRADO,  # Pago procesado, proyecto cerrado
                ProjectState.ESCALADO_HUMANO  # Problemas con pago
            ],

            # === Estado Final ===
            ProjectState.CERRADO: []  # Estado terminal, no permite transiciones
        }

        return next_state in valid_transitions.get(current_state, [])

    def get_valid_transitions(self, current_state: ProjectState) -> List[ProjectState]:
        """Retorna la lista de transiciones válidas desde el estado actual"""
        valid_transitions = {
            ProjectState.INTAKE: [ProjectState.VALIDACION_PARALELA],
            ProjectState.VALIDACION_PARALELA: [ProjectState.CONSOLIDACION],
            ProjectState.CONSOLIDACION: [ProjectState.APROBADO_F0, ProjectState.RECHAZADO_F0, ProjectState.REVISION_ITERATIVA],
            ProjectState.REVISION_ITERATIVA: [ProjectState.CONSOLIDACION, ProjectState.ESCALADO_HUMANO],
            ProjectState.APROBADO_F0: [ProjectState.FORMALIZACION_LEGAL],
            ProjectState.RECHAZADO_F0: [ProjectState.CERRADO],
            ProjectState.ESCALADO_HUMANO: [ProjectState.APROBADO_F0, ProjectState.RECHAZADO_F0, ProjectState.CERRADO],
            ProjectState.FORMALIZACION_LEGAL: [ProjectState.EJECUCION, ProjectState.RECHAZADO_F0, ProjectState.ESCALADO_HUMANO],
            ProjectState.EJECUCION: [ProjectState.ENTREGA, ProjectState.ESCALADO_HUMANO],
            ProjectState.ENTREGA: [ProjectState.PAGO, ProjectState.EJECUCION, ProjectState.ESCALADO_HUMANO],
            ProjectState.PAGO: [ProjectState.CERRADO, ProjectState.ESCALADO_HUMANO],
            ProjectState.CERRADO: []
        }
        return valid_transitions.get(current_state, [])
    
    def evaluate_consensus(
        self,
        decisions: Dict[str, AgentDecision]
    ) -> tuple[bool, Optional[ProjectState], str]:
        """
        Evalúa si hay consenso entre los agentes.
        
        Returns:
            (tiene_consenso, next_state, razon)
        """
        unique_decisions = set(decisions.values())
        
        # Consenso positivo: Todos aprueban
        if unique_decisions == {AgentDecision.APROBADO}:
            return True, ProjectState.APROBADO_F0, "Consenso positivo - Todos los agentes aprueban"
        
        # Consenso negativo: Todos rechazan
        if unique_decisions == {AgentDecision.RECHAZADO}:
            return True, ProjectState.RECHAZADO_F0, "Consenso negativo - Todos los agentes rechazan"
        
        # Conflicto: Hay desacuerdo
        return False, ProjectState.REVISION_ITERATIVA, f"Conflicto detectado - Decisiones: {decisions}"
    
    def should_escalate_to_human(self, revision_cycle: int) -> bool:
        """Determina si se debe escalar a humano por límite de ciclos"""
        return revision_cycle >= self.max_revision_cycles
    
    def get_next_state_on_escalation(self, decisions: Dict[str, AgentDecision]) -> ProjectState:
        """Determina el siguiente estado cuando se escala a humano"""
        # Contar votos
        approvals = sum(1 for d in decisions.values() if d == AgentDecision.APROBADO)
        rejections = sum(1 for d in decisions.values() if d == AgentDecision.RECHAZADO)
        
        # Decisión por mayoría
        if approvals > rejections:
            return ProjectState.APROBADO_F0
        elif rejections > approvals:
            return ProjectState.RECHAZADO_F0
        else:
            return ProjectState.ESCALADO_HUMANO  # Empate - requiere decisión humana definitiva
    
    def create_state_transition_log(
        self,
        project_id: str,
        from_state: ProjectState,
        to_state: ProjectState,
        reason: str,
        actor: str = "A2_PMO"
    ) -> Dict:
        """Crea un registro de transición de estado para auditoría"""
        return {
            "project_id": project_id,
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_valid": self.can_transition(from_state, to_state)
        }
    
    def format_email_subject(
        self,
        phase: str,
        state: ProjectState,
        project_id: str,
        action: str
    ) -> str:
        """
        Formatea el subject del email según el protocolo.
        Formato: [FASE X] - [ESTADO] - ID:[Project ID] - [Acción Requerida]
        """
        return f"[FASE {phase}] - {state.value} - ID:{project_id[:8]} - {action}"
    
    def format_attachment_name(
        self,
        project_id: str,
        agent_id: str,
        report_type: str,
        version: int,
        extension: str = "pdf"
    ) -> str:
        """
        Formatea el nombre de archivo adjunto según el protocolo.
        Formato: ID[Project ID]_[Agent ID]_Reporte_[Tipo]_V[Version].[ext]
        """
        return f"ID{project_id[:8]}_{agent_id}_Reporte_{report_type}_V{version}.{extension}"
