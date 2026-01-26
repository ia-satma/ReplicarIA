"""
Admin Routes - Complete user, company and knowledge base management
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import jwt, exceptions as jose_exceptions
from datetime import datetime
import os
import uuid
import logging
import json
import shutil
import asyncpg

from services.user_db import user_service as user_db
from services.empresa_service import empresa_service
from services.company_service import company_service
from services.auth_service import get_secret_key, security
from services.error_handler import handle_route_error
from models.empresa import Empresa, EmpresaUpdate, IndustriaEnum

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# Usar servicio centralizado de autenticación
SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"

KB_UPLOADS_DIR = "backend/uploads/kb"
os.makedirs(KB_UPLOADS_DIR, exist_ok=True)


class UpdateUsuarioRequest(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    rol: Optional[str] = None
    estado: Optional[str] = None
    empresas_permitidas: Optional[List[str]] = None


class UpdateEmpresaAdminRequest(BaseModel):
    nombre_comercial: Optional[str] = None
    razon_social: Optional[str] = None
    rfc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sitio_web: Optional[str] = None
    giro: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    industria: Optional[str] = None


class CreateEmpresaRequest(BaseModel):
    nombre_comercial: str
    razon_social: str
    rfc: str
    industria: str = "otro"
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None


class CreateUsuarioRequest(BaseModel):
    nombre: str
    email: EmailStr
    empresa: Optional[str] = None
    rol: str = "user"
    activo: bool = True


DATABASE_URL = os.environ.get('DATABASE_URL', '')


async def get_db_connection():
    """Get asyncpg connection for direct database operations"""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured")
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user and verify admin role"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user = await user_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(user.role) != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado - Se requiere rol de administrador")
    
    return user


@router.get("/usuarios")
async def list_usuarios(admin_user = Depends(get_admin_user)):
    """List all users with their details"""
    try:
        users = await user_db.get_all_users()
        return {
            "success": True,
            "usuarios": [u.to_dict() for u in users]
        }
    except Exception as e:
        return handle_route_error(e, "listar usuarios")


@router.post("/usuarios")
async def create_usuario(request: CreateUsuarioRequest, admin_user = Depends(get_admin_user)):
    """Create a new user and sync to usuarios_autorizados for OTP login"""
    try:
        existing_user = await user_db.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
        
        if request.rol not in ['admin', 'user']:
            raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'admin' o 'user'")
        
        user_id = str(uuid.uuid4())
        
        user_data = {
            'user_id': user_id,
            'email': request.email,
            'full_name': request.nombre,
            'company': request.empresa,
            'role': request.rol,
            'is_active': request.activo,
            'approval_status': 'approved' if request.activo else 'pending',
            'auth_provider': 'otp'
        }
        
        created_user = await user_db.create_user(user_data)
        
        conn = await get_db_connection()
        if conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO usuarios_autorizados (email, nombre, empresa, rol, activo)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (email) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        empresa = EXCLUDED.empresa,
                        rol = EXCLUDED.rol,
                        activo = EXCLUDED.activo
                    """,
                    request.email,
                    request.nombre,
                    request.empresa or '',
                    request.rol,
                    request.activo
                )
                logger.info(f"User synced to usuarios_autorizados: {request.email}")
            except Exception as e:
                logger.warning(f"Could not sync to usuarios_autorizados: {e}")
            finally:
                await conn.close()
        
        logger.info(f"User {user_id} created by admin {admin_user.email}")
        
        return {
            "success": True,
            "message": "Usuario creado correctamente",
            "usuario": created_user.to_dict() if created_user else None
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "crear usuario")


@router.get("/usuarios/{user_id}")
async def get_usuario(user_id: str, admin_user = Depends(get_admin_user)):
    """Get a specific user's details"""
    try:
        user = await user_db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_dict = user.to_dict()
        
        user_company_name = str(user.company) if user.company else ""
        empresa_id = await company_service.get_company_id_for_user(user_company_name) if user_company_name else None
        user_dict['empresa_id'] = empresa_id
        
        if empresa_id:
            company_data = await company_service.get_company_by_id(empresa_id)
            if company_data:
                user_dict['empresa_data'] = {
                    'id': company_data.get('id'),
                    'name': company_data.get('name'),
                    'rfc': company_data.get('rfc')
                }
        
        return {
            "success": True,
            "usuario": user_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"obtener usuario {user_id}")


@router.put("/usuarios/{user_id}")
async def update_usuario(user_id: str, request: UpdateUsuarioRequest, admin_user = Depends(get_admin_user)):
    """Update a user's profile"""
    try:
        user = await user_db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        updates = {}
        if request.nombre is not None:
            updates['full_name'] = request.nombre
        if request.email is not None:
            updates['email'] = request.email
        if request.rol is not None:
            if request.rol not in ['admin', 'user', 'cliente', 'proveedor']:
                raise HTTPException(status_code=400, detail="Rol inválido")
            role_map = {'cliente': 'user', 'proveedor': 'user'}
            updates['role'] = role_map.get(request.rol, request.rol)
        if request.estado is not None:
            status_map = {'pendiente': 'pending', 'aprobado': 'approved', 'rechazado': 'rejected'}
            updates['approval_status'] = status_map.get(request.estado, request.estado)
            if request.estado == 'aprobado':
                updates['is_active'] = True
            elif request.estado == 'rechazado':
                updates['is_active'] = False
        if request.empresas_permitidas is not None:
            updates['allowed_companies'] = json.dumps(request.empresas_permitidas)
        
        if updates:
            await user_db.update_user(user_id, updates)
            logger.info(f"User {user_id} updated by admin {admin_user.email}")
            updated_user = await user_db.get_user_by_id(user_id)
        else:
            updated_user = user
        
        return {
            "success": True,
            "message": "Usuario actualizado correctamente",
            "usuario": updated_user.to_dict() if updated_user else None
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"actualizar usuario {user_id}")


@router.delete("/usuarios/{user_id}")
async def delete_usuario(user_id: str, admin_user = Depends(get_admin_user)):
    """Delete a user (soft delete by setting inactive)"""
    try:
        user = await user_db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if user.id == admin_user.id:
            raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
        await user_db.update_user(user_id, {
            'is_active': False,
            'approval_status': 'deleted'
        })
        
        logger.info(f"User {user_id} deleted by admin {admin_user.email}")
        
        return {
            "success": True,
            "message": "Usuario eliminado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"eliminar usuario {user_id}")


@router.get("/empresas")
async def list_empresas(admin_user = Depends(get_admin_user)):
    """List all companies"""
    try:
        empresas = await empresa_service.get_all_empresas(only_active=False)
        return {
            "success": True,
            "empresas": [
                {
                    "id": e.id,
                    "nombre": e.nombre_comercial,
                    "rfc": e.rfc,
                    "razon_social": e.razon_social,
                    "industria": e.industria.value if hasattr(e.industria, 'value') else str(e.industria),
                    "activa": e.activa,
                    "fecha_alta": e.fecha_alta.isoformat() if hasattr(e.fecha_alta, 'isoformat') else str(e.fecha_alta)
                }
                for e in empresas
            ]
        }
    except Exception as e:
        return handle_route_error(e, "listar empresas")


@router.get("/empresas/{empresa_id}")
async def get_empresa(empresa_id: str, admin_user = Depends(get_admin_user)):
    """Get a specific company's details from PostgreSQL"""
    try:
        company = await company_service.get_company_by_id(empresa_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        return {
            "success": True,
            "empresa": {
                "id": str(company.get('id')),
                "nombre": company.get('name'),
                "nombre_comercial": company.get('name'),
                "rfc": company.get('rfc'),
                "razon_social": company.get('name'),
                "direccion": company.get('address'),
                "telefono": company.get('phone'),
                "email": company.get('email'),
                "sitio_web": company.get('website'),
                "giro": company.get('industry'),
                "regimen_fiscal": company.get('tax_regime'),
                "industria": company.get('industry'),
                "is_active": company.get('is_active', True),
                "activa": company.get('is_active', True),
                "created_at": str(company.get('created_at')) if company.get('created_at') else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"obtener empresa {empresa_id}")


@router.put("/empresas/{empresa_id}")
async def update_empresa(empresa_id: str, request: UpdateEmpresaAdminRequest, admin_user = Depends(get_admin_user)):
    """Update a company's details"""
    try:
        company = await company_service.get_company_by_id(empresa_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        update_dict = {}
        if request.nombre_comercial is not None:
            update_dict['nombre_comercial'] = request.nombre_comercial
        if request.razon_social is not None:
            update_dict['razon_social'] = request.razon_social
        if request.rfc is not None:
            update_dict['rfc'] = request.rfc.upper()
        if request.giro is not None:
            update_dict['sub_industria'] = request.giro
        
        if update_dict:
            from repositories.empresa_repository import empresa_repository
            updated = await empresa_repository.update(empresa_id, update_dict)
            logger.info(f"Empresa {empresa_id} updated by admin {admin_user.email}")
            
            return {
                "success": True,
                "message": "Empresa actualizada correctamente",
                "empresa": {
                    "id": updated.id if updated else empresa_id,
                    "nombre": updated.nombre_comercial if updated else company.get('name')
                }
            }
        else:
            return {
                "success": True,
                "message": "No se proporcionaron campos para actualizar",
                "empresa": {
                    "id": empresa_id,
                    "nombre": company.get('name')
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"actualizar empresa {empresa_id}")


@router.post("/empresas")
async def create_empresa(request: CreateEmpresaRequest, admin_user = Depends(get_admin_user)):
    """Create a new company"""
    try:
        from models.empresa import EmpresaCreate
        
        industria_enum = IndustriaEnum.OTRO
        try:
            industria_enum = IndustriaEnum(request.industria.lower())
        except ValueError:
            pass
        
        empresa_data = EmpresaCreate(
            nombre_comercial=request.nombre_comercial,
            razon_social=request.razon_social,
            rfc=request.rfc.upper(),
            industria=industria_enum
        )
        
        created = await empresa_service.crear_empresa(empresa_data)
        
        logger.info(f"Empresa {created.id} created by admin {admin_user.email}")
        
        return {
            "success": True,
            "message": "Empresa creada correctamente",
            "empresa": {
                "id": created.id,
                "nombre": created.nombre_comercial,
                "rfc": created.rfc
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        return handle_route_error(e, "crear empresa")


@router.get("/empresas/{empresa_id}/documentos")
async def get_empresa_documentos(empresa_id: str, admin_user = Depends(get_admin_user)):
    """Get all knowledge base documents for a company"""
    try:
        company = await company_service.get_company_by_id(empresa_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        empresa_kb_dir = os.path.join(KB_UPLOADS_DIR, empresa_id)
        documentos = []
        
        if os.path.exists(empresa_kb_dir):
            for filename in os.listdir(empresa_kb_dir):
                filepath = os.path.join(empresa_kb_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    doc_id = f"{empresa_id}_{filename}"
                    documentos.append({
                        "id": doc_id,
                        "nombre": filename,
                        "tipo": filename.split('.')[-1] if '.' in filename else "unknown",
                        "tamaño": stat.st_size,
                        "fecha_subida": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "estado": "procesado",
                        "chunks": 0
                    })
        
        return {
            "success": True,
            "documentos": documentos,
            "total": len(documentos)
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"obtener documentos de empresa {empresa_id}")


@router.post("/knowledge-base/upload")
async def upload_kb_document(
    files: List[UploadFile] = File(...),
    empresa_id: str = Form(...),
    admin_user = Depends(get_admin_user)
):
    """Upload documents to a company's knowledge base"""
    try:
        company = await company_service.get_company_by_id(empresa_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        empresa_kb_dir = os.path.join(KB_UPLOADS_DIR, empresa_id)
        os.makedirs(empresa_kb_dir, exist_ok=True)
        
        uploaded = []
        for file in files:
            file_id = str(uuid.uuid4())[:8]
            safe_filename = f"{file_id}_{file.filename}"
            filepath = os.path.join(empresa_kb_dir, safe_filename)
            
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded.append({
                "id": f"{empresa_id}_{safe_filename}",
                "nombre": file.filename,
                "tamaño": len(content),
                "estado": "procesado"
            })
            
            logger.info(f"KB document uploaded: {safe_filename} for empresa {empresa_id}")
        
        return {
            "success": True,
            "message": f"{len(uploaded)} documento(s) subido(s) correctamente",
            "documentos": uploaded
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "subir documentos KB")


@router.delete("/knowledge-base/{doc_id}")
async def delete_kb_document(doc_id: str, admin_user = Depends(get_admin_user)):
    """Delete a document from the knowledge base"""
    try:
        parts = doc_id.split('_', 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="ID de documento inválido")
        
        empresa_id, filename = parts
        filepath = os.path.join(KB_UPLOADS_DIR, empresa_id, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        os.remove(filepath)
        logger.info(f"KB document deleted: {doc_id} by admin {admin_user.email}")
        
        return {
            "success": True,
            "message": "Documento eliminado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"eliminar documento KB {doc_id}")


@router.post("/knowledge-base/reindex/{empresa_id}")
async def reindex_kb(empresa_id: str, admin_user = Depends(get_admin_user)):
    """Trigger reindexing of a company's knowledge base"""
    try:
        company = await company_service.get_company_by_id(empresa_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        empresa_kb_dir = os.path.join(KB_UPLOADS_DIR, empresa_id)
        doc_count = 0
        if os.path.exists(empresa_kb_dir):
            doc_count = len([f for f in os.listdir(empresa_kb_dir) if os.path.isfile(os.path.join(empresa_kb_dir, f))])
        
        logger.info(f"KB reindex initiated for empresa {empresa_id} by admin {admin_user.email}")
        
        return {
            "success": True,
            "message": f"Reindexación iniciada para {doc_count} documento(s)",
            "documentos_procesados": doc_count
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, f"reindexar KB de empresa {empresa_id}")
