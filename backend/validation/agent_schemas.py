"""
Schemas de Validación para Outputs de Agentes - Revisar.IA

Cada agente debe producir outputs estructurados y completos.
Estos schemas aseguran la calidad y consistencia de las respuestas.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DecisionEnum(str, Enum):
    APROBAR = "APROBAR"
    APROBAR_CONDICIONES = "APROBAR_CONDICIONES"
    SOLICITAR_AJUSTES = "SOLICITAR_AJUSTES"
    RECHAZAR = "RECHAZAR"
    PENDIENTE = "PENDIENTE"


class StatusPilarEnum(str, Enum):
    CONFORME = "CONFORME"
    CONDICIONADO = "CONDICIONADO"
    NO_CONFORME = "NO_CONFORME"
    EN_RIESGO = "EN_RIESGO"
    FALLA_CRITICA = "FALLA_CRITICA"


class EstadoChecklistEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENTREGADO = "ENTREGADO"
    INCONSISTENTE = "INCONSISTENTE"


class SeveridadEnum(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class TipoAlertaEnum(str, Enum):
    EFOS = "EFOS"
    PARTE_RELACIONADA = "PARTE_RELACIONADA"
    ESQUEMA_REPORTABLE = "ESQUEMA_REPORTABLE"
    TP_PENDIENTE = "TP_PENDIENTE"
    MONTO_ALTO = "MONTO_ALTO"
    OTRO = "OTRO"


class AnalisisRazonNegocios(BaseModel):
    vinculacion_con_giro: str = Field(..., min_length=30, description="Mínimo 30 caracteres")
    objetivo_economico: str = Field(..., min_length=50, description="Mínimo 50 caracteres")
    conclusion: Literal["CONFORME", "CONDICIONADO", "NO_CONFORME"]


class AnalisisBEE(BaseModel):
    objetivo_especifico: str = Field(..., min_length=50, description="Mínimo 50 caracteres")
    roi_esperado: Optional[float] = None
    horizonte_meses: Optional[int] = Field(None, gt=0)
    indicadores_exito: List[str] = Field(..., min_length=1)
    evaluacion: Literal["CONFORME", "CONDICIONADO", "NO_CONFORME"]


class A1SponsorOutput(BaseModel):
    """Schema de validación para A1_SPONSOR"""
    decision: DecisionEnum
    analisis_razon_negocios: AnalisisRazonNegocios
    analisis_bee: AnalisisBEE
    condiciones_estrategicas_avance: List[str] = []
    requisitos_para_sow: List[str] = []
    riesgo_puntos_razon_negocios: int = Field(..., ge=0, le=25)
    riesgo_puntos_beneficio_economico: int = Field(..., ge=0, le=25)


class ChecklistEstadoItem(BaseModel):
    item: str
    estado: Literal["CUMPLIDO", "PENDIENTE", "NO_APLICA"]


class DecisionesAgentesResumen(BaseModel):
    A1: Optional[str] = None
    A3: Optional[str] = None
    A4: Optional[str] = None
    A5: Optional[str] = None


class A2PMOOutput(BaseModel):
    """Schema de validación para A2_PMO"""
    estado_global_proyecto: Literal[
        "PENDIENTE",
        "APROBADO_ESTRATEGICO",
        "APROBADO_CONDICIONAL",
        "APROBADO_OPERATIVO",
        "RECHAZADO",
        "BLOQUEADO"
    ]
    fase_actual: str
    checklist_estado: List[ChecklistEstadoItem] = []
    decisiones_agentes_resumen: DecisionesAgentesResumen = DecisionesAgentesResumen()
    bloqueos_activos: List[str] = []
    requiere_revision_humana: bool
    razon_revision_humana: Optional[str] = None
    siguiente_accion: str
    puede_avanzar_fase: bool


class ConclusionPilar(BaseModel):
    status: StatusPilarEnum
    detalle: str = Field(..., min_length=50, description="Mínimo 50 caracteres de detalle")
    riesgo_puntos: int = Field(..., ge=0, le=25)


class ChecklistEvidenciaItem(BaseModel):
    item: str
    obligatorio: bool
    estado: EstadoChecklistEnum
    fase_requerida: str


class AlertaRiesgo(BaseModel):
    tipo_alerta: TipoAlertaEnum
    descripcion: str
    severidad: SeveridadEnum


class ConclusionPorPilar(BaseModel):
    razon_negocios: ConclusionPilar
    beneficio_economico: ConclusionPilar
    materialidad: ConclusionPilar
    trazabilidad: ConclusionPilar


class A3FiscalOutput(BaseModel):
    """Schema de validación para A3_FISCAL (el más crítico)"""
    decision: DecisionEnum
    conclusion_por_pilar: ConclusionPorPilar
    risk_score_total: int = Field(..., ge=0, le=100)
    checklist_evidencia_exigible: List[ChecklistEvidenciaItem] = Field(..., min_length=3)
    alertas_riesgo_especial: List[AlertaRiesgo] = []
    condiciones_para_vbc: List[str] = []
    riesgos_subsistentes: List[str] = []
    requiere_validacion_humana: bool
    justificacion_validacion_humana: Optional[str] = None


class ChecklistContractualItem(BaseModel):
    item: str
    status: Literal["CUMPLIDO", "PENDIENTE", "NO_APLICA"]
    accion_requerida: Optional[str] = None


class AjusteRequerido(BaseModel):
    descripcion: str
    fase_bloquea: str
    criticidad: Literal["BLOQUEANTE", "IMPORTANTE", "MENOR"]


class A4LegalOutput(BaseModel):
    """Schema de validación para A4_LEGAL"""
    decision: Literal["APROBAR", "SOLICITAR_AJUSTES", "RECHAZAR"]
    checklist_contractual: List[ChecklistContractualItem] = Field(..., min_length=5)
    ajustes_requeridos: List[AjusteRequerido] = []
    clausulas_obligatorias_faltantes: List[str] = []
    riesgo_puntos_trazabilidad: int = Field(..., ge=0, le=25)


class AnalisisProporcion(BaseModel):
    costo_vs_ventas_porcentaje: float
    evaluacion_proporcion: Literal["RAZONABLE", "ALTO_PERO_JUSTIFICABLE", "DESPROPORCIONADO"]
    presupuesto_disponible: bool
    centro_costo: str


class EvaluacionBEE(BaseModel):
    roi_evaluacion: str
    horizonte_evaluacion: str
    conclusion: Literal["CONFORME", "CONDICIONADO", "NO_CONFORME"]


class CondicionFinanciera(BaseModel):
    condicion: str
    cumplido: bool


class A5FinanzasOutput(BaseModel):
    """Schema de validación para A5_FINANZAS"""
    decision: Literal["APROBAR", "SOLICITAR_AJUSTES", "RECHAZAR"]
    analisis_proporcion: AnalisisProporcion
    evaluacion_bee: EvaluacionBEE
    condiciones_financieras: List[CondicionFinanciera] = []
    impacto_no_deducibilidad: str
    requiere_evaluacion_f9: bool


class Entregable(BaseModel):
    nombre: str
    tipo: str
    version: str
    fecha_carga: str
    ruta_archivo: str


class A6ProveedorOutput(BaseModel):
    """Schema de validación para A6_PROVEEDOR"""
    entregables_cargados: List[Entregable] = []
    minutas_sesiones: List[str] = []
    estado_avance: str
    pendientes: List[str] = []


class TipologiaEnum(str, Enum):
    CONSULTORIA_ESTRATEGICA = "CONSULTORIA_ESTRATEGICA"
    CONSULTORIA_MACRO_MERCADO = "CONSULTORIA_MACRO_MERCADO"
    SOFTWARE_SAAS_DESARROLLO = "SOFTWARE_SAAS_DESARROLLO"
    MARKETING_BRANDING = "MARKETING_BRANDING"
    INTRAGRUPO_MANAGEMENT_FEE = "INTRAGRUPO_MANAGEMENT_FEE"
    SERVICIOS_ESG_CUMPLIMIENTO = "SERVICIOS_ESG_CUMPLIMIENTO"
    REESTRUCTURAS = "REESTRUCTURAS"
    OTROS = "OTROS"


class ConfianzaEnum(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class NivelRiesgoEnum(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class ImportanciaEnum(str, Enum):
    CRITICO = "CRITICO"
    IMPORTANTE = "IMPORTANTE"
    COMPLEMENTARIO = "COMPLEMENTARIO"


class SubTipificacionOutput(BaseModel):
    """Schema de validación para SUB_TIPIFICACION"""
    tipologia_asignada: TipologiaEnum
    confianza_clasificacion: ConfianzaEnum
    justificacion: str = Field(..., min_length=50)
    palabras_clave_detectadas: List[str] = []
    alertas_tipologia: List[str] = []
    requiere_validacion_humana: bool
    checklist_aplicable: str


class MatrizMaterialidadItem(BaseModel):
    hecho_relevante: str
    fase: str
    evidencia_esperada: str
    evidencia_encontrada: Optional[str] = None
    documento_id: Optional[str] = None
    estado: Literal["OK", "FALTA", "INCONSISTENTE"]


class BrechaCritica(BaseModel):
    hecho: str
    fase: str
    impacto: str
    accion_requerida: str


class SubMaterialidadOutput(BaseModel):
    """Schema de validación para SUB_MATERIALIDAD"""
    matriz_materialidad: List[MatrizMaterialidadItem] = []
    completitud_porcentaje: float = Field(..., ge=0, le=100)
    items_ok: int = Field(..., ge=0)
    items_total: int = Field(..., ge=0)
    brechas_criticas: List[BrechaCritica] = []
    puede_emitir_vbc: bool
    razon_bloqueo_vbc: Optional[str] = None


class AlertaRiesgoEspecial(BaseModel):
    tipo_riesgo: TipoAlertaEnum
    severidad: SeveridadEnum
    descripcion: str
    evidencia: str
    accion_requerida: str
    bloquea_avance: bool


class SubRiesgosEspecialesOutput(BaseModel):
    """Schema de validación para SUB_RIESGOS_ESPECIALES"""
    alertas_detectadas: List[AlertaRiesgoEspecial] = []
    nivel_riesgo_global: NivelRiesgoEnum
    puede_continuar: bool
    condiciones_para_continuar: List[str] = []
    requiere_revision_humana_inmediata: bool
    recomendacion: str


class EvaluacionCriterio(BaseModel):
    score: int = Field(..., ge=0, le=100)
    fortalezas: List[str] = []
    debilidades: List[str] = []


class EvaluacionPorCriterio(BaseModel):
    razon_negocios: EvaluacionCriterio
    beneficio_economico: EvaluacionCriterio
    materialidad: EvaluacionCriterio
    trazabilidad: EvaluacionCriterio
    coherencia_global: EvaluacionCriterio


class DocumentoClave(BaseModel):
    tipo_documento: str
    nombre: str
    importancia: ImportanciaEnum
    presente: bool
    observaciones: str


class PuntoVulnerable(BaseModel):
    vulnerabilidad: str
    impacto_potencial: str
    mitigacion_sugerida: str


class A7DefensaOutput(BaseModel):
    """Schema de validación para A7_DEFENSA"""
    defense_file_completo: bool
    indice_defendibilidad: int = Field(..., ge=0, le=100)
    evaluacion_por_criterio: EvaluacionPorCriterio
    documentos_clave: List[DocumentoClave] = []
    argumentos_defensa: List[str] = []
    puntos_vulnerables: List[PuntoVulnerable] = []
    recomendaciones_refuerzo: List[str] = []
    conclusion: str


AGENT_OUTPUT_SCHEMAS = {
    "A1_SPONSOR": A1SponsorOutput,
    "A2_PMO": A2PMOOutput,
    "A3_FISCAL": A3FiscalOutput,
    "A4_LEGAL": A4LegalOutput,
    "A5_FINANZAS": A5FinanzasOutput,
    "A6_PROVEEDOR": A6ProveedorOutput,
    "SUB_TIPIFICACION": SubTipificacionOutput,
    "SUB_MATERIALIDAD": SubMaterialidadOutput,
    "SUB_RIESGOS_ESPECIALES": SubRiesgosEspecialesOutput,
    "A7_DEFENSA": A7DefensaOutput
}
