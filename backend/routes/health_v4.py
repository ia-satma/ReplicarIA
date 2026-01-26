from fastapi import APIRouter
from services.rag_repository import RagRepository
from services.sql_engine_service import refresh_catalog, list_tables
from services.knowledge_graph_service import get_stats as kg_stats
from services.query_router import get_route_explanation

router = APIRouter(prefix="/health", tags=["Health V4"])

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