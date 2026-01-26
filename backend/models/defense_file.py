from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SeccionDefenseFile(str, Enum):
    CARATULA = "01_CARATULA"
    RESUMEN_EJECUTIVO = "02_RESUMEN_EJECUTIVO"
    INDICE = "03_INDICE"
    ANTECEDENTES = "04_ANTECEDENTES"
    RAZON_NEGOCIOS = "05_RAZON_NEGOCIOS"
    BENEFICIO_ECONOMICO = "06_BENEFICIO_ECONOMICO"
    MATERIALIDAD = "07_MATERIALIDAD"
    FISCAL = "08_FISCAL"
    PROVEEDOR = "09_PROVEEDOR"
    LEGAL = "10_LEGAL"
    EVIDENCIAS = "11_EVIDENCIAS"
    TIMELINE = "12_TIMELINE"
    CONCLUSIONES = "13_CONCLUSIONES"
    ANEXOS = "14_ANEXOS"
    METODOLOGIA = "15_METODOLOGIA"

class DocumentoEvidencia(BaseModel):
    nombre: str
    tipo: str  # CONTRATO, MINUTA, ENTREGABLE, CFDI, PAGO, etc.
    descripcion: str
    url_pcloud: Optional[str] = None
    fecha: datetime
    hash_sha256: Optional[str] = None
    relevancia: str  # CRITICA, ALTA, MEDIA, BAJA

class HitoTimeline(BaseModel):
    fecha: datetime
    fase: str  # F0-F9
    evento: str
    descripcion: str
    documentos_relacionados: List[str] = []
    agente_responsable: Optional[str] = None

class SeccionContenido(BaseModel):
    seccion_id: SeccionDefenseFile
    titulo: str
    contenido: str
    fuentes_normativas: List[str] = []
    documentos_soporte: List[DocumentoEvidencia] = []
    dictamen_agente: Optional[str] = None  # A1, A3, A4, A5, A6
    estado: str = "PENDIENTE"  # PENDIENTE, EN_PROCESO, COMPLETO

class ResumenDictamenes(BaseModel):
    a1_estrategia: Optional[Dict[str, Any]] = None
    a3_fiscal: Optional[Dict[str, Any]] = None
    a4_legal: Optional[Dict[str, Any]] = None
    a5_finanzas: Optional[Dict[str, Any]] = None
    a6_proveedor: Optional[Dict[str, Any]] = None

class MatrizMaterialidad(BaseModel):
    categoria: str
    evidencia_requerida: str
    evidencia_presente: bool
    documento_soporte: Optional[str] = None
    observaciones: Optional[str] = None

class DefenseFileJson(BaseModel):
    """Estructura completa del Defense File"""
    # Metadata
    id: str
    proyecto_id: str
    empresa_id: str
    version: str = "1.0"
    fecha_generacion: datetime = Field(default_factory=datetime.utcnow)
    generado_por: str = "A7_DEFENSA"
    
    # Datos del proyecto
    nombre_proyecto: str
    descripcion_proyecto: str
    tipo_servicio: str
    monto_total: float
    proveedor_nombre: str
    proveedor_rfc: str
    
    # Periodo
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    
    # Secciones del Defense File
    secciones: List[SeccionContenido] = []
    
    # Resumen de dictámenes de agentes
    dictamenes: ResumenDictamenes
    
    # Timeline del proyecto
    timeline: List[HitoTimeline] = []
    
    # Matriz de materialidad
    matriz_materialidad: List[MatrizMaterialidad] = []
    
    # Documentos del expediente
    documentos: List[DocumentoEvidencia] = []
    
    # Métricas
    score_materialidad: int = Field(ge=0, le=100, default=0)
    score_trazabilidad: int = Field(ge=0, le=100, default=0)
    score_defensa: int = Field(ge=0, le=100, default=0)
    
    # Estado general
    estado: str = "EN_CONSTRUCCION"  # EN_CONSTRUCCION, COMPLETO, VALIDADO, ARCHIVADO
    
    # Observaciones y recomendaciones
    fortalezas: List[str] = []
    debilidades: List[str] = []
    recomendaciones: List[str] = []
