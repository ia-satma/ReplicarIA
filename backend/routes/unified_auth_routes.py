"""
REVISAR.IA - Rutas de Autenticación Unificadas
==============================================

Reemplaza:
- routes/auth.py
- routes/otp_auth_routes.py

Endpoints unificados para autenticación password + OTP.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import logging

from services.unified_auth_service import (
    auth_service,
    AuthResponse,
    AuthError,
    RateLimitError,
    User,
    UserStatus,
    UserRole
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


# ============================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================

class LoginRequest(BaseModel):
    """Request para login con contraseña."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class OTPRequestModel(BaseModel):
    """Request para solicitar código OTP."""
    email: EmailStr


class OTPVerifyRequest(BaseModel):
    """Request para verificar código OTP."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class RegisterRequest(BaseModel):
    """Request para registro de usuario."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    company: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Request para resetear contraseña (admin)."""
    new_password: str = Field(..., min_length=8)


class UpdateUserRequest(BaseModel):
    """Request para actualizar usuario (admin)."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class APIResponse(BaseModel):
    """Respuesta estándar de la API."""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[dict] = None


# ============================================================
# HELPERS
# ============================================================

def get_client_ip(request: Request) -> str:
    """Obtiene la IP del cliente."""
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else '0.0.0.0'


def get_user_agent(request: Request) -> str:
    """Obtiene el User-Agent."""
    return request.headers.get('user-agent', 'Unknown')


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependencia para obtener el usuario actual autenticado."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"}
        )

    session, user = await auth_service.validate_session(credentials.credentials)

    if not session or not user:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """Dependencia para obtener usuario admin."""
    if user.role not in ('admin', 'super_admin'):
        raise HTTPException(
            status_code=403,
            detail="Se requiere rol de administrador"
        )
    return user


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[User]:
    """Dependencia opcional para usuario (puede ser None)."""
    if not credentials:
        return None

    try:
        session, user = await auth_service.validate_session(credentials.credentials)
        return user
    except Exception:
        return None


# ============================================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================================

class CheckAuthMethodRequest(BaseModel):
    """Request para verificar método de autenticación."""
    email: EmailStr


@router.post("/check-auth-method", response_model=APIResponse)
async def check_auth_method(body: CheckAuthMethodRequest):
    """
    Verificar qué método de autenticación usa un email.

    - Retorna 'password' para superadmin
    - Retorna 'otp' para usuarios normales
    """
    # Usar la misma conexión que funciona para OTP
    from services.otp_auth_service import get_db_connection

    try:
        logger.info(f"[check-auth-method] Checking auth method for: {body.email}")
        conn = await get_db_connection()

        if not conn:
            logger.warning("[check-auth-method] No database connection available")
            return APIResponse(
                success=True,
                message="No DB connection - default OTP",
                data={'auth_method': 'otp'}
            )

        try:
            # Check auth_users table for password users
            row = await conn.fetchrow('''
                SELECT email, auth_method, role, status FROM auth_users
                WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            ''', body.email)

            logger.info(f"[check-auth-method] Query result: {dict(row) if row else 'No row found'}")

            if row:
                if row['status'] != 'active':
                    logger.warning(f"[check-auth-method] User found but status is: {row['status']}")
                elif row['auth_method'] == 'password':
                    logger.info(f"[check-auth-method] Password auth for role: {row['role']}")
                    return APIResponse(
                        success=True,
                        message="Método de autenticación encontrado",
                        data={
                            'auth_method': 'password',
                            'is_superadmin': row['role'] == 'super_admin'
                        }
                    )
            else:
                logger.info(f"[check-auth-method] No user found in auth_users for {body.email}")

        finally:
            await conn.close()

        return APIResponse(
            success=True,
            message="Método de autenticación: OTP",
            data={'auth_method': 'otp'}
        )
    except Exception as e:
        logger.error(f"[check-auth-method] Error: {e}", exc_info=True)
        return APIResponse(
            success=True,
            message="Default to OTP",
            data={'auth_method': 'otp'}
        )


@router.get("/debug-auth-users", response_model=APIResponse)
async def debug_auth_users():
    """
    Debug endpoint para verificar contenido de auth_users.
    Solo para diagnóstico.
    """
    from services.otp_auth_service import get_db_connection

    try:
        conn = await get_db_connection()
        if not conn:
            return APIResponse(
                success=False,
                message="No database connection",
                data={'error': 'No DATABASE_URL or connection failed'}
            )

        try:
            # Check if table exists
            table_exists = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'auth_users'
                )
            ''')

            if not table_exists:
                return APIResponse(
                    success=False,
                    message="Table auth_users does not exist",
                    data={'table_exists': False}
                )

            # Get all users (masked for security)
            rows = await conn.fetch('''
                SELECT id, email, auth_method, role, status, created_at
                FROM auth_users
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT 10
            ''')

            users = []
            for row in rows:
                users.append({
                    'id': str(row['id']),
                    'email': row['email'][:3] + '***' + row['email'][row['email'].find('@'):],
                    'auth_method': row['auth_method'],
                    'role': row['role'],
                    'status': row['status'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

            return APIResponse(
                success=True,
                message=f"Found {len(users)} users in auth_users",
                data={
                    'table_exists': True,
                    'user_count': len(users),
                    'users': users
                }
            )

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Debug auth_users error: {e}", exc_info=True)
        return APIResponse(
            success=False,
            message=f"Error: {str(e)}",
            data={'error': str(e)}
        )


@router.post("/login", response_model=APIResponse)
async def login(request: Request, body: LoginRequest):
    """
    Login con email y contraseña.

    - Para administradores y usuarios con auth_method='password'
    - Retorna token de sesión
    """
    import bcrypt
    import secrets
    from datetime import datetime, timedelta, timezone

    # Usar conexión que funciona (la misma que OTP)
    from services.otp_auth_service import get_db_connection

    try:
        conn = await get_db_connection()
        if not conn:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")

        try:
            # Buscar usuario
            row = await conn.fetchrow('''
                SELECT id, email, full_name, password_hash, role, status, auth_method,
                       empresa_id, company_name, email_verified, metadata
                FROM auth_users
                WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            ''', body.email)

            if not row:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

            if row['status'] != 'active':
                raise HTTPException(status_code=403, detail="Cuenta no activa")

            if not row['password_hash']:
                raise HTTPException(status_code=401, detail="Usuario no tiene contraseña configurada")

            # Verificar contraseña
            if not bcrypt.checkpw(body.password.encode('utf-8'), row['password_hash'].encode('utf-8')):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

            # Crear sesión
            import hashlib
            token = secrets.token_urlsafe(32)
            # Hash the token for secure storage (same method as unified_auth_service)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

            try:
                await conn.execute('''
                    INSERT INTO auth_sessions (user_id, token_hash, token_prefix, auth_method, is_active, expires_at, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ''', row['id'], token_hash, token[:8], 'password', True, expires_at,
                    get_client_ip(request), get_user_agent(request)[:500] if get_user_agent(request) else None)
                logger.info(f"Session created for {row['email']} with prefix {token[:8]}")
            except Exception as session_err:
                logger.error(f"Session insert failed: {session_err}")

            # Actualizar último login
            try:
                await conn.execute('''
                    UPDATE auth_users SET last_login_at = NOW() WHERE id = $1
                ''', row['id'])
            except Exception as update_err:
                logger.warning(f"Update last_login failed: {update_err}")

            return APIResponse(
                success=True,
                message="Login exitoso",
                data={
                    'access_token': token,
                    'token_type': 'bearer',
                    'user': {
                        'id': str(row['id']),
                        'email': row['email'],
                        'full_name': row['full_name'],
                        'role': row['role'],
                        'empresa_id': str(row['empresa_id']) if row['empresa_id'] else None,
                        'company_name': row['company_name'],
                        'is_superadmin': row['role'] == 'super_admin',
                        'metadata': row['metadata'] or {}
                    },
                    'expires_at': expires_at.isoformat()
                }
            )
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/otp/request-code", response_model=APIResponse)
async def request_otp_code(request: Request, body: OTPRequestModel):
    """
    Solicitar código OTP.

    - Envía código de 6 dígitos al email
    - Código expira en 5 minutos
    - Máximo 3 solicitudes cada 10 minutos
    """
    try:
        result = await auth_service.request_otp(
            email=body.email,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        # Siempre retornar éxito para no revelar si el email existe
        return APIResponse(
            success=True,
            message="Si el email está registrado, recibirás un código de acceso",
            data={
                'email': body.email,
                'expires_in_minutes': 5
            } if result.success else None
        )

    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=e.message,
            headers={'Retry-After': str(e.retry_after)}
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/otp/verify-code", response_model=APIResponse)
async def verify_otp_code(request: Request, body: OTPVerifyRequest):
    """
    Verificar código OTP.

    - Valida código de 6 dígitos
    - Crea sesión si es válido
    - Máximo 3 intentos por código
    """
    try:
        result = await auth_service.verify_otp(
            email=body.email,
            code=body.code,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        if result.success:
            return APIResponse(
                success=True,
                message=result.message,
                data={
                    'token': result.token,
                    'user': result.user.to_dict() if result.user else None,
                    'expires_at': result.expires_at.isoformat() if result.expires_at else None
                }
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=result.message
            )

    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=e.message,
            headers={'Retry-After': str(e.retry_after)}
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/otp/session", response_model=APIResponse)
async def get_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verificar sesión actual.

    - Valida el token de sesión
    - Retorna información del usuario
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")

    session, user = await auth_service.validate_session(credentials.credentials)

    if not session or not user:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    return APIResponse(
        success=True,
        message="Sesión válida",
        data={
            'user': user.to_dict(),
            'session': {
                'id': session.id,
                'auth_method': session.auth_method,
                'expires_at': session.expires_at.isoformat(),
                'created_at': session.created_at.isoformat() if session.created_at else None
            }
        }
    )


@router.post("/otp/logout", response_model=APIResponse)
@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Cerrar sesión.

    - Invalida el token de sesión
    """
    if not credentials:
        return APIResponse(success=True, message="Sesión cerrada")

    result = await auth_service.logout(
        token=credentials.credentials,
        ip_address=get_client_ip(request)
    )

    return APIResponse(
        success=True,
        message=result.message
    )


@router.get("/verify", response_model=APIResponse)
async def verify_auth(user: User = Depends(get_current_user)):
    """
    Verificar autenticación.

    - Verifica si el token es válido
    - Retorna información del usuario
    """
    return APIResponse(
        success=True,
        message="Token válido",
        data={
            'valid': True,
            'user': user.to_dict()
        }
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Obtener información del usuario actual.
    """
    return APIResponse(
        success=True,
        message="Usuario encontrado",
        data={'user': user.to_dict()}
    )


# ============================================================
# ENDPOINTS DE REGISTRO
# ============================================================

@router.post("/register", response_model=APIResponse)
async def register(request: Request, body: RegisterRequest):
    """
    Registrar nuevo usuario.

    - Crea cuenta con estado 'pending'
    - Requiere aprobación de administrador
    """
    try:
        user = await auth_service.create_user(
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            company_name=body.company,
            status='pending',
            auto_approve=False
        )

        return APIResponse(
            success=True,
            message="Cuenta creada. Pendiente de aprobación por administrador.",
            data={
                'pending_approval': True,
                'user': {
                    'user_id': user.id,
                    'email': user.email,
                    'full_name': user.full_name
                }
            }
        )

    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================

@router.get("/admin/all-users", response_model=APIResponse)
async def get_all_users(admin: User = Depends(get_admin_user)):
    """
    Obtener todos los usuarios (admin).
    """
    from services.unified_auth_service import DatabasePool

    async with await DatabasePool.get_connection() as conn:
        rows = await conn.fetch('''
            SELECT id, email, full_name, role, status, auth_method,
                   empresa_id, company_name, email_verified,
                   last_login_at, created_at
            FROM auth_users
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
        ''')

        users = []
        for row in rows:
            users.append({
                'user_id': str(row['id']),
                'email': row['email'],
                'full_name': row['full_name'],
                'role': row['role'],
                'status': row['status'],
                'auth_method': row['auth_method'],
                'empresa_id': str(row['empresa_id']) if row['empresa_id'] else None,
                'company': row['company_name'],
                'email_verified': row['email_verified'],
                'is_active': row['status'] == 'active',
                'approval_status': 'approved' if row['status'] == 'active' else row['status'],
                'last_login_at': row['last_login_at'].isoformat() if row['last_login_at'] else None,
                'created_at': row['created_at'].isoformat() if row['created_at'] else None
            })

    return APIResponse(
        success=True,
        message=f"{len(users)} usuarios encontrados",
        data={'users': users}
    )


@router.get("/admin/pending-users", response_model=APIResponse)
async def get_pending_users(admin: User = Depends(get_admin_user)):
    """
    Obtener usuarios pendientes de aprobación (admin).
    """
    from services.unified_auth_service import DatabasePool

    async with await DatabasePool.get_connection() as conn:
        rows = await conn.fetch('''
            SELECT id, email, full_name, role, company_name, created_at
            FROM auth_users
            WHERE status = 'pending' AND deleted_at IS NULL
            ORDER BY created_at DESC
        ''')

        users = [{
            'user_id': str(row['id']),
            'email': row['email'],
            'full_name': row['full_name'],
            'role': row['role'],
            'company': row['company_name'],
            'created_at': row['created_at'].isoformat() if row['created_at'] else None
        } for row in rows]

    return APIResponse(
        success=True,
        message=f"{len(users)} usuarios pendientes",
        data={'users': users}
    )


@router.post("/admin/approve-user/{user_id}", response_model=APIResponse)
async def approve_user(user_id: str, admin: User = Depends(get_admin_user)):
    """
    Aprobar usuario (admin).
    """
    from services.unified_auth_service import DatabasePool

    async with await DatabasePool.get_connection() as conn:
        result = await conn.execute('''
            UPDATE auth_users
            SET status = 'active',
                approved_at = NOW(),
                approved_by = $1,
                approval_required = false,
                updated_at = NOW()
            WHERE id = $2 AND deleted_at IS NULL
        ''', admin.id, user_id)

        if 'UPDATE 0' in result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Obtener email para notificación
        email = await conn.fetchval('SELECT email FROM auth_users WHERE id = $1', user_id)

    # Enviar notificación (async, no bloquea)
    try:
        from services.dreamhost_email_service import email_service
        email_service.send_user_approval_notification(email, "")
    except Exception:
        pass

    return APIResponse(
        success=True,
        message="Usuario aprobado exitosamente"
    )


@router.post("/admin/reject-user/{user_id}", response_model=APIResponse)
async def reject_user(user_id: str, admin: User = Depends(get_admin_user)):
    """
    Rechazar usuario (admin).
    """
    from services.unified_auth_service import DatabasePool

    async with await DatabasePool.get_connection() as conn:
        result = await conn.execute('''
            UPDATE auth_users
            SET status = 'blocked',
                status_reason = 'rejected_by_admin',
                status_changed_at = NOW(),
                status_changed_by = $1,
                updated_at = NOW()
            WHERE id = $2 AND deleted_at IS NULL
        ''', admin.id, user_id)

        if 'UPDATE 0' in result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return APIResponse(
        success=True,
        message="Usuario rechazado"
    )


@router.post("/admin/user/{user_id}/reset-password", response_model=APIResponse)
async def reset_user_password(
    user_id: str,
    body: ResetPasswordRequest,
    admin: User = Depends(get_admin_user)
):
    """
    Resetear contraseña de usuario (admin).
    """
    try:
        success = await auth_service.update_user_password(user_id, body.new_password)

        if not success:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Revocar todas las sesiones del usuario
        await auth_service.revoke_all_sessions(user_id, 'password_reset')

        return APIResponse(
            success=True,
            message="Contraseña actualizada exitosamente"
        )

    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/admin/user/{user_id}", response_model=APIResponse)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    admin: User = Depends(get_admin_user)
):
    """
    Actualizar usuario (admin).
    """
    from services.unified_auth_service import DatabasePool

    updates = []
    params = []
    param_count = 1

    if body.full_name is not None:
        updates.append(f"full_name = ${param_count}")
        params.append(body.full_name)
        param_count += 1

    if body.email is not None:
        updates.append(f"email = ${param_count}")
        params.append(body.email.lower())
        param_count += 1

    if body.company is not None:
        updates.append(f"company_name = ${param_count}")
        params.append(body.company)
        param_count += 1

    if body.role is not None:
        if body.role not in ('admin', 'user', 'manager', 'viewer'):
            raise HTTPException(status_code=400, detail="Rol inválido")
        updates.append(f"role = ${param_count}")
        params.append(body.role)
        param_count += 1

    if body.status is not None:
        if body.status not in ('active', 'pending', 'suspended', 'blocked'):
            raise HTTPException(status_code=400, detail="Estado inválido")
        updates.append(f"status = ${param_count}")
        params.append(body.status)
        param_count += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    updates.append("updated_at = NOW()")
    params.append(user_id)

    async with await DatabasePool.get_connection() as conn:
        result = await conn.execute(f'''
            UPDATE auth_users
            SET {", ".join(updates)}
            WHERE id = ${param_count} AND deleted_at IS NULL
        ''', *params)

        if 'UPDATE 0' in result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return APIResponse(
        success=True,
        message="Usuario actualizado exitosamente"
    )


# ============================================================
# ENDPOINTS DE HEALTH CHECK
# ============================================================

@router.get("/health", response_model=APIResponse)
async def auth_health_check():
    """
    Health check del servicio de autenticación.
    """
    health = await auth_service.health_check()

    status_code = 200 if health['status'] == 'healthy' else 503

    return APIResponse(
        success=health['status'] in ('healthy', 'degraded'),
        message=f"Auth service: {health['status']}",
        data=health
    )


@router.get("/table-schema", response_model=APIResponse)
async def get_table_schema():
    """Get auth_users table schema for debugging."""
    from services.otp_auth_service import get_db_connection

    try:
        conn = await get_db_connection()
        if not conn:
            return APIResponse(success=False, message="No DB connection")

        try:
            columns = await conn.fetch('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'auth_users'
                ORDER BY ordinal_position
            ''')

            return APIResponse(
                success=True,
                message="Table schema",
                data={
                    'columns': [dict(c) for c in columns]
                }
            )
        finally:
            await conn.close()
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.post("/test-login", response_model=APIResponse)
async def test_login(body: LoginRequest):
    """
    Test login without creating session (for debugging).
    """
    import bcrypt
    from services.otp_auth_service import get_db_connection

    steps = []
    try:
        steps.append("1. Starting test login")
        conn = await get_db_connection()
        if not conn:
            return APIResponse(success=False, message="No database connection", data={'steps': steps})

        steps.append("2. Connected to database")
        try:
            row = await conn.fetchrow('''
                SELECT id, email, full_name, password_hash, role, status
                FROM auth_users
                WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            ''', body.email)

            steps.append(f"3. Query executed, row found: {bool(row)}")

            if not row:
                return APIResponse(success=False, message="User not found", data={'steps': steps})

            steps.append(f"4. User status: {row['status']}, role: {row['role']}")
            steps.append(f"5. Password hash exists: {bool(row['password_hash'])}")

            if not row['password_hash']:
                return APIResponse(success=False, message="No password hash", data={'steps': steps})

            steps.append("6. Attempting bcrypt check...")
            password_valid = bcrypt.checkpw(body.password.encode('utf-8'), row['password_hash'].encode('utf-8'))
            steps.append(f"7. Password valid: {password_valid}")

            if not password_valid:
                return APIResponse(success=False, message="Invalid password", data={'steps': steps})

            return APIResponse(
                success=True,
                message="Test login successful - password verified",
                data={
                    'steps': steps,
                    'user': {
                        'id': str(row['id']),
                        'email': row['email'],
                        'full_name': row['full_name'],
                        'role': row['role']
                    }
                }
            )

        finally:
            await conn.close()

    except Exception as e:
        steps.append(f"ERROR: {str(e)}")
        return APIResponse(success=False, message=f"Error: {str(e)}", data={'steps': steps})


@router.post("/init-auth-tables", response_model=APIResponse)
async def init_auth_tables():
    """
    Initialize auth tables in the database.
    Creates auth_users and auth_sessions if they don't exist.
    """
    from services.otp_auth_service import get_db_connection
    import bcrypt

    try:
        conn = await get_db_connection()
        if not conn:
            return APIResponse(success=False, message="No database connection")

        try:
            # Check if tables already exist
            auth_users_exists = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'auth_users'
                )
            ''')

            if auth_users_exists:
                return APIResponse(
                    success=True,
                    message="Tables already exist",
                    data={'auth_users_exists': True}
                )

            # Create auth_users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS auth_users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    email_verified BOOLEAN DEFAULT false,
                    password_hash VARCHAR(255),
                    full_name VARCHAR(255) NOT NULL,
                    empresa_id UUID,
                    company_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'user',
                    status VARCHAR(50) DEFAULT 'pending',
                    auth_method VARCHAR(20) DEFAULT 'otp',
                    last_login_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    deleted_at TIMESTAMP WITH TIME ZONE
                )
            ''')

            # Create auth_sessions table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    token_hash VARCHAR(255) NOT NULL,
                    token_prefix VARCHAR(8),
                    auth_method VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id)')

            # Create superadmin user
            password_hash = bcrypt.hashpw('Sillybanana142#'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            await conn.execute('''
                INSERT INTO auth_users (email, full_name, password_hash, role, status, auth_method, email_verified)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    status = EXCLUDED.status,
                    auth_method = EXCLUDED.auth_method
            ''', 'santiago@satma.mx', 'Santiago Superadmin', password_hash, 'super_admin', 'active', 'password', True)

            return APIResponse(
                success=True,
                message="Auth tables created and superadmin initialized",
                data={
                    'tables_created': ['auth_users', 'auth_sessions'],
                    'superadmin_created': 'santiago@satma.mx'
                }
            )

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Init auth tables error: {e}", exc_info=True)
        return APIResponse(
            success=False,
            message=f"Error: {str(e)}",
            data={'error': str(e)}
        )


@router.get("/database-status", response_model=APIResponse)
async def database_status():
    """
    Database status for auth service.
    """
    from services.otp_auth_service import get_db_connection
    import os

    result = {
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'database_url_preview': '',
        'connection_ok': False,
        'tables': {}
    }

    # Show preview of DATABASE_URL (masked)
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        # Mask the password part
        if '@' in db_url:
            parts = db_url.split('@')
            result['database_url_preview'] = '***@' + parts[-1][:30] + '...'
        else:
            result['database_url_preview'] = db_url[:20] + '...'

    try:
        conn = await get_db_connection()
        if conn:
            result['connection_ok'] = True
            try:
                # Check auth tables
                for table in ['auth_users', 'auth_sessions', 'usuarios_autorizados', 'codigos_otp', 'sesiones_otp']:
                    exists = await conn.fetchval('''
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = $1
                        )
                    ''', table)
                    count = 0
                    if exists:
                        count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    result['tables'][table] = {'exists': exists, 'count': count}
            finally:
                await conn.close()

        return APIResponse(
            success=result['connection_ok'],
            message="Database status",
            data=result
        )
    except Exception as e:
        result['error'] = str(e)
        return APIResponse(
            success=False,
            message=f"Database error: {str(e)}",
            data=result
        )


# ============================================================
# ENDPOINTS LEGACY (Compatibilidad)
# ============================================================

@router.get("/companies")
async def get_companies():
    """
    Obtener lista de empresas (público).
    """
    from services.unified_auth_service import DatabasePool

    try:
        async with await DatabasePool.get_connection() as conn:
            rows = await conn.fetch('''
                SELECT id, name FROM companies WHERE is_active = true ORDER BY name
            ''')

            return {
                'success': True,
                'companies': [{'id': str(row['id']), 'name': row['name']} for row in rows]
            }
    except Exception:
        return {'success': True, 'companies': []}


@router.get("/admin/companies")
async def get_admin_companies(admin: User = Depends(get_admin_user)):
    """
    Obtener lista de empresas (admin).
    """
    from services.unified_auth_service import DatabasePool

    async with await DatabasePool.get_connection() as conn:
        rows = await conn.fetch('''
            SELECT name FROM companies WHERE is_active = true ORDER BY name
        ''')

        return {
            'success': True,
            'companies': [row['name'] for row in rows]
        }
