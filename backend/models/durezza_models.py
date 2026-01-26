"""
Revisar.IA - Pydantic Models for MongoDB
Complete data models for the fiscal audit system
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
import uuid

from .durezza_enums import (
    TipologiaProyecto, FaseProyecto, EstadoGlobal, TipoRelacionProveedor,
    EstadoFase, TipoAgente, DecisionAgente, TipoDocumento, AccionAuditLog,
    StatusPilar, EstadoEvidencia, ResponsableChecklist, EstadoMaterialidad
)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ConclusionPilar(BaseModel):
    status: StatusPilar = StatusPilar.CONDICIONADO
    detalle: str = ""
    riesgo_puntos: int = Field(default=0, ge=0, le=25)


class ChecklistEvidenciaItem(BaseModel):
    item: str
    obligatorio: bool = True
    estado: EstadoEvidencia = EstadoEvidencia.PENDIENTE
    fase_requerida: str = ""


class AnalisisEstructurado(BaseModel):
    conclusion_por_pilar: Dict[str, ConclusionPilar] = Field(default_factory=lambda: {
        "razon_negocios": ConclusionPilar(),
        "beneficio_economico": ConclusionPilar(),
        "materialidad": ConclusionPilar(),
        "trazabilidad": ConclusionPilar()
    })
    checklist_evidencia: List[ChecklistEvidenciaItem] = Field(default_factory=list)
    condiciones_avance_fase: List[str] = Field(default_factory=list)
    riesgos_subsistentes: List[str] = Field(default_factory=list)


class Supplier(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    nombre_razon_social: str = Field(..., max_length=300)
    nombre_comercial: Optional[str] = None
    rfc: str = Field(..., max_length=13)
    tipo_relacion: TipoRelacionProveedor = TipoRelacionProveedor.TERCERO_INDEPENDIENTE
    pais: str = "México"
    jurisdiccion: Optional[str] = None
    direccion: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_email: Optional[str] = None
    contacto_telefono: Optional[str] = None
    historial_riesgo_score: int = Field(default=0, ge=0, le=100)
    proyectos_previos_count: int = Field(default=0, ge=0)
    monto_acumulado_periodo: float = Field(default=0.0, ge=0)
    ultimo_proyecto_fecha: Optional[datetime] = None
    alerta_efos: bool = False
    alerta_efos_fecha: Optional[datetime] = None
    alerta_efos_detalle: Optional[str] = None
    alerta_lista_negra: bool = False
    alerta_tp_pendiente: bool = False
    notas_fiscales: Optional[str] = None
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Project(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    nombre: str = Field(..., max_length=200)
    descripcion: str
    monto: float = Field(..., ge=0)
    moneda: str = "MXN"
    tipologia: TipologiaProyecto = TipologiaProyecto.OTROS
    sponsor_interno: str
    area_solicitante: Optional[str] = None
    proveedor_id: Optional[str] = None
    fase_actual: FaseProyecto = FaseProyecto.F0
    estado_global: EstadoGlobal = EstadoGlobal.PENDIENTE
    risk_score_total: int = Field(default=0, ge=0, le=100)
    risk_score_razon_negocios: int = Field(default=0, ge=0, le=25)
    risk_score_beneficio_economico: int = Field(default=0, ge=0, le=25)
    risk_score_materialidad: int = Field(default=0, ge=0, le=25)
    risk_score_trazabilidad: int = Field(default=0, ge=0, le=25)
    bee_objetivo: Optional[str] = None
    bee_roi_esperado: Optional[float] = None
    bee_horizonte_meses: Optional[int] = None
    bee_indicadores_exito: List[str] = Field(default_factory=list)
    vinculo_plan_estrategico: Optional[str] = None
    justificacion_necesidad: Optional[str] = None
    requiere_revision_humana: bool = False
    revision_humana_obtenida: bool = False
    revisor_humano_nombre: Optional[str] = None
    fecha_revision_humana: Optional[datetime] = None
    defense_file_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        use_enum_values = True


class ProjectPhase(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    proyecto_id: str
    fase: FaseProyecto
    estado: EstadoFase = EstadoFase.NO_INICIADA
    checklist_total_items: int = Field(default=0, ge=0)
    checklist_items_cumplidos: int = Field(default=0, ge=0)
    documentos_requeridos: List[Dict[str, Any]] = Field(default_factory=list)
    documentos_entregados: List[Dict[str, Any]] = Field(default_factory=list)
    decisiones_agentes: Dict[str, Any] = Field(default_factory=dict)
    condiciones_pendientes: List[str] = Field(default_factory=list)
    bloqueos_activos: List[str] = Field(default_factory=list)
    fecha_inicio: Optional[datetime] = None
    fecha_completado: Optional[datetime] = None
    revisor_humano_requerido: bool = False
    revisor_humano_nombre: Optional[str] = None
    revisor_humano_aprobacion: Optional[bool] = None
    fecha_aprobacion_humana: Optional[datetime] = None
    notas: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def checklist_porcentaje(self) -> float:
        if self.checklist_total_items == 0:
            return 0.0
        return (self.checklist_items_cumplidos / self.checklist_total_items) * 100

    @property
    def dias_en_fase(self) -> Optional[int]:
        if not self.fecha_inicio:
            return None
        end = self.fecha_completado or datetime.utcnow()
        return (end - self.fecha_inicio).days

    class Config:
        use_enum_values = True


class AgentDeliberation(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    proyecto_id: str
    fase: str
    agente: TipoAgente
    version: int = Field(default=1, ge=1)
    decision: DecisionAgente = DecisionAgente.PENDIENTE
    analisis_completo: str
    analisis_estructurado: AnalisisEstructurado = Field(default_factory=AnalisisEstructurado)
    risk_score_calculado: int = Field(default=0, ge=0, le=100)
    requiere_validacion_humana: bool = False
    justificacion_validacion_humana: Optional[str] = None
    validacion_humana_obtenida: bool = False
    validador_humano_nombre: Optional[str] = None
    fecha_validacion_humana: Optional[datetime] = None
    prompt_utilizado: Optional[str] = None
    modelo_ia_utilizado: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tiempo_respuesta_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DocumentoDefenseFile(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    tipo: TipoDocumento
    nombre: str
    descripcion: Optional[str] = None
    version: str = "1.0"
    fecha_documento: Optional[datetime] = None
    fecha_carga: datetime = Field(default_factory=datetime.utcnow)
    ruta_archivo: str
    hash_integridad: Optional[str] = None
    tamano_bytes: Optional[int] = None
    fase_generado: Optional[str] = None
    cargado_por: Optional[str] = None

    class Config:
        use_enum_values = True


class MatrizMaterialidadItem(BaseModel):
    hecho_relevante: str
    evidencia_vinculada: List[str] = Field(default_factory=list)
    fase: Optional[str] = None
    responsable: ResponsableChecklist = ResponsableChecklist.INTERNO
    estado: EstadoMaterialidad = EstadoMaterialidad.FALTA
    notas: Optional[str] = None

    class Config:
        use_enum_values = True


class DecisionAprobacion(BaseModel):
    decision: str
    fecha: Optional[datetime] = None


class ResumenAprobacionGlobal(BaseModel):
    estado_final: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    decisiones_por_agente: Dict[str, DecisionAprobacion] = Field(default_factory=dict)
    risk_score_final: int = Field(default=0, ge=0, le=100)
    condiciones_cumplidas: List[str] = Field(default_factory=list)
    observaciones: Optional[str] = None


class DefenseFile(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    proyecto_id: str
    documentos: List[DocumentoDefenseFile] = Field(default_factory=list)
    matriz_materialidad: List[MatrizMaterialidadItem] = Field(default_factory=list)
    matriz_materialidad_completitud: float = Field(default=0.0, ge=0, le=100)
    matriz_materialidad_items_ok: int = Field(default=0, ge=0)
    matriz_materialidad_items_total: int = Field(default=0, ge=0)
    resumen_aprobacion_global: ResumenAprobacionGlobal = Field(default_factory=ResumenAprobacionGlobal)
    indice_defendibilidad: int = Field(default=0, ge=0, le=100)
    fortalezas_probatorias: List[str] = Field(default_factory=list)
    debilidades_identificadas: List[str] = Field(default_factory=list)
    recomendaciones_refuerzo: List[str] = Field(default_factory=list)
    vbc_fiscal_emitido: bool = False
    vbc_fiscal_fecha: Optional[datetime] = None
    vbc_fiscal_emitido_por: Optional[str] = None
    vbc_legal_emitido: bool = False
    vbc_legal_fecha: Optional[datetime] = None
    vbc_legal_emitido_por: Optional[str] = None
    auditoria_interna_completada: bool = False
    auditoria_interna_fecha: Optional[datetime] = None
    auditoria_interna_resultado: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ChecklistTemplateItem(BaseModel):
    orden: int
    descripcion: str
    obligatorio: bool = True
    tipo_documento_esperado: Optional[str] = None
    responsable: ResponsableChecklist = ResponsableChecklist.INTERNO
    criterio_aceptacion: Optional[str] = None
    ayuda_contextual: Optional[str] = None

    class Config:
        use_enum_values = True


class ChecklistTemplate(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    tipologia: TipologiaProyecto
    fase: FaseProyecto
    items: List[ChecklistTemplateItem] = Field(default_factory=list)
    total_items: int = Field(default=0, ge=0)
    items_obligatorios: int = Field(default=0, ge=0)
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class AgentConfig(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    agente: TipoAgente
    nombre_display: str
    descripcion_rol: str
    contexto_requerido: List[str] = Field(default_factory=list)
    normativa_relevante: List[str] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    plantilla_respuesta: Optional[str] = None
    fases_donde_participa: List[str] = Field(default_factory=list)
    puede_bloquear_avance: bool = False
    puede_aprobar_final: bool = False
    requiere_validacion_humana_default: bool = False
    modelo_ia_preferido: str = "gpt-4"
    temperatura: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=4000, ge=100, le=128000)
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Document(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    proyecto_id: str
    defense_file_id: Optional[str] = None
    tipo: TipoDocumento
    nombre: str = Field(..., max_length=500)
    descripcion: Optional[str] = None
    version: str = "1.0"
    fecha_documento: Optional[datetime] = None
    fase_asociada: Optional[FaseProyecto] = None
    ruta_archivo: str
    nombre_archivo_original: Optional[str] = None
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    tamano_bytes: Optional[int] = None
    hash_sha256: Optional[str] = None
    hash_calculado_fecha: Optional[datetime] = None
    cargado_por: Optional[str] = None
    validado_por: Optional[str] = None
    fecha_validacion: Optional[datetime] = None
    es_version_final: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class AuditLog(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    proyecto_id: Optional[str] = None
    accion: AccionAuditLog
    entidad_tipo: Optional[str] = None
    entidad_id: Optional[str] = None
    descripcion: str
    datos_antes: Optional[Dict[str, Any]] = None
    datos_despues: Optional[Dict[str, Any]] = None
    diff: Optional[Dict[str, Any]] = None
    usuario: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
