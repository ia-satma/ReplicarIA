"""
MODELOS DE VERSIONAMIENTO Y BITÁCORA
Sistema completo de control de versiones para expedientes de defensa fiscal
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import hashlib
import json

try:
    from beanie import Document, Indexed
    from pydantic import BaseModel, Field
    USE_BEANIE = True
except ImportError:
    from pydantic import BaseModel, Field
    USE_BEANIE = False
    Document = BaseModel
    Indexed = lambda x: x


class TipoCambio(str, Enum):
    """Tipos de cambios que se pueden registrar"""
    CREACION = "creacion"
    DOCUMENTO_AGREGADO = "documento_agregado"
    DOCUMENTO_ELIMINADO = "documento_eliminado"
    DOCUMENTO_ACTUALIZADO = "documento_actualizado"
    VALIDACION_OCR = "validacion_ocr"
    SIMULACION_RED_TEAM = "simulacion_red_team"
    CORRECCION_VULNERABILIDAD = "correccion_vulnerabilidad"
    CAMBIO_DATOS_PROYECTO = "cambio_datos_proyecto"
    COMUNICACION_PROVEEDOR = "comunicacion_proveedor"
    COMUNICACION_CLIENTE = "comunicacion_cliente"
    AJUSTE_MONTO = "ajuste_monto"
    AJUSTE_FECHA = "ajuste_fecha"
    REGENERACION_EXPEDIENTE = "regeneracion_expediente"
    NOTA_INTERNA = "nota_interna"
    APROBACION = "aprobacion"
    RECHAZO = "rechazo"
    # NUEVOS TIPOS para trazabilidad de agentes
    OPINION_AGENTE = "opinion_agente"  # Opinión/deliberación de un agente
    OPINION_SUBAGENTE = "opinion_subagente"  # Opinión de un subagente
    ORDEN_COMPRA = "orden_compra"  # Generación de orden de compra
    SOLICITUD_CONTRATO = "solicitud_contrato"  # Solicitud de contrato a Legal
    SOLICITUD_CAMBIO_PROVEEDOR = "solicitud_cambio_proveedor"  # Cambio solicitado al proveedor
    CONSOLIDACION_PMO = "consolidacion_pmo"  # Consolidación del PMO
    VALIDACION_FISCAL = "validacion_fiscal"  # Validación fiscal por A3
    VALIDACION_FINANZAS = "validacion_finanzas"  # Validación financiera por A5
    VALIDACION_LEGAL = "validacion_legal"  # Validación legal por A4
    VALIDACION_ESTRATEGIA = "validacion_estrategia"  # Validación estratégica por A1
    CLASIFICACION_SERVICIO = "clasificacion_servicio"  # Clasificación por subagente tipificación
    EVALUACION_MATERIALIDAD = "evaluacion_materialidad"  # Evaluación por subagente materialidad
    EVALUACION_RIESGOS = "evaluacion_riesgos"  # Evaluación por subagente riesgos
    GENERACION_DEFENSE_FILE = "generacion_defense_file"  # Generación de expediente defensa
    AUDITORIA_DOCUMENTAL = "auditoria_documental"  # Auditoría por A8
    OTRO = "otro"


class Severidad(str, Enum):
    """Severidad del cambio para filtrado"""
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    INFO = "info"


class EntradaBitacora(BaseModel):
    """Una entrada individual en la bitácora de cambios con aislamiento multi-tenant"""
    
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    empresa_id: Optional[str] = None
    
    usuario: str
    rol_usuario: Optional[str] = None
    
    tipo_cambio: TipoCambio
    severidad: Severidad = Severidad.MEDIA
    
    titulo: str
    descripcion: str
    
    campo_afectado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    
    documento_id: Optional[str] = None
    documento_nombre: Optional[str] = None
    
    es_comunicacion_externa: bool = False
    contraparte: Optional[str] = None
    referencia_comunicacion: Optional[str] = None
    
    adjuntos: List[str] = Field(default_factory=list)
    
    ip_origen: Optional[str] = None
    navegador: Optional[str] = None
    notas_adicionales: Optional[str] = None
    
    class Config:
        use_enum_values = True


class VersionExpediente(BaseModel):
    """Representa una versión completa del expediente"""
    
    version_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    numero_version: int
    folio_completo: str
    
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_modificacion: datetime = Field(default_factory=datetime.now)
    
    estado: str = "borrador"
    
    snapshot_proyecto: Dict[str, Any] = Field(default_factory=dict)
    snapshot_documentos: List[Dict[str, Any]] = Field(default_factory=list)
    snapshot_risk_score: Optional[float] = None
    snapshot_red_team: Optional[Dict[str, Any]] = None
    
    pdf_path: Optional[str] = None
    zip_path: Optional[str] = None
    
    hash_contenido: Optional[str] = None
    
    motivo_version: str = ""
    creado_por: str = ""
    
    cambios_desde_anterior: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ProyectoVersionado(Document if USE_BEANIE else BaseModel):
    """Proyecto con sistema de versionamiento completo y aislamiento multi-tenant"""
    
    proyecto_id: str = Indexed(str) if USE_BEANIE else ""
    empresa_id: Optional[str] = None
    nombre: str = ""
    
    folio_base: str = ""
    
    version_actual: int = 1
    
    versiones: List[VersionExpediente] = Field(default_factory=list)
    
    bitacora: List[EntradaBitacora] = Field(default_factory=list)
    
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_ultima_modificacion: datetime = Field(default_factory=datetime.now)
    creado_por: str = ""
    
    estado_expediente: str = "en_proceso"
    
    class Settings:
        name = "proyectos_versionados"
    
    def obtener_folio_actual(self) -> str:
        """Retorna folio con versión actual"""
        return f"{self.folio_base}-v{self.version_actual}"
    
    def obtener_version(self, numero: int) -> Optional[VersionExpediente]:
        """Obtiene una versión específica"""
        for v in self.versiones:
            if v.numero_version == numero:
                return v
        return None
    
    def obtener_ultima_version(self) -> Optional[VersionExpediente]:
        """Obtiene la versión más reciente"""
        if self.versiones:
            return max(self.versiones, key=lambda v: v.numero_version)
        return None


def generar_folio_base(
    rfc: str,
    proyecto_id: str,
    fecha: datetime = None
) -> str:
    """Genera folio base sin versión"""
    fecha = fecha or datetime.now()
    timestamp = fecha.strftime("%Y%m%d")
    rfc_suffix = (rfc[-4:] if rfc else "XXXX").upper()
    id_suffix = str(proyecto_id)[-4:].zfill(4)
    
    return f"DUR-{timestamp}-{rfc_suffix}-{id_suffix}"


def generar_hash_contenido(datos: Dict[str, Any]) -> str:
    """Genera hash SHA-256 del contenido para verificar integridad"""
    contenido = json.dumps(datos, sort_keys=True, default=str)
    return hashlib.sha256(contenido.encode()).hexdigest()


def crear_entrada_bitacora(
    usuario: str,
    tipo: TipoCambio,
    titulo: str,
    descripcion: str,
    empresa_id: Optional[str] = None,
    **kwargs
) -> EntradaBitacora:
    """Helper para crear entradas de bitácora con aislamiento multi-tenant"""
    return EntradaBitacora(
        usuario=usuario,
        tipo_cambio=tipo,
        titulo=titulo,
        descripcion=descripcion,
        empresa_id=empresa_id,
        **kwargs
    )
