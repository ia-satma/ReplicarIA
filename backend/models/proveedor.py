from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field
import uuid


# =============================================================================
# NEW PYDANTIC MODELS FOR A6_PROVEEDOR SCORING
# =============================================================================

class NivelRiesgoProveedor(str, Enum):
    BAJO = "BAJO"
    MEDIO_BAJO = "MEDIO_BAJO"
    MEDIO = "MEDIO"
    MEDIO_ALTO = "MEDIO_ALTO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class RecomendacionA6(str, Enum):
    APROBAR = "APROBAR"
    APROBAR_CON_CONDICIONES = "APROBAR_CON_CONDICIONES"
    RECHAZAR = "RECHAZAR"
    REQUIERE_MAS_INVESTIGACION = "REQUIERE_MAS_INVESTIGACION"


class DatosLegalesFiscales(BaseModel):
    rfc: str
    razon_social: str
    regimen_fiscal: Optional[str] = None
    objeto_social: Optional[str] = None
    fecha_constitucion: Optional[datetime] = None
    capital_social: Optional[float] = None
    representante_legal: Optional[str] = None
    domicilio_fiscal: Optional[str] = None


class DatosContactoOperativos(BaseModel):
    email_principal: Optional[str] = None
    telefono: Optional[str] = None
    sitio_web: Optional[str] = None
    contacto_comercial: Optional[str] = None
    direccion_operativa: Optional[str] = None


class DocumentoProveedor(BaseModel):
    tipo: str  # CSF, ACTA_CONSTITUTIVA, OPINION_32D, REPSE, PODER_LEGAL, etc.
    nombre_archivo: str
    url_pcloud: Optional[str] = None
    fecha_carga: datetime
    fecha_vigencia: Optional[datetime] = None
    verificado: bool = False
    datos_extraidos: Optional[dict] = None  # OCR results


class FlagRiesgo(BaseModel):
    codigo: str  # e.g., "DEFINITIVO_EFOS_69B", "SIN_REPSE_SI_APLICA"
    descripcion: str
    severidad: str  # CRITICO, ALTO, MEDIO, BAJO
    detectado: bool = False
    fecha_deteccion: Optional[datetime] = None


class ScoreDetalleA6(BaseModel):
    capacidad_juridica: int = Field(ge=0, le=20)
    capacidad_material: int = Field(ge=0, le=35)
    cumplimiento_fiscal: int = Field(ge=0, le=35)
    historial_comercial: int = Field(ge=0, le=10)
    total: int = Field(ge=0, le=100)


class RiesgoProveedorA6(BaseModel):
    score: ScoreDetalleA6
    nivel_riesgo: NivelRiesgoProveedor
    flags: List[FlagRiesgo] = []
    recomendacion: RecomendacionA6
    justificacion: str
    fecha_evaluacion: datetime
    evaluado_por: str = "A6_PROVEEDOR"


class ProveedorJson(BaseModel):
    id: Optional[str] = None
    empresa_id: str
    datos_legales_fiscales: DatosLegalesFiscales
    datos_contacto_operativos: DatosContactoOperativos
    documentos: List[DocumentoProveedor] = []
    riesgo: Optional[RiesgoProveedorA6] = None
    estatus_lista_69b: Optional[str] = None  # LIMPIO, PRESUNTO, DEFINITIVO, DESVIRTUADO
    fecha_consulta_69b: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# =============================================================================
# LEGACY DATACLASS MODELS (kept for backward compatibility)
# =============================================================================


class EstatusProveedor(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    BLOQUEADO = "bloqueado"
    PENDIENTE_REVISION = "pendiente_revision"


class TipoPersona(str, Enum):
    MORAL = "moral"
    FISICA = "fisica"


class TipoProveedor(str, Enum):
    CONSULTORIA_MACRO = "CONSULTORIA_MACRO"
    CONSULTORIA_ESTRATEGICA = "CONSULTORIA_ESTRATEGICA"
    SOFTWARE_SAAS = "SOFTWARE_SAAS"
    MARKETING_BRANDING = "MARKETING_BRANDING"
    INTRAGRUPO = "INTRAGRUPO"
    SERVICIOS_ESPECIALIZADOS = "SERVICIOS_ESPECIALIZADOS"
    OUTSOURCING_PERMITIDO = "OUTSOURCING_PERMITIDO"
    OTRO = "OTRO"


class EstatusRfc(str, Enum):
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"
    CANCELADO = "cancelado"
    NO_LOCALIZADO = "no_localizado"


class TipoOpinion(str, Enum):
    POSITIVA = "positiva"
    NEGATIVA = "negativa"
    NO_LOCALIZADO = "no_localizado"
    NO_PRESENTADA = "no_presentada"


class NivelConfianzaOCR(str, Enum):
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"


class NivelRiesgo(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass
class DomicilioFiscal:
    calle: str
    colonia: str
    municipio: str
    estado: str
    codigo_postal: str
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    pais: str = "México"
    es_zona_alto_riesgo: bool = False
    es_domicilio_masivo: bool = False
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomicilioFiscal":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CapitalSocial:
    monto_suscrito: float = 0.0
    monto_pagado: float = 0.0
    moneda: str = "MXN"
    fecha_actualizacion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapitalSocial":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SocioPrincipal:
    nombre: str
    rfc: Optional[str] = None
    porcentaje_participacion: Optional[float] = None
    es_socio_administrador: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SocioPrincipal":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MetadatosOCR:
    ocr_ok: bool = False
    nivel_confianza: Optional[str] = None
    fecha_procesamiento: Optional[str] = None
    errores_extraccion: List[str] = field(default_factory=list)
    campos_extraidos_automaticamente: List[str] = field(default_factory=list)
    campos_corregidos_manualmente: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetadatosOCR":
        if data is None:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DocumentoBase:
    archivo_id: Optional[str] = None
    archivo_url: Optional[str] = None
    nombre_archivo: Optional[str] = None
    pcloud_file_id: Optional[int] = None
    pcloud_public_link: Optional[str] = None
    metadatos_ocr: Optional[MetadatosOCR] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.metadatos_ocr:
            d['metadatos_ocr'] = self.metadatos_ocr.to_dict()
        return d


@dataclass
class ConstanciaSituacionFiscal(DocumentoBase):
    fecha_emision: Optional[str] = None
    estatus_rfc: Optional[str] = None
    fecha_inicio_operaciones: Optional[str] = None
    obligaciones_fiscales: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstanciaSituacionFiscal":
        if data is None:
            return cls()
        metadatos = data.pop('metadatos_ocr', None)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if metadatos:
            obj.metadatos_ocr = MetadatosOCR.from_dict(metadatos)
        return obj


@dataclass
class ActaConstitutiva(DocumentoBase):
    fecha_escritura: Optional[str] = None
    notario: Optional[str] = None
    numero_notaria: Optional[str] = None
    entidad_notaria: Optional[str] = None
    numero_escritura: Optional[str] = None
    folio_mercantil: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActaConstitutiva":
        if data is None:
            return cls()
        metadatos = data.pop('metadatos_ocr', None)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if metadatos:
            obj.metadatos_ocr = MetadatosOCR.from_dict(metadatos)
        return obj


@dataclass
class OpinionCumplimiento(DocumentoBase):
    tipo_opinion: Optional[str] = None
    fecha_emision: Optional[str] = None
    vigencia_hasta: Optional[str] = None
    obligatoria_por_politica: bool = False
    monto_umbral_obligatoriedad: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpinionCumplimiento":
        if data is None:
            return cls()
        metadatos = data.pop('metadatos_ocr', None)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if metadatos:
            obj.metadatos_ocr = MetadatosOCR.from_dict(metadatos)
        return obj


@dataclass
class Repse(DocumentoBase):
    numero_registro: Optional[str] = None
    objeto_autorizado: Optional[str] = None
    actividades_autorizadas: List[str] = field(default_factory=list)
    fecha_registro: Optional[str] = None
    fecha_vigencia: Optional[str] = None
    aplicable: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Repse":
        if data is None:
            return cls()
        metadatos = data.pop('metadatos_ocr', None)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if metadatos:
            obj.metadatos_ocr = MetadatosOCR.from_dict(metadatos)
        return obj


@dataclass
class DocumentosClave:
    constancia_situacion_fiscal: Optional[ConstanciaSituacionFiscal] = None
    acta_constitutiva: Optional[ActaConstitutiva] = None
    opinion_cumplimiento: Optional[OpinionCumplimiento] = None
    repse: Optional[Repse] = None
    documentos_adicionales: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'constancia_situacion_fiscal': self.constancia_situacion_fiscal.to_dict() if self.constancia_situacion_fiscal else None,
            'acta_constitutiva': self.acta_constitutiva.to_dict() if self.acta_constitutiva else None,
            'opinion_cumplimiento': self.opinion_cumplimiento.to_dict() if self.opinion_cumplimiento else None,
            'repse': self.repse.to_dict() if self.repse else None,
            'documentos_adicionales': self.documentos_adicionales
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentosClave":
        if data is None:
            return cls()
        return cls(
            constancia_situacion_fiscal=ConstanciaSituacionFiscal.from_dict(data.get('constancia_situacion_fiscal')) if data.get('constancia_situacion_fiscal') else None,
            acta_constitutiva=ActaConstitutiva.from_dict(data.get('acta_constitutiva')) if data.get('acta_constitutiva') else None,
            opinion_cumplimiento=OpinionCumplimiento.from_dict(data.get('opinion_cumplimiento')) if data.get('opinion_cumplimiento') else None,
            repse=Repse.from_dict(data.get('repse')) if data.get('repse') else None,
            documentos_adicionales=data.get('documentos_adicionales', [])
        )


@dataclass
class ContactoPrincipal:
    nombre_completo: str
    email: str
    telefono: str
    puesto: Optional[str] = None
    email_corporativo: bool = False
    extension: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContactoPrincipal":
        if data is None:
            return cls(nombre_completo="", email="", telefono="")
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RedesSociales:
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    otra: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedesSociales":
        if data is None:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FlagsRiesgo:
    proveedor_reciente: bool = False
    proveedor_muy_reciente: bool = False
    capital_vs_montos_incongruente: bool = False
    sin_opinion_cumplimiento: bool = False
    opinion_negativa: bool = False
    sin_repse_si_aplica: bool = False
    repse_vencido: bool = False
    domicilio_alto_riesgo: bool = False
    rfc_en_lista_69b: bool = False
    rfc_en_lista_efos: bool = False
    objeto_social_incongruente: bool = False
    regimen_fiscal_incongruente: bool = False
    sin_presencia_digital: bool = False
    email_no_coincide_con_dominio: bool = False
    revisado_manualmente: bool = False
    aprobado_con_excepcion: bool = False
    motivo_excepcion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlagsRiesgo":
        if data is None:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_active_flags(self) -> List[str]:
        flags = []
        for field_name, value in asdict(self).items():
            if value is True and field_name not in ['revisado_manualmente', 'aprobado_con_excepcion']:
                flags.append(field_name)
        return flags


@dataclass
class RiesgoProveedor:
    score_fiscal: float = 0.0
    score_legal: float = 0.0
    score_operativo: float = 0.0
    score_general: float = 0.0
    score_materialidad_potencial: float = 0.0
    nivel_riesgo: str = "medio"
    flags: FlagsRiesgo = field(default_factory=FlagsRiesgo)
    comentarios_agente_fiscal: Optional[str] = None
    comentarios_agente_legal: Optional[str] = None
    comentarios_agente_finanzas: Optional[str] = None
    comentarios_agente_proveedor: Optional[str] = None
    fecha_ultima_evaluacion: Optional[str] = None
    historial_evaluaciones: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['flags'] = self.flags.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiesgoProveedor":
        if data is None:
            return cls()
        flags_data = data.pop('flags', None)
        obj = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if flags_data:
            obj.flags = FlagsRiesgo.from_dict(flags_data)
        return obj


@dataclass
class Proveedor:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    empresa_id: str = ""
    razon_social: str = ""
    nombre_comercial: Optional[str] = None
    rfc: str = ""
    regimen_fiscal: str = ""
    clave_regimen_fiscal: Optional[str] = None
    domicilio_fiscal: Optional[DomicilioFiscal] = None
    fecha_constitucion: Optional[str] = None
    fecha_alta_rfc: Optional[str] = None
    objeto_social_relevante: Optional[str] = None
    objeto_social_completo: Optional[str] = None
    capital_social: Optional[CapitalSocial] = None
    tipo_persona: str = "moral"
    socios_principales: List[SocioPrincipal] = field(default_factory=list)
    sitio_web: Optional[str] = None
    sitio_web_verificado: bool = False
    redes_sociales: Optional[RedesSociales] = None
    contacto_principal: Optional[ContactoPrincipal] = None
    contactos_adicionales: List[ContactoPrincipal] = field(default_factory=list)
    tipo_proveedor: str = "OTRO"
    subtipo_proveedor: Optional[str] = None
    descripcion_servicios_ofrecidos: Optional[str] = None
    requiere_repse: bool = False
    tiene_personal_en_sitio: bool = False
    es_servicio_regulado: bool = False
    documentos: Optional[DocumentosClave] = None
    riesgo: Optional[RiesgoProveedor] = None
    estatus: str = "pendiente_revision"
    pcloud_folder_id: Optional[int] = None
    pcloud_folder_path: Optional[str] = None
    fecha_alta: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    usuario_alta: Optional[str] = None
    fecha_ultima_actualizacion: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    usuario_ultima_actualizacion: Optional[str] = None
    version_registro: int = 1
    historial_cambios: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'razon_social': self.razon_social,
            'nombre_comercial': self.nombre_comercial,
            'rfc': self.rfc,
            'regimen_fiscal': self.regimen_fiscal,
            'clave_regimen_fiscal': self.clave_regimen_fiscal,
            'domicilio_fiscal': self.domicilio_fiscal.to_dict() if self.domicilio_fiscal else None,
            'fecha_constitucion': self.fecha_constitucion,
            'fecha_alta_rfc': self.fecha_alta_rfc,
            'objeto_social_relevante': self.objeto_social_relevante,
            'objeto_social_completo': self.objeto_social_completo,
            'capital_social': self.capital_social.to_dict() if self.capital_social else None,
            'tipo_persona': self.tipo_persona,
            'socios_principales': [s.to_dict() for s in self.socios_principales],
            'sitio_web': self.sitio_web,
            'sitio_web_verificado': self.sitio_web_verificado,
            'redes_sociales': self.redes_sociales.to_dict() if self.redes_sociales else None,
            'contacto_principal': self.contacto_principal.to_dict() if self.contacto_principal else None,
            'contactos_adicionales': [c.to_dict() for c in self.contactos_adicionales],
            'tipo_proveedor': self.tipo_proveedor,
            'subtipo_proveedor': self.subtipo_proveedor,
            'descripcion_servicios_ofrecidos': self.descripcion_servicios_ofrecidos,
            'requiere_repse': self.requiere_repse,
            'tiene_personal_en_sitio': self.tiene_personal_en_sitio,
            'es_servicio_regulado': self.es_servicio_regulado,
            'documentos': self.documentos.to_dict() if self.documentos else None,
            'riesgo': self.riesgo.to_dict() if self.riesgo else None,
            'estatus': self.estatus,
            'pcloud_folder_id': self.pcloud_folder_id,
            'pcloud_folder_path': self.pcloud_folder_path,
            'fecha_alta': self.fecha_alta,
            'usuario_alta': self.usuario_alta,
            'fecha_ultima_actualizacion': self.fecha_ultima_actualizacion,
            'usuario_ultima_actualizacion': self.usuario_ultima_actualizacion,
            'version_registro': self.version_registro,
            'historial_cambios': self.historial_cambios
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proveedor":
        if data is None:
            return cls()
        
        proveedor = cls(
            id=data.get('id', str(uuid.uuid4())),
            empresa_id=data.get('empresa_id', ''),
            razon_social=data.get('razon_social', ''),
            nombre_comercial=data.get('nombre_comercial'),
            rfc=data.get('rfc', ''),
            regimen_fiscal=data.get('regimen_fiscal', ''),
            clave_regimen_fiscal=data.get('clave_regimen_fiscal'),
            fecha_constitucion=data.get('fecha_constitucion'),
            fecha_alta_rfc=data.get('fecha_alta_rfc'),
            objeto_social_relevante=data.get('objeto_social_relevante'),
            objeto_social_completo=data.get('objeto_social_completo'),
            tipo_persona=data.get('tipo_persona', 'moral'),
            sitio_web=data.get('sitio_web'),
            sitio_web_verificado=data.get('sitio_web_verificado', False),
            tipo_proveedor=data.get('tipo_proveedor', 'OTRO'),
            subtipo_proveedor=data.get('subtipo_proveedor'),
            descripcion_servicios_ofrecidos=data.get('descripcion_servicios_ofrecidos'),
            requiere_repse=data.get('requiere_repse', False),
            tiene_personal_en_sitio=data.get('tiene_personal_en_sitio', False),
            es_servicio_regulado=data.get('es_servicio_regulado', False),
            estatus=data.get('estatus', 'pendiente_revision'),
            pcloud_folder_id=data.get('pcloud_folder_id'),
            pcloud_folder_path=data.get('pcloud_folder_path'),
            fecha_alta=data.get('fecha_alta', datetime.utcnow().isoformat()),
            usuario_alta=data.get('usuario_alta'),
            fecha_ultima_actualizacion=data.get('fecha_ultima_actualizacion', datetime.utcnow().isoformat()),
            usuario_ultima_actualizacion=data.get('usuario_ultima_actualizacion'),
            version_registro=data.get('version_registro', 1),
            historial_cambios=data.get('historial_cambios', [])
        )

        if data.get('domicilio_fiscal'):
            proveedor.domicilio_fiscal = DomicilioFiscal.from_dict(data['domicilio_fiscal'])
        if data.get('capital_social'):
            proveedor.capital_social = CapitalSocial.from_dict(data['capital_social'])
        if data.get('redes_sociales'):
            proveedor.redes_sociales = RedesSociales.from_dict(data['redes_sociales'])
        if data.get('contacto_principal'):
            proveedor.contacto_principal = ContactoPrincipal.from_dict(data['contacto_principal'])
        if data.get('contactos_adicionales'):
            proveedor.contactos_adicionales = [ContactoPrincipal.from_dict(c) for c in data['contactos_adicionales']]
        if data.get('socios_principales'):
            proveedor.socios_principales = [SocioPrincipal.from_dict(s) for s in data['socios_principales']]
        if data.get('documentos'):
            proveedor.documentos = DocumentosClave.from_dict(data['documentos'])
        if data.get('riesgo'):
            proveedor.riesgo = RiesgoProveedor.from_dict(data['riesgo'])

        return proveedor
