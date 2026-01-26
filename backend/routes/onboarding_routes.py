"""
Rutas de API para el sistema de onboarding inteligente con IA
Permite crear clientes/proveedores analizando documentos y buscando datos en web
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import json
import logging
import uuid
import os
import tempfile
from datetime import datetime, timezone

import asyncpg
from jose import jwt, exceptions as jose_exceptions
from services.document_analyzer import document_analyzer
from services.web_search_service import web_search_service
from services.empresa_service import empresa_service
from services.user_db import user_service
from services.cliente_service import cliente_service
from services.documento_versionado_service import documento_versionado_service
from models.empresa import EmpresaCreate, IndustriaEnum
from repositories.empresa_repository import empresa_repository
from services.deep_research_service import deep_research_service

DATABASE_URL = os.environ.get('DATABASE_URL', '')

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DocxDocument = None
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/archivo", tags=["onboarding"])

security = HTTPBearer(auto_error=False)
SECRET_KEY: str = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY") or "fallback-dev-key"
if SECRET_KEY == "fallback-dev-key":
    logger.error("CRITICAL: SESSION_SECRET or JWT_SECRET_KEY must be configured")
ALGORITHM = "HS256"


class WebSearchRequest(BaseModel):
    datos_actuales: Dict[str, Any]
    campos_faltantes: List[str]


class CrearEntidadRequest(BaseModel):
    tipo: str
    datos: Dict[str, Any]
    email_contacto: Optional[str] = ""
    archivos_ids: Optional[List[str]] = []


class InvestigarEmpresaRequest(BaseModel):
    """Request para investigar empresa automáticamente"""
    sitio_web: Optional[str] = None
    rfc: Optional[str] = None
    nombre: Optional[str] = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual del token JWT o sesión OTP"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Try JWT first
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        pass
    
    # Fallback to OTP session token
    try:
        from services.otp_auth_service import otp_auth_service
        session = await otp_auth_service.validate_session(token)
        if session and session.get("user"):
            user = session["user"]
            return {
                "user_id": user.get("id"),
                "email": user.get("email"),
                "full_name": user.get("nombre"),
                "empresa_id": user.get("empresa"),
                "company_id": user.get("empresa"),
                "role": user.get("rol", "user")
            }
    except Exception as e:
        logger.warning(f"OTP session validation failed: {e}")
    
    return None


@router.get("/status")
async def get_archivo_status():
    """Obtiene el estado del servicio ARCHIVO (onboarding chatbot)"""
    return {
        "active": True,
        "status": "ready",
        "servicio": "ARCHIVO - Onboarding Inteligente",
        "version": "1.0.0",
        "capacidades": [
            "Análisis de documentos (PDF, DOCX, imágenes)",
            "Extracción automática de datos (RFC, razón social, dirección)",
            "Búsqueda web para completar información",
            "Creación de clientes y proveedores",
            "Validación de datos fiscales"
        ],
        "formatos_soportados": {
            "pdf": PYMUPDF_AVAILABLE,
            "docx": DOCX_AVAILABLE,
            "imagenes": True
        },
        "ia_disponible": True
    }


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrae texto de un PDF"""
    if not PYMUPDF_AVAILABLE or fitz is None:
        return "[PDF no soportado - instalar PyMuPDF]"
    
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text = text + str(page_text)
        doc.close()
        return text[:30000]
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        return ""


def extract_text_from_docx(file_content: bytes) -> str:
    """Extrae texto de un archivo DOCX"""
    if not DOCX_AVAILABLE or DocxDocument is None:
        return "[DOCX no soportado - instalar python-docx]"
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        doc = DocxDocument(tmp_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        os.unlink(tmp_path)
        return text[:30000]
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        return ""


async def crear_cliente_postgresql(
    datos: Dict[str, Any],
    empresa_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    origen: str = "chat"
) -> Optional[Dict[str, Any]]:
    """
    Crea un cliente en la tabla PostgreSQL 'clientes' con estado='pendiente'.
    Retorna el cliente creado con su ID.
    """
    if not DATABASE_URL:
        logger.warning("DATABASE_URL no configurada, no se puede crear cliente en PostgreSQL")
        return None
    
    db_url = DATABASE_URL
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = await asyncpg.connect(db_url)
        
        cliente_uuid = str(uuid.uuid4())
        now = datetime.utcnow()
        
        cliente_id = await conn.fetchval(
            """
            INSERT INTO clientes (
                cliente_uuid, nombre, rfc, razon_social, direccion, email, telefono,
                giro, sitio_web, regimen_fiscal, tipo_persona, actividad_economica,
                estado, origen, empresa_id, usuario_responsable_id, activo,
                created_at, updated_at, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            RETURNING id
            """,
            cliente_uuid,
            datos.get("nombre") or datos.get("razon_social") or "Sin nombre",
            datos.get("rfc", "").upper() if datos.get("rfc") else None,
            datos.get("razon_social") or datos.get("nombre"),
            datos.get("direccion"),
            datos.get("email"),
            datos.get("telefono"),
            datos.get("giro"),
            datos.get("sitio_web"),
            datos.get("regimen_fiscal"),
            datos.get("tipo_persona"),
            datos.get("actividad_economica") or datos.get("giro"),
            "pendiente",
            origen,
            empresa_id,
            usuario_id,
            True,
            now,
            now,
            usuario_id
        )
        
        await conn.close()
        
        logger.info(f"Cliente creado en PostgreSQL: id={cliente_id}, uuid={cliente_uuid}")
        
        return {
            "id": cliente_id,
            "cliente_uuid": cliente_uuid,
            "nombre": datos.get("nombre") or datos.get("razon_social"),
            "rfc": datos.get("rfc"),
            "razon_social": datos.get("razon_social") or datos.get("nombre"),
            "estado": "pendiente",
            "origen": origen
        }
        
    except Exception as e:
        logger.error(f"Error creando cliente en PostgreSQL: {e}")
        return None


class DocumentUploadRequest(BaseModel):
    cliente_id: int
    tipo_documento: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None


@router.post("/analizar")
async def analizar_documentos(
    files: List[UploadFile] = File(...),
    tipo_entidad: str = Form("cliente"),
    email_contacto: str = Form(""),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analiza documentos subidos y extrae datos del cliente/proveedor usando IA
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
    
    documentos_procesados = []
    
    for file in files:
        try:
            content = await file.read()
            texto = ""
            filename = file.filename or ""
            
            if file.content_type == "application/pdf" or filename.lower().endswith('.pdf'):
                texto = extract_text_from_pdf(content)
            elif file.content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"] or filename.lower().endswith('.docx'):
                texto = extract_text_from_docx(content)
            elif file.content_type and file.content_type.startswith("text/"):
                texto = content.decode('utf-8', errors='ignore')[:30000]
            else:
                texto = content.decode('utf-8', errors='ignore')[:30000]
            
            if texto.strip():
                documentos_procesados.append({
                    "nombre": file.filename,
                    "texto": texto,
                    "tipo": file.content_type
                })
                
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            continue
    
    if not documentos_procesados:
        raise HTTPException(
            status_code=400, 
            detail="No se pudo extraer texto de ningún documento"
        )
    
    datos = await document_analyzer.analizar_documentos(
        documentos=documentos_procesados,
        tipo_entidad=tipo_entidad
    )
    
    if email_contacto and not datos.get("email"):
        datos["email"] = email_contacto
        if "fuentes" not in datos:
            datos["fuentes"] = []
        datos["fuentes"].append({
            "campo": "email",
            "fuente": "usuario",
            "confianza": 1.0
        })
    
    return {
        "success": True,
        "datos": datos,
        "archivos_procesados": len(documentos_procesados),
        "archivos_nombres": [d["nombre"] for d in documentos_procesados]
    }


@router.post("/buscar-web")
async def buscar_datos_web(request: WebSearchRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Busca datos faltantes de una empresa en fuentes públicas de internet
    """
    nombre = request.datos_actuales.get("nombre") or request.datos_actuales.get("razon_social")
    rfc = request.datos_actuales.get("rfc")
    
    if not nombre and not rfc:
        return {
            "datos_encontrados": {},
            "fuentes_nuevas": [],
            "aun_faltantes": request.campos_faltantes
        }
    
    resultado = await web_search_service.buscar_datos_empresa(
        nombre=nombre,
        rfc=rfc,
        campos_faltantes=request.campos_faltantes
    )
    
    return resultado


@router.post("/investigar")
async def investigar_empresa(
    request: InvestigarEmpresaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Deep Research: Investiga automáticamente una empresa a partir de input mínimo.
    
    Acepta:
    - sitio_web: URL del sitio web de la empresa
    - rfc: RFC de la empresa
    - nombre: Nombre o razón social
    
    Retorna datos auto-completados con niveles de confianza por campo.
    """
    if not request.sitio_web and not request.rfc and not request.nombre:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un dato: sitio_web, rfc o nombre"
        )
    
    logger.info(f"Iniciando Deep Research: web={request.sitio_web}, rfc={request.rfc}, nombre={request.nombre}")
    
    try:
        resultado = await deep_research_service.investigar_empresa(
            sitio_web=request.sitio_web,
            rfc=request.rfc,
            nombre=request.nombre
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Deep Research: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la investigación: {str(e)}"
        )


@router.post("/crear-entidad")
async def crear_entidad(request: CrearEntidadRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Crea un nuevo cliente o proveedor con los datos recopilados.
    - Si el usuario está autenticado: crea el cliente dentro de su empresa (tenant)
    - Si no hay auth o es admin creando tenant: crea una empresa nueva
    """
    datos = request.datos
    
    if not datos.get("rfc") and not datos.get("nombre") and not datos.get("razon_social"):
        raise HTTPException(
            status_code=400, 
            detail="Se requiere al menos el RFC o nombre de la empresa"
        )
    
    current_user = await get_current_user(credentials)
    user_empresa_id = None
    user_id = None
    is_admin = False
    
    if current_user:
        user_empresa_id = current_user.get("empresa_id") or current_user.get("company_id")
        user_id = current_user.get("user_id") or current_user.get("sub")
        role = current_user.get("role", "").lower()
        is_admin = role in ["admin", "superadmin", "platform_admin"]
    
    try:
        if current_user and not is_admin and not user_empresa_id:
            raise HTTPException(
                status_code=403,
                detail="Usuario sin empresa asignada. Contacte al administrador."
            )
        
        if current_user and not is_admin and request.tipo != "cliente":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden crear nuevos tenants. Use tipo='cliente'."
            )
        
        if not is_admin and not current_user:
            raise HTTPException(
                status_code=401,
                detail="Autenticación requerida para crear entidades."
            )
        
        if request.tipo == "cliente" and user_empresa_id:
            cliente_data = {
                "razon_social": datos.get("razon_social") or datos.get("nombre") or "Sin nombre",
                "nombre_comercial": datos.get("nombre") or datos.get("razon_social"),
                "rfc": datos.get("rfc", "").upper() if datos.get("rfc") else None,
                "direccion_fiscal": datos.get("direccion"),
                "ciudad": datos.get("ciudad"),
                "estado": datos.get("estado"),
                "codigo_postal": datos.get("codigo_postal"),
                "regimen_fiscal": datos.get("regimen_fiscal"),
                "actividad_economica": datos.get("giro"),
                "giro": datos.get("giro"),
                "representante_legal": datos.get("representante_legal"),
                "sitio_web": datos.get("sitio_web"),
                "telefono_principal": datos.get("telefono"),
                "email_principal": request.email_contacto or datos.get("email"),
                "status": "activo"
            }
            
            cliente = await cliente_service.create_cliente(
                cliente_data={k: v for k, v in cliente_data.items() if v is not None},
                empresa_id=user_empresa_id,
                creado_por=user_id
            )
            
            pg_datos = {
                "nombre": datos.get("nombre") or datos.get("razon_social"),
                "razon_social": datos.get("razon_social") or datos.get("nombre"),
                "rfc": datos.get("rfc"),
                "direccion": datos.get("direccion"),
                "email": request.email_contacto or datos.get("email"),
                "telefono": datos.get("telefono"),
                "giro": datos.get("giro"),
                "sitio_web": datos.get("sitio_web"),
                "regimen_fiscal": datos.get("regimen_fiscal"),
            }
            pg_cliente = await crear_cliente_postgresql(
                datos=pg_datos,
                empresa_id=user_empresa_id,
                usuario_id=user_id,
                origen="chat"
            )
            
            pg_cliente_id = pg_cliente.get("id") if pg_cliente else None
            
            logger.info(f"Created cliente {cliente['id']} for empresa {user_empresa_id}, PostgreSQL ID: {pg_cliente_id}")
            
            return {
                "success": True,
                "cliente_id": cliente["id"],
                "pg_cliente_id": pg_cliente_id,
                "empresa_id": user_empresa_id,
                "tipo": "cliente",
                "company_name": cliente.get("razon_social"),
                "mensaje": "Cliente creado exitosamente",
                "datos_guardados": {
                    "nombre": cliente.get("razon_social"),
                    "rfc": cliente.get("rfc"),
                    "giro": cliente.get("giro")
                }
            }
        
        industria = IndustriaEnum.OTRO
        giro = datos.get("giro", "").lower() if datos.get("giro") else ""
        
        if "tecnolog" in giro or "software" in giro or "sistemas" in giro:
            industria = IndustriaEnum.TECNOLOGIA
        elif "construc" in giro or "inmobili" in giro:
            industria = IndustriaEnum.CONSTRUCCION
        elif "manufactur" in giro or "fabric" in giro:
            industria = IndustriaEnum.MANUFACTURA
        elif "comerci" in giro or "venta" in giro:
            industria = IndustriaEnum.COMERCIO
        elif "servicio" in giro or "consultor" in giro:
            industria = IndustriaEnum.SERVICIOS_PROFESIONALES
        elif "salud" in giro or "hospital" in giro or "medic" in giro:
            industria = IndustriaEnum.SALUD
        elif "transporte" in giro or "logistic" in giro:
            industria = IndustriaEnum.TRANSPORTE_LOGISTICA
        
        rfc_value = datos.get("rfc", "").upper() if datos.get("rfc") else "PENDIENTE000"
        empresa_data = EmpresaCreate(
            nombre_comercial=datos.get("nombre") or datos.get("razon_social") or "Sin nombre",
            razon_social=datos.get("razon_social") or datos.get("nombre") or "Sin razón social",
            rfc=rfc_value,
            industria=industria,
            sub_industria=datos.get("giro")
        )
        
        empresa = await empresa_service.crear_empresa(empresa_data)
        empresa_id = empresa.id
        
        campos_extra = {}
        if datos.get("direccion"):
            campos_extra["direccion"] = datos["direccion"]
        if datos.get("telefono"):
            campos_extra["telefono"] = datos["telefono"]
        if datos.get("sitio_web"):
            campos_extra["sitio_web"] = datos["sitio_web"]
        if datos.get("representante_legal"):
            campos_extra["representante_legal"] = datos["representante_legal"]
        if datos.get("capital_social"):
            campos_extra["capital_social"] = datos["capital_social"]
        if datos.get("regimen_fiscal"):
            campos_extra["regimen_fiscal"] = datos["regimen_fiscal"]
        
        if campos_extra:
            await empresa_repository.update(empresa_id, campos_extra)
        
        usuario_id = None
        if request.email_contacto:
            try:
                existing_user = await user_service.get_user_by_email(request.email_contacto)
                if existing_user:
                    user_dict = existing_user.to_dict() if hasattr(existing_user, 'to_dict') else {}
                    usuario_id = user_dict.get("user_id") if user_dict else getattr(existing_user, 'id', None)
                else:
                    nuevo_usuario = await user_service.create_user({
                        "user_id": str(uuid.uuid4()),
                        "email": request.email_contacto,
                        "full_name": datos.get("representante_legal") or datos.get("nombre") or "Usuario",
                        "password_hash": None,
                        "role": "cliente" if request.tipo == "cliente" else "proveedor",
                        "company": empresa_id,
                        "is_active": False,
                        "approval_status": "pending"
                    })
                    usuario_id = nuevo_usuario.id if nuevo_usuario else None
            except Exception as e:
                logger.warning(f"Could not create user: {e}")
        
        logger.info(f"Created {request.tipo}: {empresa_id} with email {request.email_contacto}")
        
        return {
            "success": True,
            "company_id": empresa_id,
            "empresa_id": empresa_id,
            "usuario_id": usuario_id,
            "tipo": request.tipo,
            "company_name": empresa.nombre_comercial,
            "mensaje": f"{request.tipo.capitalize()} creado exitosamente",
            "datos_guardados": {
                "nombre": empresa.nombre_comercial,
                "rfc": empresa.rfc,
                "industria": empresa.industria.value if hasattr(empresa.industria, 'value') else str(empresa.industria)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos-entidad")
async def get_tipos_entidad():
    """Retorna los tipos de entidad disponibles"""
    return {
        "tipos": [
            {"id": "cliente", "nombre": "Cliente", "descripcion": "Empresa que contrata servicios"},
            {"id": "proveedor", "nombre": "Proveedor", "descripcion": "Empresa que proporciona servicios"}
        ]
    }


@router.post("/documentos")
async def subir_documentos_cliente(
    files: List[UploadFile] = File(...),
    cliente_id: int = Form(...),
    tipo_documento: Optional[str] = Form(None),
    categoria: Optional[str] = Form(None),
    subcategoria: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Sube documentos asociados a un cliente existente usando el servicio de versionamiento.
    
    Args:
        files: Lista de archivos a subir
        cliente_id: ID del cliente en PostgreSQL
        tipo_documento: Tipo del documento (opcional)
        categoria: Categoría del documento (opcional)
        subcategoria: Subcategoría del documento (opcional)
    
    Returns:
        Lista de documentos subidos con sus detalles
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
    
    current_user = await get_current_user(credentials)
    usuario = None
    if current_user:
        usuario = current_user.get("user_id") or current_user.get("sub") or current_user.get("email")
    
    resultados = []
    errores = []
    
    for file in files:
        try:
            contenido = await file.read()
            nombre_archivo = file.filename or f"documento_{uuid.uuid4().hex[:8]}"
            
            resultado = await documento_versionado_service.subir_documento(
                cliente_id=cliente_id,
                nombre_archivo=nombre_archivo,
                contenido=contenido,
                tipo_documento=tipo_documento,
                categoria=categoria,
                subcategoria=subcategoria,
                usuario=usuario,
                metadata_adicional={
                    "content_type": file.content_type,
                    "origen": "chatbot_archivo",
                    "subido_via": "onboarding"
                }
            )
            
            resultados.append({
                "filename": file.filename,
                "status": resultado.get("status"),
                "mensaje": resultado.get("mensaje"),
                "documento_id": resultado.get("documento_id"),
                "documento_uuid": resultado.get("documento_uuid"),
                "version": resultado.get("version")
            })
            
            logger.info(f"Documento '{file.filename}' subido para cliente {cliente_id}: {resultado.get('status')}")
            
        except Exception as e:
            logger.error(f"Error subiendo documento {file.filename}: {e}")
            errores.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success": len(errores) == 0,
        "cliente_id": cliente_id,
        "documentos_subidos": resultados,
        "errores": errores,
        "total_subidos": len(resultados),
        "total_errores": len(errores)
    }


@router.get("/documentos/{cliente_id}")
async def obtener_documentos_cliente(
    cliente_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Lista todos los documentos de un cliente.
    """
    try:
        documentos = await documento_versionado_service.listar_documentos_cliente(cliente_id)
        return {
            "success": True,
            "cliente_id": cliente_id,
            "documentos": documentos,
            "total": len(documentos)
        }
    except Exception as e:
        logger.error(f"Error listando documentos para cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
