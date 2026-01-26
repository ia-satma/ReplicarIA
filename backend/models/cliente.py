"""
Modelo de Cliente para arquitectura multi-tenant.
Los clientes pertenecen a una empresa (tenant) y representan 
las empresas que el tenant está auditando/consultando.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import uuid


class TipoCliente(str, Enum):
    PERSONA_MORAL = "persona_moral"
    PERSONA_FISICA = "persona_fisica"


class EstadoCliente(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    PROSPECTO = "prospecto"
    SUSPENDIDO = "suspendido"


class ContactoCliente(BaseModel):
    nombre: str
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: bool = False


class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    empresa_id: str
    
    razon_social: str
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    tipo: TipoCliente = TipoCliente.PERSONA_MORAL
    
    direccion_fiscal: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    pais: str = "México"
    
    regimen_fiscal: Optional[str] = None
    actividad_economica: Optional[str] = None
    giro: Optional[str] = None
    
    representante_legal: Optional[str] = None
    contactos: List[ContactoCliente] = []
    
    sitio_web: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    
    notas: Optional[str] = None
    etiquetas: List[str] = []
    documentos_ids: List[str] = []
    
    status: EstadoCliente = EstadoCliente.ACTIVO
    fecha_alta: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ClienteCreate(BaseModel):
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    tipo: TipoCliente = TipoCliente.PERSONA_MORAL
    direccion_fiscal: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    actividad_economica: Optional[str] = None
    giro: Optional[str] = None
    representante_legal: Optional[str] = None
    contactos: List[ContactoCliente] = []
    sitio_web: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    notas: Optional[str] = None
    etiquetas: List[str] = []


class ClienteUpdate(BaseModel):
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    tipo: Optional[TipoCliente] = None
    direccion_fiscal: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    actividad_economica: Optional[str] = None
    giro: Optional[str] = None
    representante_legal: Optional[str] = None
    contactos: Optional[List[ContactoCliente]] = None
    sitio_web: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    notas: Optional[str] = None
    etiquetas: Optional[List[str]] = None
    status: Optional[EstadoCliente] = None


class ClienteResponse(BaseModel):
    id: str
    empresa_id: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    tipo: str = "persona_moral"
    status: str = "activo"
    ciudad: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    fecha_alta: Optional[datetime] = None
    giro: Optional[str] = None
    actividad_economica: Optional[str] = None
