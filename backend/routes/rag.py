"""
RAG API Routes for Revisar.ia Multi-Agent System
Handles knowledge base operations for agent deliberations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from services.rag_service import rag_service, AGENT_COLLECTIONS, AGENT_PCLOUD_LINKS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])


class AddDocumentRequest(BaseModel):
    agent_id: str
    document_id: str
    content: str
    metadata: Optional[Dict] = None


class AddDocumentsBatchRequest(BaseModel):
    agent_id: str
    documents: List[Dict]


class QueryRequest(BaseModel):
    agent_id: str
    query_text: str
    n_results: int = 5
    where_filter: Optional[Dict] = None


class QueryAllRequest(BaseModel):
    query_text: str
    n_results_per_agent: int = 3


class ContextRequest(BaseModel):
    agent_id: str
    project_description: str
    n_results: int = 5


@router.get("/status")
async def get_rag_status():
    """Get RAG service status and statistics"""
    return rag_service.get_all_stats()


@router.get("/agents")
async def list_agent_collections():
    """List all agent collections and their pCloud links"""
    agents = []
    for agent_id, collection_name in AGENT_COLLECTIONS.items():
        stats = rag_service.get_collection_stats(agent_id)
        agents.append({
            "agent_id": agent_id,
            "collection_name": collection_name,
            "document_count": stats.get("document_count", 0),
            "pcloud_link": AGENT_PCLOUD_LINKS.get(agent_id)
        })
    return {"agents": agents}


@router.get("/stats/{agent_id}")
async def get_agent_stats(agent_id: str):
    """Get statistics for a specific agent's knowledge base"""
    if agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    result = rag_service.get_collection_stats(agent_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/documents/add")
async def add_document(request: AddDocumentRequest):
    """Add a document to an agent's knowledge base"""
    if request.agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    result = rag_service.add_document(
        agent_id=request.agent_id,
        document_id=request.document_id,
        content=request.content,
        metadata=request.metadata
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/documents/add-batch")
async def add_documents_batch(request: AddDocumentsBatchRequest):
    """Add multiple documents to an agent's knowledge base"""
    if request.agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    result = rag_service.add_documents_batch(
        agent_id=request.agent_id,
        documents=request.documents
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/query")
async def query_knowledge_base(request: QueryRequest):
    """Query an agent's knowledge base"""
    if request.agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    result = rag_service.query(
        agent_id=request.agent_id,
        query_text=request.query_text,
        n_results=request.n_results,
        where_filter=request.where_filter
    )
    
    return result


@router.post("/query-all")
async def query_all_agents(request: QueryAllRequest):
    """Query all agents' knowledge bases"""
    result = rag_service.query_all_agents(
        query_text=request.query_text,
        n_results_per_agent=request.n_results_per_agent
    )
    
    return result


@router.post("/context")
async def get_deliberation_context(request: ContextRequest):
    """Get relevant context for agent deliberation on a project"""
    if request.agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    context = rag_service.get_context_for_deliberation(
        project_description=request.project_description,
        agent_id=request.agent_id,
        n_results=request.n_results
    )
    
    return {
        "agent_id": request.agent_id,
        "context": context,
        "has_context": bool(context)
    }


@router.delete("/documents/{agent_id}/{document_id}")
async def delete_document(agent_id: str, document_id: str):
    """Delete a document from an agent's knowledge base"""
    if agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    result = rag_service.delete_document(agent_id, document_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.delete("/clear/{agent_id}")
async def clear_agent_collection(agent_id: str):
    """Clear all documents from an agent's knowledge base"""
    if agent_id not in AGENT_COLLECTIONS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    result = rag_service.clear_collection(agent_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result
