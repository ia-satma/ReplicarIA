from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pcloud", tags=["pCloud"])

from services.pcloud_service import pcloud_service

@router.get("/test")
async def test_pcloud_connection():
    """Test pCloud connection with current credentials"""
    result = pcloud_service.login()
    return result

@router.post("/initialize")
async def initialize_pcloud_structure():
    """Initialize REVISAR.ia folder structure - creates all required subfolders"""
    result = pcloud_service.initialize_folder_structure()
    return result

@router.get("/folders")
async def list_agent_folders():
    """List all agent folders discovered in REVISAR.ia"""
    result = pcloud_service.find_agent_folders()
    return result

@router.get("/documents/{agent_id}")
async def list_agent_documents(agent_id: str):
    result = pcloud_service.list_agent_documents(agent_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@router.post("/sync/{agent_id}")
async def sync_agent_to_rag(agent_id: str):
    try:
        from services.rag_service import rag_service
        result = pcloud_service.sync_agent_documents_to_rag(agent_id, rag_service)
        return result
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all")
async def sync_all_agents_to_rag():
    try:
        from services.rag_service import rag_service
        
        agents = ["A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL", "A5_FINANZAS", "A6_PROVEEDOR", "A7_DEFENSA", "KNOWLEDGE_BASE"]
        results = {}
        
        for agent_id in agents:
            result = pcloud_service.sync_agent_documents_to_rag(agent_id, rag_service)
            results[agent_id] = {
                "success": result.get("success"),
                "synced_count": result.get("synced_count", 0),
                "error_count": result.get("error_count", 0)
            }
            
        total_synced = sum(r.get("synced_count", 0) for r in results.values())
        
        return {
            "success": True,
            "total_synced": total_synced,
            "by_agent": results
        }
    except Exception as e:
        logger.error(f"Sync all error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{file_id}/link")
async def get_file_download_link(file_id: int):
    if not pcloud_service.auth_token:
        pcloud_service.login()
    result = pcloud_service.get_file_link(file_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
