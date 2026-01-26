"""
Métricas de optimización de costos LLM
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])

_usage_stats = {
    "query_router": {
        "total_queries": 0,
        "simple_tier": {"count": 0, "total_cost": 0.0},
        "medium_tier": {"count": 0, "total_cost": 0.0},
        "complex_tier": {"count": 0, "total_cost": 0.0}
    },
    "embedding_cache": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0
    },
    "rag_parallel": {
        "total_preloads": 0,
        "avg_time_saved_seconds": 6.0
    }
}

@router.get("/llm-costs")
async def get_llm_costs() -> Dict[str, Any]:
    """Retorna métricas de costos y optimizaciones LLM"""
    router_stats = _usage_stats["query_router"]
    cache_stats = _usage_stats["embedding_cache"]
    
    total_queries = router_stats["total_queries"]
    total_cost = sum(
        tier["total_cost"] 
        for tier in [router_stats["simple_tier"], router_stats["medium_tier"], router_stats["complex_tier"]]
    )
    
    cost_without_optimization = total_queries * 0.035
    savings = max(0, cost_without_optimization - total_cost)
    savings_percent = (savings / cost_without_optimization * 100) if cost_without_optimization > 0 else 0
    
    cache_requests = cache_stats["total_requests"]
    cache_hit_rate = (cache_stats["cache_hits"] / cache_requests * 100) if cache_requests > 0 else 0
    
    return {
        "query_router": {
            "total_queries": total_queries,
            "cost_breakdown": {
                "simple": {
                    "queries": router_stats["simple_tier"]["count"],
                    "cost": round(router_stats["simple_tier"]["total_cost"], 4),
                    "model": "gpt-4o-mini"
                },
                "medium": {
                    "queries": router_stats["medium_tier"]["count"],
                    "cost": round(router_stats["medium_tier"]["total_cost"], 4),
                    "model": "gpt-4o"
                },
                "complex": {
                    "queries": router_stats["complex_tier"]["count"],
                    "cost": round(router_stats["complex_tier"]["total_cost"], 4),
                    "model": "gpt-4o"
                }
            },
            "total_cost": round(total_cost, 4),
            "estimated_savings": round(savings, 4),
            "savings_percent": round(savings_percent, 1)
        },
        "embedding_cache": {
            "total_requests": cache_requests,
            "cache_hits": cache_stats["cache_hits"],
            "cache_misses": cache_stats["cache_misses"],
            "hit_rate_percent": round(cache_hit_rate, 1),
            "estimated_cost_saved": round(cache_stats["cache_hits"] * 0.0001, 4)
        },
        "rag_parallel": {
            "total_preloads": _usage_stats["rag_parallel"]["total_preloads"],
            "avg_time_saved_seconds": _usage_stats["rag_parallel"]["avg_time_saved_seconds"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/track-usage")
async def track_usage(event: Dict[str, Any]) -> Dict[str, str]:
    """Endpoint para que los servicios reporten uso"""
    event_type = event.get("type")
    
    if event_type == "query_router":
        tier = event.get("tier", "medium")
        cost = event.get("cost", 0.0)
        _usage_stats["query_router"]["total_queries"] += 1
        _usage_stats["query_router"][f"{tier}_tier"]["count"] += 1
        _usage_stats["query_router"][f"{tier}_tier"]["total_cost"] += cost
        
    elif event_type == "embedding_cache":
        _usage_stats["embedding_cache"]["total_requests"] += 1
        if event.get("hit"):
            _usage_stats["embedding_cache"]["cache_hits"] += 1
        else:
            _usage_stats["embedding_cache"]["cache_misses"] += 1
            
    elif event_type == "rag_parallel":
        _usage_stats["rag_parallel"]["total_preloads"] += 1
    
    return {"status": "tracked"}

def get_usage_stats():
    """Función helper para acceder a stats desde otros módulos"""
    return _usage_stats

def track_query_router(tier: str, cost: float):
    """Helper para registrar uso del query router"""
    _usage_stats["query_router"]["total_queries"] += 1
    _usage_stats["query_router"][f"{tier}_tier"]["count"] += 1
    _usage_stats["query_router"][f"{tier}_tier"]["total_cost"] += cost

def track_embedding_cache(hit: bool):
    """Helper para registrar uso del cache de embeddings"""
    _usage_stats["embedding_cache"]["total_requests"] += 1
    if hit:
        _usage_stats["embedding_cache"]["cache_hits"] += 1
    else:
        _usage_stats["embedding_cache"]["cache_misses"] += 1

def track_rag_preload():
    """Helper para registrar uso de precarga RAG"""
    _usage_stats["rag_parallel"]["total_preloads"] += 1
