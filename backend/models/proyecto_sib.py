from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TipoBeneficio(str, Enum):
    INGRESOS = "INGRESOS"
    AHORROS = "AHORROS"
    MITIGACION_RIESGO = "MITIGACION_RIESGO"
    CUMPLIMIENTO = "CUMPLIMIENTO"
    EFICIENCIA = "EFICIENCIA"

class EstadoA1(str, Enum):
    CONFORME = "CONFORME"
    CONDICIONADA = "CONDICIONADA"
    NO_CONFORME = "NO_CONFORME"

class RecomendacionF2(str, Enum):
    AVANZAR = "AVANZAR"
    REPLANTEAR = "REPLANTEAR"
    NO_AVANZAR = "NO_AVANZAR"

class KPI(BaseModel):
    nombre: str
    valor_objetivo: str
    unidad: str
    horizonte_meses: int

class VinculacionEstrategica(BaseModel):
    pilar_estrategico: Optional[str] = None
    okr_relacionado: Optional[str] = None
    iniciativa_origen: Optional[str] = None

class FormularioSIB(BaseModel):
    """Service Initiation Brief - Formulario inicial del proyecto"""
    nombre_proyecto: str
    descripcion: str
    tipo_servicio: str
    
    problema_a_resolver: str
    objetivo_principal: str
    objetivos_secundarios: List[str] = []
    
    tipo_beneficio: TipoBeneficio
    descripcion_beneficio: str
    mecanismo_causa_efecto: str
    
    kpis: List[KPI] = []
    horizonte_meses: int = Field(ge=1, le=60)
    
    vinculacion: VinculacionEstrategica
    
    supuestos: List[str] = []
    
    monto_estimado: float
    proveedor_propuesto: Optional[str] = None
    fecha_inicio_estimada: Optional[datetime] = None
    
    solicitante: str
    area_solicitante: str
    fecha_solicitud: datetime = Field(default_factory=datetime.utcnow)

class ScoreDetalleA1(BaseModel):
    sustancia_economica: int = Field(ge=0, le=5)
    proposito_concreto: int = Field(ge=0, le=5)
    coherencia_estrategica: int = Field(ge=0, le=5)
    bee_describible: int = Field(ge=0, le=5)
    documentacion_contemporanea: int = Field(ge=0, le=5)
    total: int = Field(ge=0, le=25)

class RedFlagA1(BaseModel):
    codigo: str
    descripcion: str
    severidad: str
    detectado: bool = False

class DictamenA1(BaseModel):
    """Dictamen de A1_ESTRATEGIA"""
    proyecto_id: str
    
    razon_negocios_identificada: str
    razon_negocios_solidez: str
    
    bee_tipo: TipoBeneficio
    bee_descripcion: str
    bee_mecanismo: str
    bee_horizonte_meses: int
    
    score: ScoreDetalleA1
    
    red_flags: List[RedFlagA1] = []
    
    estado: EstadoA1
    recomendacion_f2: RecomendacionF2
    
    observaciones: str
    areas_mejora: List[str] = []
    
    fecha_dictamen: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
