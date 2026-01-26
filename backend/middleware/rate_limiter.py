"""
Rate Limiter Middleware
Implements per-empresa rate limiting based on plan tiers
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncpg
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded."""
    def __init__(self, message: str, reset_at: datetime = None, plan: str = None):
        super().__init__(message)
        self.message = message
        self.reset_at = reset_at or datetime.utcnow().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        self.plan = plan


async def get_db_connection():
    """Get a database connection."""
    if not DATABASE_URL:
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


class RateLimiter:
    """Rate limiter with per-plan limits and usage tracking."""
    
    def __init__(self):
        self.limits = {
            "free": {"requests_per_day": 50, "tokens_per_day": 100_000},
            "starter": {"requests_per_day": 500, "tokens_per_day": 1_000_000},
            "pro": {"requests_per_day": 5000, "tokens_per_day": 10_000_000},
            "enterprise": {"requests_per_day": 50000, "tokens_per_day": 100_000_000},
            "demo": {"requests_per_day": 100, "tokens_per_day": 200_000},
        }
        
        self.default_plan = "starter"
    
    async def ensure_table_exists(self) -> bool:
        """Ensure usage_tracking table exists."""
        conn = await get_db_connection()
        if not conn:
            return False
        
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID NOT NULL,
                    fecha DATE NOT NULL,
                    requests_today INTEGER DEFAULT 0,
                    tokens_today INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(empresa_id, fecha)
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_empresa_fecha 
                ON usage_tracking(empresa_id, fecha)
            """)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create usage_tracking table: {e}")
            return False
        finally:
            await conn.close()
    
    async def check_and_increment(
        self,
        empresa_id: str,
        tokens_used: int = 0
    ) -> Dict[str, Any]:
        """
        Check rate limits and increment usage.
        Raises HTTPException if limit exceeded.
        """
        if not empresa_id:
            return {"requests_remaining": 999, "tokens_remaining": 999999, "plan": "unknown"}
        
        conn = await get_db_connection()
        if not conn:
            return {"requests_remaining": 999, "tokens_remaining": 999999, "plan": "unknown"}
        
        try:
            today = datetime.utcnow().date()
            
            row = await conn.fetchrow("""
                SELECT 
                    e.plan,
                    COALESCE(u.requests_today, 0) as requests_today,
                    COALESCE(u.tokens_today, 0) as tokens_today
                FROM empresas e
                LEFT JOIN usage_tracking u ON u.empresa_id = e.id AND u.fecha = $2
                WHERE e.id = $1
            """, empresa_id, today)
            
            if not row:
                plan = self.default_plan
                current_requests = 0
                current_tokens = 0
            else:
                plan = row["plan"] or self.default_plan
                current_requests = row["requests_today"]
                current_tokens = row["tokens_today"]
            
            limits = self.limits.get(plan, self.limits[self.default_plan])
            
            if current_requests >= limits["requests_per_day"]:
                reset_time = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) 
                              + timedelta(days=1))
                raise RateLimitExceeded(
                    message=f"Límite diario de {limits['requests_per_day']} requests alcanzado",
                    reset_at=reset_time,
                    plan=plan
                )
            
            if current_tokens >= limits["tokens_per_day"]:
                reset_time = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) 
                              + timedelta(days=1))
                raise RateLimitExceeded(
                    message=f"Límite diario de {limits['tokens_per_day']:,} tokens alcanzado",
                    reset_at=reset_time,
                    plan=plan
                )
            
            await conn.execute("""
                INSERT INTO usage_tracking (empresa_id, fecha, requests_today, tokens_today, updated_at)
                VALUES ($1, $2, 1, $3, NOW())
                ON CONFLICT (empresa_id, fecha) DO UPDATE
                SET requests_today = usage_tracking.requests_today + 1,
                    tokens_today = usage_tracking.tokens_today + $3,
                    updated_at = NOW()
            """, empresa_id, today, tokens_used)
            
            return {
                "requests_remaining": limits["requests_per_day"] - current_requests - 1,
                "tokens_remaining": limits["tokens_per_day"] - current_tokens - tokens_used,
                "plan": plan,
                "requests_used": current_requests + 1,
                "tokens_used": current_tokens + tokens_used
            }
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {"requests_remaining": 999, "tokens_remaining": 999999, "plan": "unknown"}
        finally:
            await conn.close()
    
    async def get_usage_stats(
        self,
        empresa_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics for an empresa."""
        conn = await get_db_connection()
        if not conn:
            return {"error": "Database unavailable"}
        
        try:
            rows = await conn.fetch("""
                SELECT 
                    fecha,
                    requests_today,
                    tokens_today
                FROM usage_tracking
                WHERE empresa_id = $1
                AND fecha >= CURRENT_DATE - $2::integer
                ORDER BY fecha DESC
            """, empresa_id, days)
            
            total_requests = sum(r["requests_today"] for r in rows)
            total_tokens = sum(r["tokens_today"] for r in rows)
            
            plan_row = await conn.fetchrow(
                "SELECT plan FROM empresas WHERE id = $1", empresa_id
            )
            plan = plan_row["plan"] if plan_row else self.default_plan
            limits = self.limits.get(plan, self.limits[self.default_plan])
            
            estimated_cost_usd = round(total_tokens / 1_000_000 * 15, 2)
            
            return {
                "empresa_id": empresa_id,
                "plan": plan,
                "period_days": days,
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost_usd,
                "daily_limits": limits,
                "daily_usage": [
                    {
                        "date": str(r["fecha"]),
                        "requests": r["requests_today"],
                        "tokens": r["tokens_today"]
                    }
                    for r in rows
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e)}
        finally:
            await conn.close()


rate_limiter = RateLimiter()
