"""
REVISAR.IA - Servicio de Autenticación Unificado
================================================

Este servicio reemplaza y consolida:
- auth_service.py (JWT stateless)
- otp_auth_service.py (OTP con fallback demo)
- user_db.py (SQLAlchemy parcial)

Características:
- Sistema único de autenticación (password + OTP)
- Rate limiting en base de datos (escalable)
- Sesiones en base de datos (revocables)
- Auditoría completa
- Manejo de errores robusto
- Health checks integrados

Autor: Claude Code
Fecha: 2026-01-27
"""

import os
import re
import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import asynccontextmanager

import asyncpg
import bcrypt
from jose import jwt, JWTError

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when email sending fails"""
    pass

# ============================================================
# CONFIGURACIÓN
# ============================================================

class AuthConfig:
    """Configuración centralizada de autenticación."""

    # Database
    DATABASE_URL: str = os.environ.get('DATABASE_URL', '')

    # JWT
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET') or os.environ.get('JWT_SECRET_KEY', '')
    ALGORITHM: str = 'HS256'

    # Sesiones
    SESSION_DURATION_HOURS: int = int(os.environ.get('SESSION_DURATION_HOURS', '168'))  # 7 días
    SESSION_REFRESH_HOURS: int = int(os.environ.get('SESSION_REFRESH_HOURS', '24'))

    # OTP
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = int(os.environ.get('OTP_EXPIRY_MINUTES', '5'))
    OTP_MAX_ATTEMPTS: int = 3

    # Rate Limiting
    LOGIN_MAX_ATTEMPTS: int = int(os.environ.get('LOGIN_MAX_ATTEMPTS', '5'))
    LOGIN_WINDOW_MINUTES: int = int(os.environ.get('LOGIN_WINDOW_MINUTES', '15'))
    LOGIN_BLOCK_MINUTES: int = int(os.environ.get('LOGIN_BLOCK_MINUTES', '15'))

    OTP_REQUEST_MAX: int = int(os.environ.get('OTP_REQUEST_MAX', '3'))
    OTP_REQUEST_WINDOW_MINUTES: int = int(os.environ.get('OTP_REQUEST_WINDOW_MINUTES', '10'))

    # Password
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 72  # Límite de bcrypt

    # Environment
    ENVIRONMENT: str = os.environ.get('ENVIRONMENT', 'production').lower()
    IS_DEVELOPMENT: bool = ENVIRONMENT in ('development', 'dev', 'local', 'test')

    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """Valida la configuración y retorna (is_valid, errors)."""
        errors = []

        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL no configurado")

        if not cls.SECRET_KEY:
            if cls.IS_DEVELOPMENT:
                logger.warning("⚠️ SECRET_KEY no configurado - usando valor temporal para desarrollo")
                cls.SECRET_KEY = f"DEV-ONLY-{secrets.token_hex(32)}"
            else:
                errors.append("SECRET_KEY no configurado (requerido en producción)")

        if len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY debe tener al menos 32 caracteres")

        return len(errors) == 0, errors


# ============================================================
# MODELOS DE DATOS
# ============================================================

class UserStatus(str, Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    BLOCKED = 'blocked'
    DELETED = 'deleted'


class UserRole(str, Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'
    VIEWER = 'viewer'


class AuthMethod(str, Enum):
    PASSWORD = 'password'
    OTP = 'otp'
    BOTH = 'both'
    SSO = 'sso'


class AuthAction(str, Enum):
    LOGIN = 'login'
    LOGOUT = 'logout'
    OTP_REQUEST = 'otp_request'
    OTP_VERIFY = 'otp_verify'
    PASSWORD_RESET = 'password_reset'
    REGISTER = 'register'
    SESSION_REFRESH = 'session_refresh'


class AuthResult(str, Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'
    BLOCKED = 'blocked'
    ERROR = 'error'


@dataclass
class User:
    """Modelo de usuario."""
    id: str
    email: str
    full_name: str
    role: str
    status: str
    auth_method: str
    empresa_id: Optional[str] = None
    company_name: Optional[str] = None
    email_verified: bool = False
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON."""
        return {
            'user_id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'auth_method': self.auth_method,
            'empresa_id': self.empresa_id,
            'company_name': self.company_name,
            'email_verified': self.email_verified,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def can_login(self) -> Tuple[bool, Optional[str]]:
        """Verifica si el usuario puede hacer login."""
        if self.status == UserStatus.DELETED.value:
            return False, "Cuenta eliminada"
        if self.status == UserStatus.BLOCKED.value:
            return False, "Cuenta bloqueada"
        if self.status == UserStatus.SUSPENDED.value:
            return False, "Cuenta suspendida"
        if self.status == UserStatus.PENDING.value:
            return False, "Cuenta pendiente de aprobación"
        return True, None


@dataclass
class Session:
    """Modelo de sesión."""
    id: str
    user_id: str
    token: str
    auth_method: str
    expires_at: datetime
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class AuthResponse:
    """Respuesta estándar de autenticación."""
    success: bool
    message: str
    user: Optional[User] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None  # Segundos hasta poder reintentar

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON response."""
        result = {
            'success': self.success,
            'message': self.message,
        }
        if self.success and self.user:
            result['data'] = {
                'user': self.user.to_dict(),
                'token': self.token,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            }
        if not self.success:
            result['error'] = {
                'code': self.error_code or 'AUTH_ERROR',
                'message': self.message,
            }
            if self.retry_after:
                result['error']['retry_after'] = self.retry_after
        return result


# ============================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================

class AuthError(Exception):
    """Error base de autenticación."""
    def __init__(self, message: str, code: str = 'AUTH_ERROR', status_code: int = 401):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(AuthError):
    """Error de rate limiting."""
    def __init__(self, message: str, retry_after: int):
        super().__init__(message, 'RATE_LIMITED', 429)
        self.retry_after = retry_after


class InvalidCredentialsError(AuthError):
    """Credenciales inválidas."""
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message, 'INVALID_CREDENTIALS', 401)


class AccountBlockedError(AuthError):
    """Cuenta bloqueada."""
    def __init__(self, message: str = "Cuenta bloqueada"):
        super().__init__(message, 'ACCOUNT_BLOCKED', 403)


class SessionExpiredError(AuthError):
    """Sesión expirada."""
    def __init__(self, message: str = "Sesión expirada"):
        super().__init__(message, 'SESSION_EXPIRED', 401)


# ============================================================
# POOL DE CONEXIONES
# ============================================================

class DatabasePool:
    """Gestiona el pool de conexiones a la base de datos."""

    _pool: Optional[asyncpg.Pool] = None
    _initialized: bool = False

    @classmethod
    async def initialize(cls) -> bool:
        """Inicializa el pool de conexiones."""
        if cls._initialized and cls._pool:
            return True

        if not AuthConfig.DATABASE_URL:
            logger.error("❌ DATABASE_URL no configurado")
            return False

        try:
            # Limpiar URL para asyncpg
            db_url = AuthConfig.DATABASE_URL
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)

            # Remover sslmode si existe (asyncpg lo maneja diferente)
            if '?sslmode=' in db_url or '&sslmode=' in db_url:
                import re
                db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)

            cls._pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
                statement_cache_size=0,  # Desactivar cache para compatibilidad
            )

            # Verificar conexión
            async with cls._pool.acquire() as conn:
                await conn.fetchval('SELECT 1')

            cls._initialized = True
            logger.info("✅ Pool de conexiones de autenticación inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando pool de DB: {e}")
            cls._pool = None
            cls._initialized = False
            return False

    @classmethod
    async def get_connection(cls):
        """Obtiene una conexión del pool."""
        if not cls._initialized:
            await cls.initialize()

        if not cls._pool:
            raise AuthError("Base de datos no disponible", 'DB_UNAVAILABLE', 503)

        return cls._pool.acquire()

    @classmethod
    async def close(cls):
        """Cierra el pool de conexiones."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._initialized = False
            logger.info("Pool de conexiones cerrado")

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Verifica el estado de la base de datos."""
        try:
            if not cls._pool:
                return {'status': 'error', 'message': 'Pool no inicializado'}

            async with cls._pool.acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                pool_size = cls._pool.get_size()
                free_size = cls._pool.get_idle_size()

            return {
                'status': 'healthy',
                'pool_size': pool_size,
                'free_connections': free_size,
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


# ============================================================
# SERVICIO DE AUTENTICACIÓN UNIFICADO
# ============================================================

class UnifiedAuthService:
    """
    Servicio de autenticación unificado.

    Soporta:
    - Login con contraseña
    - Login con OTP
    - Sesiones en base de datos
    - Rate limiting en base de datos
    - Auditoría completa
    """

    def __init__(self):
        self._email_service = None

    # ========================================
    # UTILIDADES DE HASHING
    # ========================================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña con bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verifica contraseña contra hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def generate_token() -> str:
        """Genera un token seguro."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash de token para almacenamiento."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        """Genera código OTP de 6 dígitos."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(AuthConfig.OTP_LENGTH)])

    # ========================================
    # RATE LIMITING
    # ========================================

    async def check_rate_limit(
        self,
        identifier: str,
        identifier_type: str,
        action: str,
        max_attempts: int = None,
        window_minutes: int = None,
        block_minutes: int = None
    ) -> Tuple[bool, int, Optional[datetime]]:
        """
        Verifica rate limit en la base de datos.

        Returns:
            (is_blocked, attempts_remaining, blocked_until)
        """
        max_attempts = max_attempts or AuthConfig.LOGIN_MAX_ATTEMPTS
        window_minutes = window_minutes or AuthConfig.LOGIN_WINDOW_MINUTES
        block_minutes = block_minutes or AuthConfig.LOGIN_BLOCK_MINUTES

        async with await DatabasePool.get_connection() as conn:
            result = await conn.fetchrow('''
                SELECT * FROM check_rate_limit($1, $2, $3, $4, $5, $6)
            ''', identifier, identifier_type, action, max_attempts, window_minutes, block_minutes)

            if result:
                is_blocked = result['is_blocked'] or result['should_block']
                attempts_remaining = result['attempts_remaining']
                blocked_until = result['blocked_until']

                if is_blocked:
                    # Calcular segundos hasta desbloqueo
                    if blocked_until:
                        retry_after = int((blocked_until - datetime.now(timezone.utc)).total_seconds())
                        raise RateLimitError(
                            f"Demasiados intentos. Intenta de nuevo en {retry_after // 60} minutos.",
                            max(0, retry_after)
                        )

                return is_blocked, attempts_remaining, blocked_until

        return False, max_attempts, None

    async def clear_rate_limit(self, identifier: str, identifier_type: str, action: str):
        """Limpia el rate limit después de un login exitoso."""
        async with await DatabasePool.get_connection() as conn:
            await conn.execute('''
                DELETE FROM auth_rate_limits
                WHERE identifier = $1 AND identifier_type = $2 AND action = $3
            ''', identifier, identifier_type, action)

    # ========================================
    # AUDITORÍA
    # ========================================

    async def log_auth_event(
        self,
        action: str,
        result: str,
        user_id: str = None,
        email: str = None,
        ip_address: str = None,
        user_agent: str = None,
        failure_reason: str = None,
        metadata: Dict = None
    ):
        """Registra evento de auditoría."""
        try:
            async with await DatabasePool.get_connection() as conn:
                await conn.execute('''
                    SELECT log_auth_event($1, $2, $3, $4, $5, $6, $7, $8)
                ''', user_id, email, action, result, ip_address, user_agent, failure_reason,
                    json.dumps(metadata or {}))
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")

    # ========================================
    # GESTIÓN DE USUARIOS
    # ========================================

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene usuario por email."""
        async with await DatabasePool.get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT id, email, full_name, role, status, auth_method,
                       empresa_id, company_name, email_verified,
                       last_login_at, created_at, metadata
                FROM auth_users
                WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            ''', email)

            if not row:
                return None

            return User(
                id=str(row['id']),
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                status=row['status'],
                auth_method=row['auth_method'],
                empresa_id=str(row['empresa_id']) if row['empresa_id'] else None,
                company_name=row['company_name'],
                email_verified=row['email_verified'],
                last_login_at=row['last_login_at'],
                created_at=row['created_at'],
                metadata=row['metadata'] or {}
            )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Obtiene usuario por ID."""
        async with await DatabasePool.get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT id, email, full_name, role, status, auth_method,
                       empresa_id, company_name, email_verified,
                       last_login_at, created_at, metadata
                FROM auth_users
                WHERE id = $1 AND deleted_at IS NULL
            ''', user_id)

            if not row:
                return None

            return User(
                id=str(row['id']),
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                status=row['status'],
                auth_method=row['auth_method'],
                empresa_id=str(row['empresa_id']) if row['empresa_id'] else None,
                company_name=row['company_name'],
                email_verified=row['email_verified'],
                last_login_at=row['last_login_at'],
                created_at=row['created_at'],
                metadata=row['metadata'] or {}
            )

    async def create_user(
        self,
        email: str,
        full_name: str,
        password: str = None,
        role: str = 'user',
        auth_method: str = 'otp',
        status: str = 'pending',
        empresa_id: str = None,
        company_name: str = None,
        auto_approve: bool = False
    ) -> User:
        """Crea un nuevo usuario."""
        # Validaciones
        email = email.lower().strip()
        if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email):
            raise AuthError("Email inválido", 'INVALID_EMAIL', 400)

        password_hash = None
        if password:
            if len(password) < AuthConfig.PASSWORD_MIN_LENGTH:
                raise AuthError(
                    f"La contraseña debe tener al menos {AuthConfig.PASSWORD_MIN_LENGTH} caracteres",
                    'PASSWORD_TOO_SHORT', 400
                )
            if len(password.encode('utf-8')) > AuthConfig.PASSWORD_MAX_LENGTH:
                raise AuthError("La contraseña es demasiado larga", 'PASSWORD_TOO_LONG', 400)
            password_hash = self.hash_password(password)
            auth_method = 'password' if auth_method == 'otp' else auth_method

        if auto_approve:
            status = 'active'

        async with await DatabasePool.get_connection() as conn:
            # Verificar si ya existe
            existing = await conn.fetchval(
                'SELECT id FROM auth_users WHERE LOWER(email) = LOWER($1)', email
            )
            if existing:
                raise AuthError("El email ya está registrado", 'EMAIL_EXISTS', 400)

            # Crear usuario
            row = await conn.fetchrow('''
                INSERT INTO auth_users (
                    email, full_name, password_hash, role, status, auth_method,
                    empresa_id, company_name, approval_required
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, email, full_name, role, status, auth_method,
                          empresa_id, company_name, email_verified, created_at
            ''', email, full_name, password_hash, role, status, auth_method,
                empresa_id, company_name, not auto_approve)

            user = User(
                id=str(row['id']),
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                status=row['status'],
                auth_method=row['auth_method'],
                empresa_id=str(row['empresa_id']) if row['empresa_id'] else None,
                company_name=row['company_name'],
                email_verified=row['email_verified'],
                created_at=row['created_at']
            )

            await self.log_auth_event(
                action='register',
                result='success',
                user_id=user.id,
                email=user.email
            )

            return user

    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Actualiza la contraseña de un usuario."""
        if len(new_password) < AuthConfig.PASSWORD_MIN_LENGTH:
            raise AuthError(
                f"La contraseña debe tener al menos {AuthConfig.PASSWORD_MIN_LENGTH} caracteres",
                'PASSWORD_TOO_SHORT', 400
            )

        password_hash = self.hash_password(new_password)

        async with await DatabasePool.get_connection() as conn:
            result = await conn.execute('''
                UPDATE auth_users
                SET password_hash = $1, password_changed_at = NOW(), updated_at = NOW()
                WHERE id = $2 AND deleted_at IS NULL
            ''', password_hash, user_id)

            return 'UPDATE 1' in result

    # ========================================
    # SESIONES
    # ========================================

    async def create_session(
        self,
        user: User,
        auth_method: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Session:
        """Crea una nueva sesión."""
        token = self.generate_token()
        token_hash = self.hash_token(token)
        token_prefix = token[:8]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=AuthConfig.SESSION_DURATION_HOURS)

        async with await DatabasePool.get_connection() as conn:
            row = await conn.fetchrow('''
                INSERT INTO auth_sessions (
                    user_id, token_hash, token_prefix, auth_method,
                    expires_at, ip_address, user_agent
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, created_at
            ''', user.id, token_hash, token_prefix, auth_method, expires_at, ip_address, user_agent)

            # Actualizar último login del usuario
            await conn.execute('''
                UPDATE auth_users
                SET last_login_at = NOW(), last_login_ip = $1, last_login_user_agent = $2
                WHERE id = $3
            ''', ip_address, user_agent, user.id)

        return Session(
            id=str(row['id']),
            user_id=user.id,
            token=token,  # Token real, no el hash
            auth_method=auth_method,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=row['created_at']
        )

    async def validate_session(self, token: str) -> Tuple[Optional[Session], Optional[User]]:
        """Valida una sesión y retorna la sesión y el usuario."""
        token_hash = self.hash_token(token)

        async with await DatabasePool.get_connection() as conn:
            row = await conn.fetchrow('''
                SELECT s.id, s.user_id, s.auth_method, s.expires_at, s.is_active,
                       s.ip_address, s.user_agent, s.created_at,
                       u.email, u.full_name, u.role, u.status, u.auth_method as user_auth_method,
                       u.empresa_id, u.company_name, u.email_verified
                FROM auth_sessions s
                JOIN auth_users u ON u.id = s.user_id
                WHERE s.token_hash = $1 AND s.is_active = true
                  AND s.expires_at > NOW() AND u.deleted_at IS NULL
            ''', token_hash)

            if not row:
                return None, None

            # Verificar estado del usuario
            if row['status'] != 'active':
                return None, None

            # Actualizar última actividad
            await conn.execute('''
                UPDATE auth_sessions SET last_activity_at = NOW() WHERE id = $1
            ''', row['id'])

            session = Session(
                id=str(row['id']),
                user_id=str(row['user_id']),
                token=token,
                auth_method=row['auth_method'],
                expires_at=row['expires_at'],
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                created_at=row['created_at']
            )

            user = User(
                id=str(row['user_id']),
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                status=row['status'],
                auth_method=row['user_auth_method'],
                empresa_id=str(row['empresa_id']) if row['empresa_id'] else None,
                company_name=row['company_name'],
                email_verified=row['email_verified']
            )

            return session, user

    async def revoke_session(self, token: str, reason: str = 'logout') -> bool:
        """Revoca una sesión."""
        token_hash = self.hash_token(token)

        async with await DatabasePool.get_connection() as conn:
            result = await conn.execute('''
                UPDATE auth_sessions
                SET is_active = false, revoked_at = NOW(), revoked_reason = $1
                WHERE token_hash = $2 AND is_active = true
            ''', reason, token_hash)

            return 'UPDATE 1' in result

    async def revoke_all_sessions(self, user_id: str, reason: str = 'logout_all') -> int:
        """Revoca todas las sesiones de un usuario."""
        async with await DatabasePool.get_connection() as conn:
            result = await conn.execute('''
                UPDATE auth_sessions
                SET is_active = false, revoked_at = NOW(), revoked_reason = $1
                WHERE user_id = $2 AND is_active = true
            ''', reason, user_id)

            # Extraer número de filas afectadas
            count = int(result.split()[-1]) if result else 0
            return count

    # ========================================
    # LOGIN CON CONTRASEÑA
    # ========================================

    async def login_with_password(
        self,
        email: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuthResponse:
        """
        Autentica usuario con email y contraseña.
        """
        email = email.lower().strip()

        # Verificar rate limit
        try:
            await self.check_rate_limit(email, 'email', 'login')
        except RateLimitError as e:
            await self.log_auth_event(
                action='login', result='blocked', email=email,
                ip_address=ip_address, failure_reason='rate_limited'
            )
            return AuthResponse(
                success=False,
                message=e.message,
                error_code=e.code,
                retry_after=e.retry_after
            )

        # Obtener usuario
        user = await self.get_user_by_email(email)

        if not user:
            await self.log_auth_event(
                action='login', result='failure', email=email,
                ip_address=ip_address, failure_reason='user_not_found'
            )
            return AuthResponse(
                success=False,
                message="Credenciales inválidas",
                error_code='INVALID_CREDENTIALS'
            )

        # Verificar si puede hacer login
        can_login, reason = user.can_login()
        if not can_login:
            await self.log_auth_event(
                action='login', result='failure', user_id=user.id, email=email,
                ip_address=ip_address, failure_reason=reason
            )
            return AuthResponse(
                success=False,
                message=reason,
                error_code='ACCOUNT_BLOCKED'
            )

        # Verificar contraseña
        async with await DatabasePool.get_connection() as conn:
            password_hash = await conn.fetchval(
                'SELECT password_hash FROM auth_users WHERE id = $1', user.id
            )

        if not password_hash or not self.verify_password(password, password_hash):
            await self.log_auth_event(
                action='login', result='failure', user_id=user.id, email=email,
                ip_address=ip_address, failure_reason='invalid_password'
            )
            return AuthResponse(
                success=False,
                message="Credenciales inválidas",
                error_code='INVALID_CREDENTIALS'
            )

        # Limpiar rate limit y crear sesión
        await self.clear_rate_limit(email, 'email', 'login')

        session = await self.create_session(user, 'password', ip_address, user_agent)

        await self.log_auth_event(
            action='login', result='success', user_id=user.id, email=email,
            ip_address=ip_address, metadata={'auth_method': 'password'}
        )

        return AuthResponse(
            success=True,
            message="Login exitoso",
            user=user,
            token=session.token,
            expires_at=session.expires_at
        )

    # ========================================
    # LOGIN CON OTP
    # ========================================

    async def request_otp(
        self,
        email: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuthResponse:
        """
        Solicita un código OTP para el email.
        """
        email = email.lower().strip()

        # Verificar rate limit para solicitudes OTP
        try:
            await self.check_rate_limit(
                email, 'email', 'otp_request',
                max_attempts=AuthConfig.OTP_REQUEST_MAX,
                window_minutes=AuthConfig.OTP_REQUEST_WINDOW_MINUTES
            )
        except RateLimitError as e:
            return AuthResponse(
                success=False,
                message=e.message,
                error_code=e.code,
                retry_after=e.retry_after
            )

        # Obtener usuario
        user = await self.get_user_by_email(email)

        if not user:
            # No revelar si el usuario existe o no
            return AuthResponse(
                success=False,
                message="Si el email está registrado, recibirás un código de acceso",
                error_code='USER_NOT_FOUND'
            )

        # Verificar si puede hacer login
        can_login, reason = user.can_login()
        if not can_login:
            return AuthResponse(
                success=False,
                message=reason,
                error_code='ACCOUNT_BLOCKED'
            )

        # Generar OTP
        otp_code = self.generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=AuthConfig.OTP_EXPIRY_MINUTES)

        async with await DatabasePool.get_connection() as conn:
            # Invalidar códigos anteriores
            await conn.execute('''
                UPDATE auth_otp_codes SET used = true
                WHERE user_id = $1 AND used = false
            ''', user.id)

            # Crear nuevo código
            await conn.execute('''
                INSERT INTO auth_otp_codes (
                    user_id, email, code, expires_at, requested_ip, requested_user_agent
                ) VALUES ($1, $2, $3, $4, $5, $6)
            ''', user.id, email, otp_code, expires_at, ip_address, user_agent)

        # Enviar código por email
        try:
            await self._send_otp_email(user, otp_code)
        except Exception as e:
            logger.error(f"Error enviando OTP: {e}")
            return AuthResponse(
                success=False,
                message="Error enviando código. Intenta de nuevo.",
                error_code='EMAIL_SEND_ERROR'
            )

        await self.log_auth_event(
            action='otp_request', result='success', user_id=user.id, email=email,
            ip_address=ip_address
        )

        return AuthResponse(
            success=True,
            message="Código enviado a tu email",
            user=User(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                status=user.status,
                auth_method=user.auth_method
            )  # Usuario parcial sin token
        )

    async def verify_otp(
        self,
        email: str,
        code: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuthResponse:
        """
        Verifica código OTP y crea sesión.
        """
        email = email.lower().strip()
        code = code.strip()

        # Validar formato
        if not re.match(r'^\d{6}$', code):
            return AuthResponse(
                success=False,
                message="Código inválido",
                error_code='INVALID_CODE_FORMAT'
            )

        # Verificar rate limit
        try:
            await self.check_rate_limit(email, 'email', 'otp_verify')
        except RateLimitError as e:
            await self.log_auth_event(
                action='otp_verify', result='blocked', email=email,
                ip_address=ip_address, failure_reason='rate_limited'
            )
            return AuthResponse(
                success=False,
                message=e.message,
                error_code=e.code,
                retry_after=e.retry_after
            )

        async with await DatabasePool.get_connection() as conn:
            # Buscar código válido
            row = await conn.fetchrow('''
                SELECT c.id, c.user_id, c.verification_attempts, c.max_attempts
                FROM auth_otp_codes c
                JOIN auth_users u ON u.id = c.user_id
                WHERE LOWER(c.email) = LOWER($1)
                  AND c.code = $2
                  AND c.used = false
                  AND c.expires_at > NOW()
                  AND u.deleted_at IS NULL
                ORDER BY c.created_at DESC
                LIMIT 1
            ''', email, code)

            if not row:
                await self.log_auth_event(
                    action='otp_verify', result='failure', email=email,
                    ip_address=ip_address, failure_reason='invalid_or_expired_code'
                )
                return AuthResponse(
                    success=False,
                    message="Código inválido o expirado",
                    error_code='INVALID_OTP'
                )

            # Verificar intentos
            if row['verification_attempts'] >= row['max_attempts']:
                await conn.execute('UPDATE auth_otp_codes SET used = true WHERE id = $1', row['id'])
                return AuthResponse(
                    success=False,
                    message="Código bloqueado por demasiados intentos",
                    error_code='OTP_MAX_ATTEMPTS'
                )

            # Marcar como usado
            await conn.execute('''
                UPDATE auth_otp_codes
                SET used = true, used_at = NOW(), verified_ip = $1
                WHERE id = $2
            ''', ip_address, row['id'])

        # Obtener usuario y crear sesión
        user = await self.get_user_by_id(str(row['user_id']))
        if not user:
            return AuthResponse(
                success=False,
                message="Error de autenticación",
                error_code='USER_NOT_FOUND'
            )

        # Limpiar rate limits
        await self.clear_rate_limit(email, 'email', 'otp_verify')
        await self.clear_rate_limit(email, 'email', 'otp_request')

        session = await self.create_session(user, 'otp', ip_address, user_agent)

        await self.log_auth_event(
            action='otp_verify', result='success', user_id=user.id, email=email,
            ip_address=ip_address
        )

        return AuthResponse(
            success=True,
            message="Verificación exitosa",
            user=user,
            token=session.token,
            expires_at=session.expires_at
        )

    async def _send_otp_email(self, user: User, code: str):
        """Envía el código OTP por email."""
        try:
            from services.dreamhost_email_service import email_service
            result = email_service.send_otp_email(
                recipient_email=user.email,
                recipient_name=user.full_name,
                otp_code=code,
                expires_minutes=AuthConfig.OTP_EXPIRY_MINUTES
            )
            if not result.get('success'):
                raise EmailSendError(result.get('error', 'Error desconocido al enviar email'))
        except ImportError:
            logger.warning(f"Email service no disponible. OTP para {user.email}: {code}")
            if AuthConfig.IS_DEVELOPMENT:
                logger.info(f"🔑 [DEV] OTP Code for {user.email}: {code}")

    # ========================================
    # LOGOUT
    # ========================================

    async def logout(self, token: str, ip_address: str = None) -> AuthResponse:
        """Cierra la sesión actual."""
        session, user = await self.validate_session(token)

        if not session:
            return AuthResponse(
                success=True,
                message="Sesión cerrada"  # No revelar si existía o no
            )

        await self.revoke_session(token, 'logout')

        await self.log_auth_event(
            action='logout', result='success',
            user_id=user.id if user else None,
            email=user.email if user else None,
            ip_address=ip_address
        )

        return AuthResponse(
            success=True,
            message="Sesión cerrada exitosamente"
        )

    # ========================================
    # HEALTH CHECK
    # ========================================

    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio de autenticación."""
        config_valid, config_errors = AuthConfig.validate()
        db_health = await DatabasePool.health_check()

        # Verificar tablas
        tables_ok = False
        if db_health['status'] == 'healthy':
            try:
                async with await DatabasePool.get_connection() as conn:
                    tables = await conn.fetch('''
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name IN ('auth_users', 'auth_sessions', 'auth_otp_codes', 'auth_rate_limits')
                    ''')
                    tables_ok = len(tables) == 4
            except Exception as e:
                logger.error(f"Error verificando tablas: {e}")

        status = 'healthy'
        if not config_valid or db_health['status'] != 'healthy' or not tables_ok:
            status = 'degraded' if db_health['status'] == 'healthy' else 'unhealthy'

        return {
            'status': status,
            'config': {
                'valid': config_valid,
                'errors': config_errors if not config_valid else [],
                'environment': AuthConfig.ENVIRONMENT
            },
            'database': db_health,
            'tables': {
                'all_present': tables_ok,
                'required': ['auth_users', 'auth_sessions', 'auth_otp_codes', 'auth_rate_limits']
            }
        }


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

auth_service = UnifiedAuthService()


# ============================================================
# FUNCIONES DE INICIALIZACIÓN
# ============================================================

async def init_auth_service() -> bool:
    """Inicializa el servicio de autenticación."""
    logger.info("Inicializando servicio de autenticación unificado...")

    # Validar configuración
    config_valid, errors = AuthConfig.validate()
    if not config_valid:
        for error in errors:
            logger.error(f"❌ Config error: {error}")
        if not AuthConfig.IS_DEVELOPMENT:
            return False

    # Inicializar pool de DB
    if not await DatabasePool.initialize():
        logger.error("❌ No se pudo inicializar el pool de base de datos")
        return False

    # Verificar/crear tablas
    try:
        async with await DatabasePool.get_connection() as conn:
            # Verificar si existen las tablas
            tables = await conn.fetch('''
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'auth_%'
            ''')

            if len(tables) < 4:
                logger.info("Ejecutando schema de autenticación...")
                schema_path = os.path.join(
                    os.path.dirname(__file__), '..', 'database', 'auth_schema.sql'
                )
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                    await conn.execute(schema_sql)
                    logger.info("✅ Schema de autenticación ejecutado")
                else:
                    logger.warning(f"Schema file no encontrado: {schema_path}")
    except Exception as e:
        logger.error(f"Error verificando/creando tablas: {e}")

    # Health check
    health = await auth_service.health_check()
    logger.info(f"Auth service health: {health['status']}")

    return health['status'] in ('healthy', 'degraded')


async def shutdown_auth_service():
    """Cierra el servicio de autenticación."""
    await DatabasePool.close()
    logger.info("Servicio de autenticación cerrado")
