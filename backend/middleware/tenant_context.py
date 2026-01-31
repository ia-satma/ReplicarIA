"""
Multi-tenant context middleware for strict empresa isolation.
Ensures users can only access data from their allowed companies.
"""
import os
import json
import logging
from contextvars import ContextVar
from functools import wraps
from typing import Optional, List, Callable

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

tenant_context: ContextVar[dict] = ContextVar("tenant_context", default={})


class TenantContext:
    """Immutable tenant context for the current request."""
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        empresa_id: Optional[str] = None,
        allowed_companies: Optional[List[str]] = None,
        is_admin: bool = False,
        is_authenticated: bool = False
    ):
        self._user_id = user_id
        self._empresa_id = empresa_id
        self._allowed_companies = allowed_companies or []
        self._is_admin = is_admin
        self._is_authenticated = is_authenticated
    
    @property
    def user_id(self) -> Optional[str]:
        return self._user_id
    
    @property
    def empresa_id(self) -> Optional[str]:
        return self._empresa_id
    
    @property
    def allowed_companies(self) -> List[str]:
        return self._allowed_companies
    
    @property
    def is_admin(self) -> bool:
        return self._is_admin
    
    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated
    
    def can_access_empresa(self, empresa_id: str) -> bool:
        """Check if current user can access the specified empresa using exact match."""
        if not self._is_authenticated:
            return False
        if self._is_admin:
            return True
        if not self._allowed_companies:
            return False
        
        empresa_normalized = empresa_id.lower().strip()
        return empresa_normalized in self._allowed_companies
    
    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "empresa_id": self._empresa_id,
            "allowed_companies": self._allowed_companies,
            "is_admin": self._is_admin,
            "is_authenticated": self._is_authenticated
        }


_current_tenant: ContextVar[TenantContext] = ContextVar(
    "current_tenant", 
    default=TenantContext()
)


def get_current_tenant() -> TenantContext:
    """Get the current tenant context for this request."""
    return _current_tenant.get()


def get_current_empresa_id() -> Optional[str]:
    """Get the current empresa_id from tenant context."""
    return get_current_tenant().empresa_id


def get_current_user_id() -> Optional[str]:
    """Get the current user_id from tenant context."""
    return get_current_tenant().user_id


def set_tenant_context(context: TenantContext) -> None:
    """Set the tenant context for the current request."""
    _current_tenant.set(context)


SKIP_TENANT_CHECK_PATHS = {
    "/",
    "/api/",
    "/api/health",
    "/api/status",
    "/api/stats",
    "/auth/login",
    "/auth/register",
    "/auth/token",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/token",
    "/api/auth/verify",
    "/api/auth/otp/request-code",
    "/api/auth/otp/verify-code",
    "/api/auth/otp/session",
    "/api/auth/otp/logout",
    "/api/auth/otp/status",
    "/api/auth/otp/test-email",
    "/api/auth/otp/send-test-email",
    "/api/auth/companies",
    "/api/chat/archivo",
    "/api/chat/archivo/analyze-document",
    "/api/onboarding/complete",
    "/api/durezza/health",
    "/api/durezza/estadisticas",
    "/api/durezza/stats",
    "/api/subagentes/",
    "/api/fases/",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}

SKIP_TENANT_CHECK_PREFIXES = (
    "/static",
    "/assets",
    "/dashboard",
    "/_next",
    "/favicon",
    "/api/templates",
    "/api/subagentes",
    "/api/fases",
    "/api/docs",
    "/api/health",
    "/api/empresas",
    "/api/kb",
    "/api/biblioteca",
    "/api/knowledge/health",
    "/api/knowledge/migrate",
    "/api/knowledge/public",
    "/api/test",
    "/api/upload",
    "/api/support",
    "/api/auth/admin",
    "/api/files/uploads",
    "/api/pcloud",  # pCloud endpoints for storage management
    "/api/archivo",
    "/api/agents",
    "/api/admin",
    "/api/asistente-facturacion",
    "/api/onboarding",
    "/api/clientes",
    "/api/disenar",
    "/api/defense-files",
    "/api/trafico",
    "/api/guardian",
    "/api/lista-69b",
    "/api/agentes",
    "/api/checklists",
    "/api/proveedores",
    "/api/durezza",
    "/api/contexto",
    "/api/scoring",
    "/api/versioning",
    "/api/loops",
    "/api/validacion",
    "/api/documentos",
    "/api/projects",
    "/api/usage",
    "/api/stats",
    "/templates",
)

AUTH_ONLY_PREFIXES = (
    "/api/knowledge",
    "/knowledge",
)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that establishes tenant context for each request.
    
    1. Extracts user_id from JWT Authorization header
    2. Loads allowed_companies for the user
    3. Validates X-Empresa-ID header against allowed_companies
    4. Rejects with 403 if empresa is not authorized
    5. Stores context in ContextVar for the entire request lifecycle
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Always try to build tenant context if there's auth, even for skipped routes
        # This allows decorators like @require_empresa to work on skipped routes
        try:
            context = await self._build_tenant_context(request)
            set_tenant_context(context)
        except Exception as e:
            logger.debug(f"Could not build tenant context: {e}")
            # Set empty context on error
            set_tenant_context(TenantContext())

        # Skip validation for explicitly excluded paths
        if path in SKIP_TENANT_CHECK_PATHS or path.startswith(SKIP_TENANT_CHECK_PREFIXES):
            return await call_next(request)

        # Skip non-API routes
        if not path.startswith("/api") and not path.startswith("/deliberation"):
            return await call_next(request)

        try:
            context = get_current_tenant()
            is_auth_only_route = path.startswith(AUTH_ONLY_PREFIXES)
            is_api_route = path.startswith("/api") or path.startswith("/deliberation")
            empresa_header = request.headers.get("X-Empresa-ID")

            if is_auth_only_route:
                if not context.is_authenticated:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": "Autenticación requerida",
                            "error_code": "AUTHENTICATION_REQUIRED"
                        }
                    )
                return await call_next(request)

            if is_api_route:
                if not context.is_authenticated:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": "Autenticación requerida",
                            "error_code": "AUTHENTICATION_REQUIRED"
                        }
                    )

                if not empresa_header:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": "Header X-Empresa-ID es requerido",
                            "error_code": "EMPRESA_HEADER_REQUIRED"
                        }
                    )

                if not context.can_access_empresa(empresa_header):
                    logger.warning(
                        f"Tenant access denied: user={context.user_id} "
                        f"empresa={empresa_header} allowed={context.allowed_companies}"
                    )
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "No tienes permiso para acceder a esta empresa",
                            "error_code": "EMPRESA_NOT_AUTHORIZED"
                        }
                    )

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"TenantContextMiddleware error: {e}", exc_info=True)
            # Don't silently continue - return error response
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Error interno de autenticación",
                    "error_code": "AUTH_MIDDLEWARE_ERROR"
                }
            )
    
    async def _build_tenant_context(self, request: Request) -> TenantContext:
        """Extract and validate tenant context from request."""
        auth_header = request.headers.get("Authorization")
        empresa_header = request.headers.get("X-Empresa-ID")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return TenantContext(
                empresa_id=empresa_header,
                is_authenticated=False
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            from jose import jwt, JWTError
            from services.auth_service import get_secret_key
            SECRET_KEY = get_secret_key()

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id") or payload.get("sub")
            
            if not user_id:
                return TenantContext(
                    empresa_id=empresa_header,
                    is_authenticated=False
                )
            
            user_data = await self._get_user_data(user_id)
            
            is_admin = user_data.get("is_admin", False)
            allowed_companies = user_data.get("allowed_companies", [])
            
            return TenantContext(
                user_id=str(user_id),
                empresa_id=empresa_header,
                allowed_companies=allowed_companies,
                is_admin=is_admin,
                is_authenticated=True
            )
            
        except Exception as e:
            logger.debug(f"JWT decode error: {e}")
            return TenantContext(
                empresa_id=empresa_header,
                is_authenticated=False
            )
    
    async def _get_user_data(self, user_id) -> dict:
        """Load user data including allowed_companies."""
        try:
            from services.user_db import user_service
            user = await user_service.get_user_by_id(user_id)
            
            if not user:
                return {"is_admin": False, "allowed_companies": []}
            
            allowed_companies = []
            allowed_companies_raw = getattr(user, 'allowed_companies', None)
            if allowed_companies_raw:
                try:
                    companies = json.loads(str(allowed_companies_raw))
                    if isinstance(companies, list):
                        allowed_companies = [c.lower().strip() for c in companies]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            user_company = getattr(user, 'company', None)
            if user_company:
                user_company_str = str(user_company).strip()
                empresa_id = await self._resolve_empresa_id(user_company_str)
                if empresa_id and empresa_id.lower() not in allowed_companies:
                    allowed_companies.append(empresa_id.lower())
                if user_company_str.lower() not in allowed_companies:
                    allowed_companies.append(user_company_str.lower())
            
            user_role = getattr(user, 'role', '')
            return {
                "is_admin": str(user_role) == "admin",
                "allowed_companies": allowed_companies
            }
            
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            return {"is_admin": False, "allowed_companies": []}
    
    async def _resolve_empresa_id(self, company_name: str) -> Optional[str]:
        """Look up empresa_id (UUID) from company name in the PostgreSQL companies table."""
        try:
            from sqlalchemy import text
            from services.user_db import get_session, async_session_factory
            
            if async_session_factory is None:
                return None
            
            async with get_session() as session:
                result = await session.execute(
                    text("SELECT id FROM companies WHERE name = :name LIMIT 1"),
                    {"name": company_name}
                )
                row = result.fetchone()
                if row:
                    return str(row[0])
            return None
        except Exception as e:
            logger.debug(f"Could not resolve empresa_id for '{company_name}': {e}")
            return None


def require_empresa(func: Callable) -> Callable:
    """
    Decorator that ensures a valid empresa context exists.
    
    Usage:
        @router.get("/projects")
        @require_empresa
        async def get_projects():
            empresa_id = get_current_empresa_id()
            ...
    
    Raises HTTPException 400 if no empresa context.
    Raises HTTPException 401 if not authenticated.
    Raises HTTPException 403 if empresa not authorized.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        context = get_current_tenant()
        
        if not context.is_authenticated:
            raise HTTPException(
                status_code=401,
                detail="Autenticación requerida"
            )
        
        if not context.empresa_id:
            raise HTTPException(
                status_code=400,
                detail="Header X-Empresa-ID es requerido"
            )
        
        if not context.can_access_empresa(context.empresa_id):
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta empresa"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_auth(func: Callable) -> Callable:
    """
    Decorator that ensures the user is authenticated.
    
    Usage:
        @router.get("/profile")
        @require_auth
        async def get_profile():
            user_id = get_current_user_id()
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        context = get_current_tenant()
        
        if not context.is_authenticated:
            raise HTTPException(
                status_code=401,
                detail="Autenticación requerida"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    Decorator that ensures the user is an admin.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        context = get_current_tenant()
        
        if not context.is_authenticated:
            raise HTTPException(
                status_code=401,
                detail="Autenticación requerida"
            )
        
        if not context.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Se requieren permisos de administrador"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper
