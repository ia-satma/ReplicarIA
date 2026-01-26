"""
Servicio de Rate Limiting y Usage Tracking.
Protege la API de uso excesivo y trackea consumo para facturación.
"""

import asyncpg
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UsageType(str, Enum):
    CHAT = "chat"
    RAG = "rag"
    UPLOAD = "upload"
    EMBEDDING = "embedding"


@dataclass
class UsageCheckResult:
    allowed: bool
    requests_remaining: int
    tokens_remaining: int
    message: str
    plan: str = "free"
    
    def to_headers(self) -> Dict[str, str]:
        """Headers para incluir en la respuesta HTTP."""
        return {
            "X-RateLimit-Remaining-Requests": str(self.requests_remaining),
            "X-RateLimit-Remaining-Tokens": str(self.tokens_remaining),
            "X-RateLimit-Plan": self.plan,
        }


class RateLimiterService:
    """Rate limiting y tracking de uso."""
    
    PRECIO_INPUT_PER_1M = 300
    PRECIO_OUTPUT_PER_1M = 1500
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def check_and_increment(
        self,
        empresa_id: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        usage_type: UsageType = UsageType.CHAT
    ) -> UsageCheckResult:
        """
        Verifica límites e incrementa uso en una sola operación.
        Usa la función de PostgreSQL para atomicidad.
        """
        try:
            row = await self.db.fetchrow("""
                SELECT * FROM increment_usage($1::uuid, 1, $2, $3, $4)
            """, empresa_id, tokens_in, tokens_out, usage_type.value)
            
            plan = await self.db.fetchval("""
                SELECT plan_id FROM empresas WHERE id = $1::uuid
            """, empresa_id)
            
            return UsageCheckResult(
                allowed=row["allowed"] if row else True,
                requests_remaining=row["requests_remaining"] or 0 if row else 50,
                tokens_remaining=row["tokens_remaining"] or 0 if row else 100000,
                message=row["message"] if row else "OK",
                plan=plan or "free"
            )
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}, allowing request")
            return UsageCheckResult(
                allowed=True,
                requests_remaining=50,
                tokens_remaining=100000,
                message="Rate limit check bypassed",
                plan="free"
            )
    
    async def check_limits_only(
        self,
        empresa_id: str,
        estimated_tokens: int = 0
    ) -> UsageCheckResult:
        """
        Solo verifica límites sin incrementar (para pre-check).
        """
        try:
            row = await self.db.fetchrow("""
                SELECT 
                    e.plan_id,
                    e.uso_suspendido,
                    COALESCE(p.requests_per_day, 50) as requests_per_day,
                    COALESCE(p.tokens_per_day, 100000) as tokens_per_day,
                    COALESCE(u.requests_count, 0) as requests_hoy,
                    COALESCE(u.tokens_input + u.tokens_output, 0) as tokens_hoy
                FROM empresas e
                LEFT JOIN planes p ON p.id = e.plan_id
                LEFT JOIN usage_tracking u ON u.empresa_id = e.id AND u.fecha = CURRENT_DATE
                WHERE e.id = $1::uuid
            """, empresa_id)
            
            if not row:
                return UsageCheckResult(
                    allowed=True,
                    requests_remaining=50,
                    tokens_remaining=100000,
                    message="Empresa no encontrada, usando defaults"
                )
            
            if row["uso_suspendido"]:
                return UsageCheckResult(
                    allowed=False,
                    requests_remaining=0,
                    tokens_remaining=0,
                    message="Cuenta suspendida",
                    plan=row["plan_id"]
                )
            
            requests_remaining = row["requests_per_day"] - row["requests_hoy"]
            tokens_remaining = row["tokens_per_day"] - row["tokens_hoy"]
            
            allowed = requests_remaining > 0 and tokens_remaining >= estimated_tokens
            
            return UsageCheckResult(
                allowed=allowed,
                requests_remaining=max(0, requests_remaining),
                tokens_remaining=max(0, tokens_remaining),
                message="OK" if allowed else "Límite alcanzado",
                plan=row["plan_id"] or "free"
            )
        except Exception as e:
            logger.warning(f"Rate limit pre-check failed: {e}")
            return UsageCheckResult(
                allowed=True,
                requests_remaining=50,
                tokens_remaining=100000,
                message="Check bypassed"
            )
    
    async def update_tokens_used(
        self,
        empresa_id: str,
        tokens_in: int,
        tokens_out: int,
        usage_type: UsageType = UsageType.CHAT
    ):
        """
        Actualiza tokens usados después de una llamada a la API.
        Llamar esto DESPUÉS de que se complete la request.
        """
        try:
            costo = self._calculate_cost(tokens_in, tokens_out)
            
            await self.db.execute("""
                INSERT INTO usage_tracking (empresa_id, fecha, tokens_input, tokens_output, costo_estimado_cents,
                    chat_requests, rag_queries, document_uploads)
                VALUES ($1::uuid, CURRENT_DATE, $2, $3, $4,
                    CASE WHEN $5 = 'chat' THEN 1 ELSE 0 END,
                    CASE WHEN $5 = 'rag' THEN 1 ELSE 0 END,
                    CASE WHEN $5 = 'upload' THEN 1 ELSE 0 END)
                ON CONFLICT (empresa_id, fecha) DO UPDATE SET
                    tokens_input = usage_tracking.tokens_input + $2,
                    tokens_output = usage_tracking.tokens_output + $3,
                    costo_estimado_cents = usage_tracking.costo_estimado_cents + $4,
                    updated_at = NOW()
            """, empresa_id, tokens_in, tokens_out, costo, usage_type.value)
        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")
    
    async def log_request(
        self,
        empresa_id: str,
        endpoint: str,
        method: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: int = 0,
        status_code: int = 200,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Registra un request para auditoría."""
        try:
            await self.db.execute("""
                INSERT INTO request_logs (
                    empresa_id, user_id, endpoint, method,
                    tokens_in, tokens_out, latency_ms,
                    status_code, error_message, ip_address, user_agent
                ) VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                empresa_id,
                user_id,
                endpoint,
                method,
                tokens_in,
                tokens_out,
                latency_ms,
                status_code,
                error_message,
                ip_address,
                user_agent
            )
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def get_usage_stats(self, empresa_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de uso para el dashboard."""
        try:
            row = await self.db.fetchrow("""
                SELECT * FROM v_usage_dashboard WHERE empresa_id = $1::uuid
            """, empresa_id)
            
            if not row:
                return {
                    "plan": "free",
                    "requests_hoy": 0,
                    "tokens_hoy": 0,
                    "limite_requests": 50,
                    "limite_tokens": 100000,
                    "pct_requests": 0,
                    "pct_tokens": 0
                }
            
            return dict(row)
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e)}
    
    async def get_monthly_usage(self, empresa_id: str) -> list:
        """Obtiene uso mensual para reportes."""
        try:
            rows = await self.db.fetch("""
                SELECT * FROM v_usage_monthly 
                WHERE empresa_id = $1::uuid 
                ORDER BY mes DESC 
                LIMIT 12
            """, empresa_id)
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get monthly usage: {e}")
            return []
    
    def _calculate_cost(self, tokens_in: int, tokens_out: int) -> int:
        """Calcula costo en centavos USD."""
        cost_in = (tokens_in / 1_000_000) * self.PRECIO_INPUT_PER_1M
        cost_out = (tokens_out / 1_000_000) * self.PRECIO_OUTPUT_PER_1M
        return int(cost_in + cost_out)


async def get_rate_limiter() -> RateLimiterService:
    """Factory function para obtener RateLimiterService."""
    from services.database_pg import get_pool
    pool = await get_pool()
    return RateLimiterService(pool)
