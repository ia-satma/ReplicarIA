"""
Auth Service - Servicio centralizado de autenticación
=====================================================

Este módulo centraliza toda la lógica de autenticación para evitar
duplicación de código y asegurar consistencia en toda la aplicación.

USO:
    from services.auth_service import get_secret_key, verify_token, get_current_user

IMPORTANTE:
    - SECRET_KEY DEBE estar configurado en variables de entorno
    - NO usar fallbacks en producción
"""

import os
import logging
from functools import lru_cache
from typing import Optional, Dict, Any

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# Security scheme para FastAPI
security = HTTPBearer(auto_error=False)

# Cache para el secret key
_secret_key_cache: Optional[str] = None


def get_secret_key() -> str:
    """
    Obtiene el SECRET_KEY de las variables de entorno.

    IMPORTANTE: En producción, DEBE estar configurado.
    NO hay fallback por seguridad.

    Returns:
        str: El secret key configurado

    Raises:
        RuntimeError: Si SECRET_KEY no está configurado
    """
    global _secret_key_cache

    if _secret_key_cache is not None:
        return _secret_key_cache

    # Intentar múltiples nombres de variable de entorno
    secret = (
        os.environ.get("SECRET_KEY") or
        os.environ.get("SESSION_SECRET") or
        os.environ.get("JWT_SECRET_KEY")
    )

    if not secret:
        # En desarrollo, permitir un warning pero NO un fallback inseguro
        env = os.environ.get("ENVIRONMENT", "production").lower()
        if env in ("development", "dev", "local", "test"):
            logger.warning(
                "⚠️  SECRET_KEY no configurado - usando valor temporal para desarrollo. "
                "NUNCA usar en producción!"
            )
            # Este valor es obvio y no debe usarse en producción
            secret = "DEVELOPMENT-ONLY-KEY-DO-NOT-USE-IN-PRODUCTION-" + os.urandom(16).hex()
        else:
            logger.error("❌ SECRET_KEY no configurado en producción!")
            raise RuntimeError(
                "SECRET_KEY environment variable is required. "
                "Set SECRET_KEY, SESSION_SECRET, or JWT_SECRET_KEY."
            )

    _secret_key_cache = secret
    return secret


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifica y decodifica un token JWT.

    Args:
        token: El token JWT a verificar

    Returns:
        Dict con el payload del token

    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    try:
        secret = get_secret_key()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency de FastAPI para obtener el usuario actual del token.

    Uso:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}

    Args:
        credentials: Credenciales del header Authorization

    Returns:
        Dict con información del usuario del token

    Raises:
        HTTPException: Si no hay token o es inválido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_token(credentials.credentials)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency opcional - retorna None si no hay token en lugar de error.

    Útil para endpoints que funcionan diferente con/sin autenticación.
    """
    if not credentials:
        return None

    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None


def get_empresa_id_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extrae el empresa_id del token JWT si existe.
    """
    if not credentials:
        return None

    try:
        payload = verify_token(credentials.credentials)
        return payload.get("empresa_id")
    except HTTPException:
        return None


def require_role(required_roles: list[str]):
    """
    Decorator/dependency para requerir roles específicos.

    Uso:
        @router.get("/admin-only")
        async def admin_route(user: dict = Depends(require_role(["admin"]))):
            return {"admin": True}
    """
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol requerido: {required_roles}. Tu rol: {user_role}"
            )
        return user
    return role_checker


# Alias para compatibilidad
get_secret = get_secret_key
