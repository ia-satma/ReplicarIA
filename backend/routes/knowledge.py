"""
Knowledge Management API Routes
Admin endpoints for managing agent training knowledge
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from routes.auth import get_admin_user
from services.agent_knowledge_service import agent_knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


class AddDocumentRequest(BaseModel):
    content: str
    title: str
    metadata: Optional[dict] = None


@router.get("/agents")
async def list_all_agents_knowledge(admin_user=Depends(get_admin_user)):
    """List all agents with their knowledge statistics"""
    try:
        stats = agent_knowledge_service.get_all_agents_stats()
        return {
            "success": True,
            "agents": stats
        }
    except Exception as e:
        logger.error(f"Error listing agents knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_id}")
async def get_agent_knowledge(agent_id: str, admin_user=Depends(get_admin_user)):
    """Get knowledge files and stats for a specific agent"""
    try:
        files = agent_knowledge_service.list_agent_knowledge_files(agent_id)
        stats = agent_knowledge_service.get_knowledge_stats(agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "stats": stats,
            "files": files
        }
    except Exception as e:
        logger.error(f"Error getting agent knowledge for {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/ingest")
async def ingest_agent_folder(agent_id: str, admin_user=Depends(get_admin_user)):
    """Trigger ingestion of all files in an agent's knowledge folder"""
    try:
        result = agent_knowledge_service.ingest_agent_folder(agent_id)
        
        if not result.get("success") and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "message": f"Ingested {result['chunks_ingested']} chunks from {result['files_processed']} files",
            "details": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting agent folder for {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/add")
async def add_document_to_agent(agent_id: str, request: AddDocumentRequest, admin_user=Depends(get_admin_user)):
    """Add a document to an agent's knowledge base"""
    try:
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if not request.title or not request.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        
        metadata = {
            "title": request.title,
            "source": "api_upload",
            **(request.metadata or {})
        }
        
        result = agent_knowledge_service.ingest_document(agent_id, request.content, metadata)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to add document"))
        
        return {
            "success": True,
            "message": f"Document '{request.title}' added to {agent_id} knowledge base",
            "chunk_id": result.get("chunk_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document to {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
