"""
Exception Handlers para Revisar.IA
Handlers globales para excepciones específicas del sistema.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


async def candado_exception_handler(request: Request, exc):
    """Handler global para excepciones de candados bloqueados"""
    
    logger.warning(
        f"Candado bloqueó request - "
        f"Path: {request.url.path} - "
        f"Fase: {exc.fase} - "
        f"Bloqueos: {exc.bloqueos}"
    )
    
    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": "CANDADO_BLOQUEADO",
            "fase_bloqueada": exc.fase,
            "bloqueos": exc.bloqueos,
            "mensaje": exc.mensaje,
            "accion_requerida": "Resolver los bloqueos listados antes de intentar avanzar"
        }
    )
