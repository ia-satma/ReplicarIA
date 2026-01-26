"""
Knowledge Base Models for Bibliotecar.IA
Document versioning, alerts, and dashboard models
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    LEY = "ley"
    REGLAMENTO = "reglamento"
    RMF = "rmf"
    CRITERIO = "criterio"
    JURISPRUDENCIA = "jurisprudencia"
    TESIS = "tesis"
    OPINION = "opinion"
    CONFERENCIA = "conferencia"
    CONTRATO = "contrato"
    OTRO = "otro"


class ChangeType(str, Enum):
    ORIGINAL = "original"
    REFORMA = "reforma"
    ADICION = "adicion"
    DEROGACION = "derogacion"
    FE_ERRATAS = "fe_erratas"
    INTERPRETACION = "interpretacion"


class KnowledgeState(str, Enum):
    COMPLETO = "completo"
    ACTUALIZABLE = "actualizable"
    INCOMPLETO = "incompleto"
    CRITICO = "critico"
    EN_REVISION = "en_revision"


class AlertType(str, Enum):
    ACTUALIZACION = "actualizacion"
    FALTANTE = "faltante"
    VENCIMIENTO = "vencimiento"
    CALIDAD = "calidad"


class Priority(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class DocumentVersion(BaseModel):
    """Version model for legal documents"""
    document_id: str
    version_id: str
    document_type: DocumentType
    ordenamiento: str
    nombre_completo: str
    version: str
    fecha_publicacion: datetime
    fecha_inicio_vigencia: datetime
    fecha_fin_vigencia: Optional[datetime] = None
    es_vigente: bool = True
    tipo_cambio: ChangeType = ChangeType.ORIGINAL
    version_anterior: Optional[str] = None
    version_siguiente: Optional[str] = None
    documentos_relacionados: List[str] = []
    dof_fecha_publicacion: Optional[datetime] = None
    dof_enlace: Optional[str] = None
    decreto_numero: Optional[str] = None
    articulos_modificados: List[str] = []
    resumen_cambios: Optional[str] = None
    fecha_ingestion: datetime = Field(default_factory=datetime.utcnow)
    usuario_ingestion: Optional[str] = None
    chunks_generados: int = 0
    score_calidad: float = 0.0


class ArticleInterpretation(BaseModel):
    """Interpretation of an article"""
    tipo: str
    identificador: str
    fecha: datetime
    resumen: str


class ArticleVersion(BaseModel):
    """Version of an article"""
    version: str
    fecha_vigencia: datetime
    texto: str
    cambio_tipo: str
    cambio_descripcion: Optional[str] = None


class ArticleHistory(BaseModel):
    """History of an article across versions"""
    ordenamiento: str
    articulo: str
    versiones: List[ArticleVersion] = []
    interpretaciones: List[ArticleInterpretation] = []


class KBCategory(BaseModel):
    """Knowledge base category"""
    nombre: str
    icono: str
    documentos: int = 0
    estado: KnowledgeState = KnowledgeState.INCOMPLETO
    completitud: float = 0.0
    ultima_actualizacion: Optional[datetime] = None
    alertas: int = 0


class KBAlert(BaseModel):
    """Knowledge base alert"""
    id: str
    tipo: AlertType
    prioridad: Priority
    mensaje: str
    categoria: str
    accion: str
    fecha_deteccion: datetime = Field(default_factory=datetime.utcnow)
    resuelta: bool = False


class KBSolicitud(BaseModel):
    """Document request from agents"""
    id: str
    documento: str
    razon: str
    solicitado_por: List[str] = []
    prioridad: Priority = Priority.MEDIA
    fecha_solicitud: datetime = Field(default_factory=datetime.utcnow)
    completada: bool = False


class KBDashboard(BaseModel):
    """Knowledge base dashboard summary"""
    total_documentos: int = 0
    total_chunks: int = 0
    ultima_actualizacion: Optional[datetime] = None
    score_promedio: float = 0.0
    completitud_general: float = 0.0
    categorias: List[KBCategory] = []
    alertas: List[KBAlert] = []
    solicitudes: List[KBSolicitud] = []


class IngestionRequest(BaseModel):
    """Request to ingest a document"""
    documento_tipo: DocumentType
    ordenamiento: str
    nombre: str
    version: str
    fecha_publicacion: datetime
    contenido: Optional[str] = None
    archivo_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class IngestionResult(BaseModel):
    """Result of document ingestion"""
    success: bool
    document_id: Optional[str] = None
    version_id: Optional[str] = None
    chunks_generados: int = 0
    mensaje: str = ""
    errores: List[str] = []


class ChatMessage(BaseModel):
    """Chat message for Bibliotecar.IA"""
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class BibliotecaContext(BaseModel):
    """Context for Bibliotecar.IA conversation"""
    session_id: str
    messages: List[ChatMessage] = []
    current_action: Optional[str] = None
    pending_ingestion: Optional[IngestionRequest] = None
    empresa_id: Optional[str] = None
