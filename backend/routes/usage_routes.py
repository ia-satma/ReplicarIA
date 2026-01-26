"""
Rutas para Rate Limiting y Usage Tracking.
Proporciona endpoints para dashboard de uso y consulta de límites.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage", tags=["Usage"])


async def get_current_empresa_id():
    """Placeholder for tenant context - returns demo empresa."""
    return "00000000-0000-0000-0000-000000000001"


async def get_db_pool():
    """Get database pool from services."""
    try:
        from services.database_pg import get_pool
        return await get_pool()
    except Exception as e:
        logger.error(f"Failed to get DB pool: {e}")
        return None


@router.get("/dashboard")
async def get_usage_dashboard(empresa_id: Optional[str] = None):
    """
    Obtiene estadísticas de uso para el dashboard.
    Muestra requests/tokens usados hoy y límites del plan.
    """
    if not empresa_id:
        empresa_id = await get_current_empresa_id()
    
    pool = await get_db_pool()
    if not pool:
        return {
            "plan": "free",
            "requests_hoy": 0,
            "tokens_hoy": 0,
            "limite_requests": 50,
            "limite_tokens": 100000,
            "pct_requests": 0,
            "pct_tokens": 0,
            "message": "Database not available"
        }
    
    try:
        from services.rate_limiter_service import RateLimiterService
        service = RateLimiterService(pool)
        stats = await service.get_usage_stats(empresa_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {
            "plan": "free",
            "requests_hoy": 0,
            "tokens_hoy": 0,
            "limite_requests": 50,
            "limite_tokens": 100000,
            "error": str(e)
        }


@router.get("/monthly")
async def get_monthly_usage(empresa_id: Optional[str] = None, months: int = 12):
    """
    Obtiene histórico de uso mensual.
    Útil para reportes y facturación.
    """
    if not empresa_id:
        empresa_id = await get_current_empresa_id()
    
    pool = await get_db_pool()
    if not pool:
        return {"months": [], "message": "Database not available"}
    
    try:
        from services.rate_limiter_service import RateLimiterService
        service = RateLimiterService(pool)
        monthly = await service.get_monthly_usage(empresa_id)
        return {"months": monthly}
    except Exception as e:
        logger.error(f"Error getting monthly usage: {e}")
        return {"months": [], "error": str(e)}


@router.get("/limits")
async def get_current_limits(empresa_id: Optional[str] = None):
    """
    Obtiene los límites actuales del plan.
    """
    if not empresa_id:
        empresa_id = await get_current_empresa_id()
    
    pool = await get_db_pool()
    if not pool:
        return {
            "plan": "free",
            "requests_per_day": 50,
            "tokens_per_day": 100000,
            "requests_remaining": 50,
            "tokens_remaining": 100000
        }
    
    try:
        from services.rate_limiter_service import RateLimiterService
        service = RateLimiterService(pool)
        result = await service.check_limits_only(empresa_id)
        return {
            "plan": result.plan,
            "requests_remaining": result.requests_remaining,
            "tokens_remaining": result.tokens_remaining,
            "message": result.message
        }
    except Exception as e:
        logger.error(f"Error getting limits: {e}")
        return {
            "plan": "free",
            "requests_remaining": 50,
            "tokens_remaining": 100000,
            "error": str(e)
        }


@router.get("/plans")
async def get_available_plans():
    """
    Lista los planes disponibles con sus límites.
    """
    pool = await get_db_pool()
    if not pool:
        return {
            "plans": [
                {"id": "free", "nombre": "Gratuito", "requests_per_day": 50, "tokens_per_day": 100000, "precio": 0},
                {"id": "starter", "nombre": "Starter", "requests_per_day": 500, "tokens_per_day": 1000000, "precio": 49},
                {"id": "pro", "nombre": "Profesional", "requests_per_day": 5000, "tokens_per_day": 10000000, "precio": 149},
                {"id": "enterprise", "nombre": "Enterprise", "requests_per_day": 50000, "tokens_per_day": 100000000, "precio": 499}
            ]
        }
    
    try:
        rows = await pool.fetch("""
            SELECT id, nombre, requests_per_day, tokens_per_day, 
                   precio_mensual_cents / 100 as precio_usd
            FROM planes
            WHERE activo = true
            ORDER BY requests_per_day
        """)
        return {"plans": [dict(row) for row in rows]}
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        return {"plans": [], "error": str(e)}


@router.post("/check")
async def check_rate_limit(
    empresa_id: Optional[str] = None,
    estimated_tokens: int = 0
):
    """
    Verifica si una operación está dentro de los límites.
    Útil para pre-check antes de llamadas costosas.
    """
    if not empresa_id:
        empresa_id = await get_current_empresa_id()
    
    pool = await get_db_pool()
    if not pool:
        return {"allowed": True, "message": "Rate limiting bypassed"}
    
    try:
        from services.rate_limiter_service import RateLimiterService
        service = RateLimiterService(pool)
        result = await service.check_limits_only(empresa_id, estimated_tokens)
        return {
            "allowed": result.allowed,
            "requests_remaining": result.requests_remaining,
            "tokens_remaining": result.tokens_remaining,
            "message": result.message,
            "plan": result.plan
        }
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return {"allowed": True, "message": "Check bypassed", "error": str(e)}
