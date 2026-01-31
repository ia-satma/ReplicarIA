"""
Modelo de Empresa/Tenant para arquitectura multi-tenant.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class IndustriaEnum(str, Enum):
    CONSTRUCCION = "construccion"
    SERVICIOS_PROFESIONALES = "servicios_profesionales"
    MANUFACTURA = "manufactura"
    COMERCIO = "comercio"
    TECNOLOGIA = "tecnologia"
    SALUD = "salud"
    EDUCACION = "educacion"
    HOTELERIA_RESTAURANTES = "hoteleria_restaurantes"
    TRANSPORTE_LOGISTICA = "transporte_logistica"
    INMOBILIARIO = "inmobiliario"
    OTRO = "otro"


class PilarEstrategico(BaseModel):
    nombre: str
    descripcion: str
    peso: float = 0.25


class OKR(BaseModel):
    objetivo: str
    key_results: List[str]
    periodo: str
    responsable: Optional[str] = None


class ConfiguracionTipologia(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    habilitada: bool = True
    checklist_documentos: List[str]
    criterios_adicionales: Optional[dict] = None


class Empresa(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre_comercial: str
    razon_social: str
    rfc: str
    industria: IndustriaEnum
    sub_industria: Optional[str] = None
    # Datos de contacto
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sitio_web: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    # Estrategia
    vision: Optional[str] = None
    mision: Optional[str] = None
    valores: List[str] = []
    pilares_estrategicos: List[PilarEstrategico] = []
    mercados_objetivo: List[str] = []
    competidores_principales: List[str] = []
    ventajas_competitivas: List[str] = []
    modelo_negocio: Optional[str] = None
    okrs: List[OKR] = []
    tipologias_configuradas: List[ConfiguracionTipologia] = []
    rag_collection_id: Optional[str] = None
    fecha_alta: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)
    activa: bool = True
    plan: str = "basico"
    admin_user_ids: List[str] = []


class EmpresaCreate(BaseModel):
    nombre_comercial: str
    razon_social: str
    rfc: str
    industria: IndustriaEnum
    sub_industria: Optional[str] = None


class EmpresaUpdate(BaseModel):
    nombre_comercial: Optional[str] = None
    vision: Optional[str] = None
    mision: Optional[str] = None
    valores: Optional[List[str]] = None
    pilares_estrategicos: Optional[List[PilarEstrategico]] = None
    mercados_objetivo: Optional[List[str]] = None
    okrs: Optional[List[OKR]] = None
    tipologias_configuradas: Optional[List[ConfiguracionTipologia]] = None
