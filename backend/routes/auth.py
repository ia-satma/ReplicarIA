"""
Authentication Routes - Using PostgreSQL for user storage
Supports email/password authentication with JWT tokens
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import jwt, exceptions as jose_exceptions
from datetime import datetime, timedelta, timezone
import os
import uuid
import logging

from services.dreamhost_email_service import email_service
from services.auth_service import get_secret_key, get_current_user, security
from services.error_handler import handle_route_error

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# Usar servicio centralizado de autenticación
SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: str = ""

    def validate_password_length(self):
        if len(self.password.encode('utf-8')) > 72:
            raise ValueError("Password cannot exceed 72 bytes")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    company: str
    role: str


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    token = credentials.credentials
    payload = verify_token(token)
    return payload


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to optionally get current user (returns None if not authenticated)"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except HTTPException:
        return None


@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    from services.user_db import user_service
    
    try:
        if len(user_data.password.encode('utf-8')) > 72:
            raise HTTPException(status_code=400, detail="La contraseña no puede exceder 72 bytes")
        
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Este email ya está registrado")
        
        user = {
            "user_id": str(uuid.uuid4()),
            "email": user_data.email,
            "password_hash": hash_password(user_data.password),
            "full_name": user_data.full_name,
            "company": user_data.company,
            "role": "user",
            "is_active": False,
            "approval_status": "pending",
            "auth_provider": "email"
        }
        
        new_user = await user_service.create_user(user)
        
        logger.info(f"User registered (pending approval): {user_data.email}")
        
        return {
            "success": True,
            "message": "Tu cuenta ha sido creada y está pendiente de aprobación. Te notificaremos cuando un administrador apruebe tu acceso.",
            "pending_approval": True,
            "user": {
                "user_id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "registro de usuario")


@router.post("/login")
async def login(credentials: UserLogin):
    """Login with email and password"""
    from services.user_db import user_service
    
    try:
        logger.info(f"Login attempt for email: {credentials.email}")
        user = await user_service.get_user_by_email(credentials.email)
        if not user:
            logger.warning(f"User not found: {credentials.email}")
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        
        logger.info(f"User found: {user.email}, id: {user.id}")
        password_hash_val = getattr(user, 'password_hash', None)
        password_hash = str(password_hash_val) if password_hash_val else None
        logger.info(f"Password hash exists: {password_hash is not None}, length: {len(password_hash) if password_hash else 0}")
        if not password_hash:
            logger.warning(f"No password hash for user: {credentials.email}")
            raise HTTPException(status_code=401, detail="Esta cuenta usa otro método de autenticación")
        
        password_valid = verify_password(credentials.password, password_hash)
        logger.info(f"Password verification result: {password_valid}")
        if not password_valid:
            logger.warning(f"Invalid password for user: {credentials.email}")
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        
        approval_status = getattr(user, 'approval_status', 'approved')
        
        if approval_status == "pending":
            raise HTTPException(
                status_code=403, 
                detail="Tu cuenta está pendiente de aprobación por un administrador"
            )
        
        if approval_status == "rejected":
            raise HTTPException(
                status_code=403, 
                detail="Tu solicitud de acceso ha sido rechazada"
            )
        
        if not bool(user.is_active):
            raise HTTPException(
                status_code=403, 
                detail="Tu cuenta ha sido desactivada"
            )
        
        if approval_status != "approved":
            raise HTTPException(
                status_code=403, 
                detail="Tu cuenta no está autorizada para acceder"
            )
        
        user_company = getattr(user, 'company', None)
        user_role = getattr(user, 'role', 'user')
        
        empresa_id = ""
        if user_company:
            from services.user_db import get_session
            from sqlalchemy import text
            try:
                async with get_session() as session:
                    result = await session.execute(
                        text("SELECT id FROM companies WHERE LOWER(TRIM(name)) = LOWER(TRIM(:name)) AND is_active = true"),
                        {"name": user_company}
                    )
                    row = result.fetchone()
                    if row:
                        empresa_id = str(row[0])
                        logger.info(f"Found empresa_id {empresa_id} for company '{user_company}'")
                    else:
                        logger.warning(f"No company found for '{user_company}' - empresa_id will be empty")
            except Exception as e:
                logger.warning(f"Could not lookup empresa_id for '{user_company}': {e}")
        
        token_data = {
            "user_id": str(user.id),
            "email": str(user.email),
            "full_name": str(user.full_name) if user.full_name else "",
            "company": str(user_company) if user_company else "",
            "company_id": empresa_id,
            "empresa_id": empresa_id,
            "role": str(user_role) if user_role else "user"
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"Login successful: {credentials.email}")
        
        user_full_name = getattr(user, 'full_name', None)
        user_company = getattr(user, 'company', None)
        user_role = getattr(user, 'role', None)
        return Token(
            access_token=access_token,
            user={
                "user_id": str(user.id),
                "email": str(user.email),
                "full_name": str(user_full_name) if user_full_name else "",
                "company": str(user_company) if user_company else "",
                "role": str(user_role) if user_role else "user"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "login de usuario")


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    from services.user_db import user_service
    
    user = await user_service.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "success": True,
        "user": user.to_dict()
    }


@router.post("/logout")
async def logout():
    """Logout - client should discard the token"""
    return {
        "success": True,
        "message": "Sesión cerrada exitosamente"
    }


@router.get("/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verify if the current token is valid"""
    from services.user_db import user_service
    
    user = await user_service.get_user_by_id(current_user["user_id"])
    if not user or not bool(user.is_active):
        raise HTTPException(status_code=401, detail="Token inválido o usuario desactivado")
    
    user_full_name = getattr(user, 'full_name', None)
    user_company = getattr(user, 'company', None)
    user_role = getattr(user, 'role', None)
    return {
        "success": True,
        "valid": True,
        "user": {
            "user_id": str(user.id),
            "email": str(user.email),
            "full_name": str(user_full_name) if user_full_name else "",
            "company": str(user_company) if user_company else "",
            "role": str(user_role) if user_role else "user"
        }
    }


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user and verify admin role"""
    from services.user_db import user_service
    
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    user = await user_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    if str(user.role) != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado - Se requiere rol de administrador")
    
    return user


@router.get("/admin/pending-users")
async def get_pending_users(admin_user = Depends(get_admin_user)):
    """Get all users with pending approval status (admin only)"""
    from services.user_db import user_service
    
    try:
        pending_users = await user_service.get_pending_users()
        return {
            "success": True,
            "users": [user.to_dict() for user in pending_users]
        }
    except Exception as e:
        return handle_route_error(e, "obtener usuarios pendientes")


@router.get("/admin/all-users")
async def get_all_users(admin_user = Depends(get_admin_user)):
    """Get all users (admin only)"""
    from services.user_db import user_service
    
    try:
        all_users = await user_service.get_all_users()
        return {
            "success": True,
            "users": [user.to_dict() for user in all_users]
        }
    except Exception as e:
        return handle_route_error(e, "obtener todos los usuarios")


@router.post("/admin/approve-user/{user_id}")
async def approve_user(user_id: str, admin_user = Depends(get_admin_user)):
    """Approve a user registration (admin only)"""
    from services.user_db import user_service
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success = await user_service.update_user_approval(
            user_id=user_id,
            approval_status="approved",
            is_active=True,
            approved_by=admin_user.id
        )
        
        if success:
            logger.info(f"User {user_id} approved by admin {str(admin_user.email)}")
            user_full_name = getattr(user, 'full_name', None)
            try:
                email_result = email_service.send_user_approval_notification(
                    user_email=str(user.email),
                    user_name=str(user_full_name) if user_full_name else ""
                )
                if email_result.get("success"):
                    logger.info(f"Approval notification email sent to {user.email}")
                else:
                    logger.warning(f"Failed to send approval notification to {user.email}: {email_result.get('error', 'Unknown error')}")
            except Exception as email_error:
                logger.error(f"Error sending approval notification email to {user.email}: {str(email_error)}")
            
            return {
                "success": True,
                "message": f"Usuario {user.email} aprobado exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al aprobar usuario")
            
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "aprobar usuario")


@router.post("/admin/reject-user/{user_id}")
async def reject_user(user_id: str, admin_user = Depends(get_admin_user)):
    """Reject a user registration (admin only)"""
    from services.user_db import user_service
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success = await user_service.update_user_approval(
            user_id=user_id,
            approval_status="rejected",
            is_active=False,
            approved_by=admin_user.id
        )
        
        if success:
            logger.info(f"User {user_id} rejected by admin {str(admin_user.email)}")
            user_full_name = getattr(user, 'full_name', None)
            try:
                email_result = email_service.send_user_rejection_notification(
                    user_email=str(user.email),
                    user_name=str(user_full_name) if user_full_name else ""
                )
                if email_result.get("success"):
                    logger.info(f"Rejection notification email sent to {user.email}")
                else:
                    logger.warning(f"Failed to send rejection notification to {user.email}: {email_result.get('error', 'Unknown error')}")
            except Exception as email_error:
                logger.error(f"Error sending rejection notification email to {user.email}: {str(email_error)}")
            
            return {
                "success": True,
                "message": f"Usuario {user.email} rechazado"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al rechazar usuario")
            
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "rechazar usuario")


class UpdateAllowedCompaniesRequest(BaseModel):
    allowed_companies: List[str]


@router.post("/admin/user/{user_id}/allowed-companies")
async def update_user_allowed_companies(user_id: str, request: UpdateAllowedCompaniesRequest, admin_user = Depends(get_admin_user)):
    """Update user's allowed companies list (admin only)"""
    from services.user_db import user_service
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success = await user_service.update_user_allowed_companies(
            user_id=user_id,
            allowed_companies=request.allowed_companies
        )
        
        if success:
            logger.info(f"Allowed companies updated for user {user_id} by admin {str(admin_user.email)}: {request.allowed_companies}")
            return {
                "success": True,
                "message": f"Empresas permitidas actualizadas para {user.email}",
                "allowed_companies": request.allowed_companies
            }
        else:
            raise HTTPException(status_code=500, detail="Error al actualizar empresas permitidas")
            
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "actualizar empresas permitidas")


@router.get("/companies")
async def get_companies_public():
    """Get list of all available companies (public endpoint for forms)"""
    try:
        from services.user_db import get_session
        from sqlalchemy import text
        
        DEFAULT_COMPANIES = [
            ("ac91ec43-50d0-4cb4-9df9-72ef1f819055", "AGENCIA DE MARKETING Y PUBLICIDAD S.C."),
            ("4c07ccda-4ceb-4a71-9ef5-d0a8fe7cc9ac", "SERVICIOS DE MANTENIMIENTO S.A. DE C.V."),
            ("727831c3-b31c-46e5-9d1f-99a89b2af781", "CONSULTORIA EN MATERIA INFORMATICA S.A. DE C.V."),
            ("c1905d78-f5e6-460b-87bb-f5d351047cfe", "CONSULTORIA JURIDICA, S.C."),
            ("68d82549-2cd1-485c-a065-e0c4e3c67c78", "CONSULTORIA ESPECIALIZADA EN CUESTIONES OPERATIVAS, S.C."),
            ("6b01ac74-0c68-4970-9d8e-a535614ddd59", "ESTUDIOS E INVESTIGACIONES DE MERCADO, S.A. DE C.V."),
            ("3c924d0b-bdac-4eb9-8ee2-786a90a6d48a", "COORDINACION Y GESTION DE EVENTOS, S.C."),
        ]
        
        async with get_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM companies")
            )
            count = result.scalar()
            
            if count == 0:
                logger.info("Companies table is empty, auto-seeding default companies...")
                for company_id, company_name in DEFAULT_COMPANIES:
                    await session.execute(
                        text("INSERT INTO companies (id, name, is_active, created_at) VALUES (:id, :name, true, NOW()) ON CONFLICT (id) DO NOTHING"),
                        {"id": company_id, "name": company_name}
                    )
                await session.commit()
                logger.info(f"Auto-seeded {len(DEFAULT_COMPANIES)} companies")
            
            result = await session.execute(
                text("SELECT id, name FROM companies WHERE is_active = true ORDER BY name")
            )
            companies = [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]
        
        return {
            "success": True,
            "companies": companies
        }
        
    except Exception as e:
        return handle_route_error(e, "obtener empresas")


@router.get("/admin/companies")
async def get_available_companies(admin_user = Depends(get_admin_user)):
    """Get list of all available companies from companies table (admin only)"""
    try:
        from services.user_db import get_session
        from sqlalchemy import text
        
        async with get_session() as session:
            result = await session.execute(
                text("SELECT name FROM companies WHERE is_active = true ORDER BY name")
            )
            companies = [row[0] for row in result.fetchall()]
        
        return {
            "success": True,
            "companies": companies
        }
        
    except Exception as e:
        return handle_route_error(e, "obtener empresas disponibles")


class UpdateUserRequest(BaseModel):
    full_name: str = None
    email: EmailStr = None
    company: str = None
    role: str = None


@router.put("/admin/user/{user_id}")
async def update_user_profile(user_id: str, request: UpdateUserRequest, admin_user = Depends(get_admin_user)):
    """Update user profile data (admin only)"""
    from services.user_db import user_service
    from datetime import datetime, timezone
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        update_data = {"updated_at": datetime.now(timezone.utc)}
        
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.email is not None:
            existing = await user_service.get_user_by_email(request.email)
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="Este email ya está en uso por otro usuario")
            update_data["email"] = request.email
        if request.company is not None:
            update_data["company"] = request.company
        if request.role is not None:
            if request.role not in ["admin", "user"]:
                raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'admin' o 'user'")
            update_data["role"] = request.role
        
        success = await user_service.update_user(user_id, update_data)
        
        if success:
            logger.info(f"User {user_id} updated by admin {str(admin_user.email)}")
            return {
                "success": True,
                "message": f"Usuario actualizado exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al actualizar usuario")
            
    except HTTPException:
        raise
    except Exception as e:
        return handle_route_error(e, "actualizar usuario")
