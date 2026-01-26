"""
Error Handler - Manejo centralizado de errores
==============================================

Este módulo proporciona funciones para manejar errores de forma consistente
en toda la aplicación, evitando los `except:` genéricos.

USO:
    from services.error_handler import handle_route_error, safe_execute

    @router.get("/endpoint")
    async def my_endpoint():
        try:
            # ... código ...
        except Exception as e:
            return handle_route_error(e, "Error en my_endpoint")

    # O usando el decorator
    @safe_execute("mi_operación")
    async def my_function():
        # ... código ...
"""

import logging
import traceback
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from jose import JWTError
import asyncpg

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AppError(Exception):
    """Base exception para errores de la aplicación"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Recurso no encontrado"""
    def __init__(self, message: str = "Recurso no encontrado", details: Optional[dict] = None):
        super().__init__(message, status_code=404, details=details)


class UnauthorizedError(AppError):
    """No autorizado"""
    def __init__(self, message: str = "No autorizado", details: Optional[dict] = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(AppError):
    """Acceso prohibido"""
    def __init__(self, message: str = "Acceso prohibido", details: Optional[dict] = None):
        super().__init__(message, status_code=403, details=details)


class ValidationException(AppError):
    """Error de validación"""
    def __init__(self, message: str = "Error de validación", details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)


def handle_route_error(
    error: Exception,
    context: str = "operación",
    log_traceback: bool = True
) -> JSONResponse:
    """
    Maneja errores de forma consistente en rutas FastAPI.

    Args:
        error: La excepción capturada
        context: Descripción del contexto donde ocurrió el error
        log_traceback: Si se debe loguear el traceback completo

    Returns:
        JSONResponse con el error formateado
    """
    # Si ya es una HTTPException, re-lanzarla
    if isinstance(error, HTTPException):
        raise error

    # Errores de la aplicación
    if isinstance(error, AppError):
        logger.warning(f"{context}: {error.message}")
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message, "error_type": type(error).__name__, **error.details}
        )

    # Errores de JWT
    if isinstance(error, JWTError):
        logger.warning(f"JWT error en {context}: {str(error)}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o expirado"}
        )

    # Errores de validación de Pydantic
    if isinstance(error, ValidationError):
        logger.warning(f"Validation error en {context}: {str(error)}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Error de validación", "errors": error.errors()}
        )

    # Errores de base de datos PostgreSQL
    if isinstance(error, asyncpg.PostgresError):
        logger.error(f"Database error en {context}: {str(error)}")
        if log_traceback:
            logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Error de base de datos"}
        )

    # Errores de conexión
    if isinstance(error, (ConnectionError, TimeoutError)):
        logger.error(f"Connection error en {context}: {str(error)}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Servicio temporalmente no disponible"}
        )

    # Errores de valor
    if isinstance(error, (ValueError, TypeError)):
        logger.warning(f"Value error en {context}: {str(error)}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(error)}
        )

    # Errores genéricos - loguear completamente pero no exponer detalles
    logger.error(f"Unexpected error en {context}: {type(error).__name__}: {str(error)}")
    if log_traceback:
        logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )


def safe_execute(context: str = "operación"):
    """
    Decorator para manejar errores de forma segura en funciones async.

    USO:
        @safe_execute("obtener_usuario")
        async def get_user(user_id: str):
            # ... código que puede fallar ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error en {context}"
                ) from e
        return wrapper
    return decorator


def log_and_raise(
    error: Exception,
    context: str,
    status_code: int = 500,
    expose_message: bool = False
):
    """
    Loguea un error y lanza HTTPException.

    Args:
        error: La excepción original
        context: Contexto del error
        status_code: Código HTTP a retornar
        expose_message: Si se debe exponer el mensaje de error al cliente
    """
    logger.error(f"Error en {context}: {type(error).__name__}: {str(error)}")
    logger.error(traceback.format_exc())

    detail = str(error) if expose_message else f"Error en {context}"
    raise HTTPException(status_code=status_code, detail=detail)


async def safe_db_operation(
    operation: Callable,
    context: str = "operación de BD",
    default: Any = None
) -> Any:
    """
    Ejecuta una operación de base de datos de forma segura.

    Args:
        operation: Función async a ejecutar
        context: Descripción de la operación
        default: Valor a retornar si hay error

    Returns:
        El resultado de la operación o el valor default
    """
    try:
        return await operation()
    except asyncpg.PostgresError as e:
        logger.error(f"Database error en {context}: {str(e)}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error en {context}: {str(e)}")
        return default
