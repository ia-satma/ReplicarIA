from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class ProjectPhase(str, Enum):
    """Fases del proyecto según flujo documentado"""
    PHASE_0_INTAKE = "phase_0_intake"
    PHASE_1_ACQUISITION = "phase_1_acquisition"
    PHASE_2_CONTRACTUAL = "phase_2_contractual"
    PHASE_3_EXECUTION = "phase_3_execution"
    PHASE_4_MONITORING = "phase_4_monitoring"
    PHASE_5_DELIVERY = "phase_5_delivery"
    PHASE_6_VALIDATION = "phase_6_validation"
    PHASE_7_AUDIT = "phase_7_audit"
    PHASE_8_PAYMENT = "phase_8_payment"
    PHASE_9_CLOSURE = "phase_9_closure"

class ProjectStatus(str, Enum):
    """Estados del proyecto"""
    SUBMITTED = "submitted"
    IN_VALIDATION = "in_validation"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONTRACTED = "contracted"
    IN_EXECUTION = "in_execution"
    COMPLETED = "completed"
    CLOSED = "closed"

class StrategicInitiativeBrief(BaseModel):
    """Strategic Initiative Brief (SIB) - Formulario inicial"""
    sib_id: str
    project_name: str
    sponsor_name: str
    sponsor_email: str
    department: str
    description: str
    strategic_alignment: str
    expected_economic_benefit: float
    budget_estimate: float
    duration_months: int
    attachments: List[str] = []
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    form_data: Dict = {}  # Datos completos del formulario Wufoo

class ValidationReport(BaseModel):
    """Reporte de validación de un agente"""
    report_id: str
    project_id: str
    agent_id: str
    agent_role: str
    validation_type: str  # strategic, fiscal, legal, financial
    is_approved: bool
    findings: List[str]
    recommendations: List[str]
    risk_level: str  # low, medium, high
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    llm_analysis: Optional[str] = None

class Evidence(BaseModel):
    """Evidencia documental del proyecto"""
    evidence_id: str
    project_id: str
    phase: ProjectPhase
    evidence_type: str  # email, document, log, report
    file_path: Optional[str] = None
    drive_file_id: Optional[str] = None
    description: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = {}

class Project(BaseModel):
    """Proyecto completo en el sistema"""
    project_id: str
    sib_id: str
    current_phase: ProjectPhase
    current_status: ProjectStatus
    
    # State Machine para workflow coordinado
    workflow_state: str = "INTAKE"  # Estado de la máquina de estados
    revision_cycle: int = 0  # Contador de ciclos de revisión iterativa
    
    # Información básica
    project_name: str
    sponsor_agent_id: str
    description: str
    
    # Tracking financiero
    budget: float
    expected_benefit: float
    actual_cost: float = 0.0
    
    # Fechas importantes
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Documentación y evidencias
    validation_reports: List[str] = []  # IDs de reportes
    evidences: List[str] = []  # IDs de evidencias
    contracts: List[str] = []  # IDs de contratos
    
    # Defense File (carpeta de trazabilidad)
    defense_file_folder_id: Optional[str] = None
    
    # Metadata adicional
    metadata: Dict = {}
    
    class Config:
        use_enum_values = True
