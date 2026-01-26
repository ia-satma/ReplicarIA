from fastapi import APIRouter
from services.knowledge_graph_service import upsert_triple, save, get_stats
from services.rag_repository import RagRepository
import re
import logging

router = APIRouter(prefix="/kg", tags=["Knowledge Graph"])
logger = logging.getLogger(__name__)

# Patterns para extracción de entidades legales
ART_PATTERN = re.compile(r'Art(?:ículo|\.)?\s*(\d+(?:-[A-Z])?)\s*(LISR|CFF|DOF)', re.I)
LEY_PATTERN = re.compile(r'\b(LISR|CFF|DOF|Ley del ISR|Código Fiscal)\b', re.I)

@router.get('/populate/{agent_id}')
async def populate_kg_from_rag(agent_id: str):
    """Extrae entidades y relaciones desde chunks RAG del agente"""
    
    logger.info(f"[KG POPULATE] Iniciando para {agent_id}")
    
    # Usar kg_enhanced en lugar de knowledge_graph_service
    try:
        from services.kg_enhanced import KG
        result = KG.populate_from_agent(agent_id, limit=2000)
        stats = KG.get_stats() if hasattr(KG, 'get_stats') else {"nodes": len(KG.G.nodes()), "edges": len(KG.G.edges())}
        
        return {
            "success": True,
            "agent_id": agent_id,
            "triples_added": result.get('edges', 0),
            "kg_stats": stats
        }
    except Exception as e:
        logger.error(f"Error populating KG: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
