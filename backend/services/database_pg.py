"""
PostgreSQL Database Connection Manager.
Provides connection pooling for the new PostgreSQL-based services.
"""

import os
import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    
    if _pool is None:
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not configured")
        
        try:
            _pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise
    
    return _pool


async def close_pool():
    """Close the connection pool."""
    global _pool
    
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


@asynccontextmanager
async def get_connection():
    """Get a connection from the pool."""
    pool = await get_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


async def execute(query: str, *args):
    """Execute a query."""
    pool = await get_pool()
    return await pool.execute(query, *args)


async def fetch(query: str, *args):
    """Fetch multiple rows."""
    pool = await get_pool()
    return await pool.fetch(query, *args)


async def fetchrow(query: str, *args):
    """Fetch single row."""
    pool = await get_pool()
    return await pool.fetchrow(query, *args)


async def fetchval(query: str, *args):
    """Fetch single value."""
    pool = await get_pool()
    return await pool.fetchval(query, *args)


async def check_connection() -> bool:
    """Check if database connection is working."""
    try:
        pool = await get_pool()
        result = await pool.fetchval("SELECT 1")
        return result == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def get_project_service():
    """Get configured ProjectService instance."""
    from services.project_service import ProjectService
    pool = await get_pool()
    return ProjectService(pool)


async def get_deliberation_service():
    """Get configured DeliberationPGService instance."""
    from services.deliberation_pg_service import DeliberationPGService
    pool = await get_pool()
    return DeliberationPGService(pool)
