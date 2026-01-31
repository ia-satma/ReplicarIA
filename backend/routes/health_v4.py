from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_repository import RagRepository
from services.sql_engine_service import refresh_catalog, list_tables
from services.knowledge_graph_service import get_stats as kg_stats
from services.query_router import get_route_explanation
import os
import asyncpg
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health V4"])

DATABASE_URL = os.environ.get('DATABASE_URL', '')
RESET_SECRET = os.environ.get('RESET_SECRET_KEY', 'satma-reset-2024-confirmado')


def get_clean_db_url() -> str:
    url = DATABASE_URL
    if not url:
        return ''
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)
    return url


class ResetRequest(BaseModel):
    secret_key: str


@router.post('/reset-demo')
async def reset_demo_data(request: ResetRequest):
    """Reset all demo data. Requires secret_key."""
    if request.secret_key != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    db_url = get_clean_db_url()
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        conn = await asyncpg.connect(db_url, ssl='require')
        logger.warning("⚠️ RESET DEMO DATA started")

        results = {"cleaned": [], "errors": []}

        tables = [
            'clientes_historial', 'clientes_interacciones', 'clientes_contexto',
            'clientes_documentos', 'proveedores_scoring', 'df_proveedores',
            'df_documents', 'df_metadata', 'kb_chunk_agente', 'kb_chunks',
            'kb_documentos', 'kb_metricas', 'projects', 'project_documents',
            'project_notes', 'clientes', 'proveedores', 'auth_otp_codes',
            'auth_rate_limits'
        ]

        for table in tables:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", table
                )
                if exists:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    await conn.execute(f'DELETE FROM {table}')
                    results["cleaned"].append({"table": table, "deleted": count})
            except Exception as e:
                results["errors"].append({"table": table, "error": str(e)[:50]})

        # Clean non-admin users
        try:
            await conn.execute('''
                DELETE FROM auth_users
                WHERE email NOT IN ('ia@satma.mx', 'admin@revisar-ia.com')
                AND role NOT IN ('super_admin', 'admin')
            ''')
            results["cleaned"].append({"table": "auth_users (non-admin)", "deleted": "done"})
        except Exception as e:
            results["errors"].append({"table": "auth_users", "error": str(e)[:50]})

        await conn.close()
        logger.warning("✅ RESET DEMO DATA completed")

        return {"success": True, "results": results, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/rag_count/{agent_id}')
def rag_count(agent_id: str):
    try:
        rag = RagRepository()
        count = rag.count(agent_id)
        return {"success": True, "agent": agent_id, "count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get('/sql_refresh')
def sql_refresh():
    try:
        result = refresh_catalog()
        tables = list_tables()
        return {"success": True, "refreshed": result, "tables": tables}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get('/kg_stats')
def kg_statistics():
    try:
        stats = kg_stats()
        return {"success": True, "kg": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post('/router_test')
def test_router(query: str):
    try:
        explanation = get_route_explanation(query)
        return {"success": True, "routing": explanation}
    except Exception as e:
        return {"success": False, "error": str(e)}