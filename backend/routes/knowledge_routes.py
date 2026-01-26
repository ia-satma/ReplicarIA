"""
Knowledge Repository API Routes
Corporate knowledge management with file explorer functionality
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from pydantic import BaseModel
import os
import logging
from jose import jwt, exceptions as jose_exceptions

from services.knowledge_service import knowledge_service
from services.classification_service import classification_service, chunking_service, rag_query_service
from services.vector_search_service import vector_search_service
from services.auth_service import get_secret_key, verify_token as auth_verify_token, security

router = APIRouter(prefix="/knowledge", tags=["Knowledge Repository"])
logger = logging.getLogger(__name__)

# Usar servicio centralizado de autenticación
SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"


class CreateFolderRequest(BaseModel):
    path: str = "/"
    name: str


class BrowseResponse(BaseModel):
    path: str
    folders: List[dict]
    documents: List[dict]


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    token = credentials.credentials
    payload = verify_token(token)
    return payload


def get_user_empresa_id(user: dict) -> str:
    """Extract empresa_id from user token, ensuring multi-tenant isolation."""
    empresa_id = user.get("empresa_id") or user.get("company_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="No tiene empresa asignada")
    return empresa_id


@router.get("/health", include_in_schema=True)
async def health_check():
    """Health check endpoint for Knowledge Repository - no auth required"""
    return {
        "status": "healthy",
        "service": "knowledge_repository", 
        "version": "1.0.0"
    }


@router.get("/public/health")
async def public_health_check():
    """Public health check endpoint - no auth required"""
    return {
        "status": "healthy",
        "service": "knowledge_repository",
        "version": "1.0.0"
    }


@router.get("/browse")
async def browse_folder(
    path: str = Query("/", description="Path to browse"),
    current_user: dict = Depends(get_current_user)
):
    """List folders and documents at a given path."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        result = await knowledge_service.browse(empresa_id, path)
        return {
            "success": True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error browsing path {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new folder at the given path."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        user_id = current_user.get("user_id")
        
        result = await knowledge_service.create_folder(
            empresa_id=empresa_id,
            path=request.path,
            name=request.name,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Folder '{request.name}' created",
            "folder": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form("/"),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file to the knowledge repository."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        user_id = current_user.get("user_id")
        
        content = await file.read()
        
        result = await knowledge_service.upload_file(
            empresa_id=empresa_id,
            path=path,
            filename=file.filename,
            content=content,
            mime_type=file.content_type,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded",
            "document": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document metadata by ID."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        doc = await knowledge_service.get_document(document_id, empresa_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return {
            "success": True,
            "document": doc
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a document file."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        doc = await knowledge_service.get_document(document_id, empresa_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        file_path = await knowledge_service.get_document_file_path(document_id, empresa_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en el sistema")
        
        return FileResponse(
            path=file_path,
            filename=doc['filename'],
            media_type=doc.get('mime_type', 'application/octet-stream')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of archive"),
    current_user: dict = Depends(get_current_user)
):
    """Delete or archive a document."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        user_id = current_user.get("user_id")
        
        success = await knowledge_service.delete_document(
            document_id=document_id,
            empresa_id=empresa_id,
            user_id=user_id,
            hard_delete=hard_delete
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        action = "eliminado permanentemente" if hard_delete else "archivado"
        return {
            "success": True,
            "message": f"Documento {action}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/documents/{document_id}/status")
async def update_document_status(
    document_id: str,
    status: str = Query(..., description="New status: uploaded, processing, ready, archived, indexed, error"),
    current_user: dict = Depends(get_current_user)
):
    """Update document processing status."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        success = await knowledge_service.update_document_status(document_id, status, empresa_id)
        if not success:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return {
            "success": True,
            "message": f"Status actualizado a '{status}'"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/init")
async def initialize_folder_structure(
    current_user: dict = Depends(get_current_user)
):
    """Initialize the predefined folder structure for the empresa."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        user_id = current_user.get("user_id")
        
        result = await knowledge_service.initialize_folder_structure(
            empresa_id=empresa_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": "Estructura de carpetas inicializada",
            **result
        }
    except Exception as e:
        logger.error(f"Error initializing folder structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_repository_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get repository statistics for the empresa."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        stats = await knowledge_service.get_stats(empresa_id)
        
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        logger.error(f"Error getting repository stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query for filenames", min_length=2),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search documents by filename."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        results = await knowledge_service.search(empresa_id, q, limit)
        
        return {
            "success": True,
            "query": q,
            "total": len(results),
            "documents": results
        }
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RAGQueryRequest(BaseModel):
    query: str
    limit: int = 5
    categoria_filter: Optional[str] = None


class HybridSearchRequest(BaseModel):
    query: str
    limit: int = 10
    categoria_filter: Optional[str] = None
    semantic_weight: float = 0.7


class IngestRequest(BaseModel):
    document_id: str


class ReindexRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    full_reindex: bool = False


@router.post("/query_rag")
async def query_rag(
    request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Query the knowledge base using RAG (Retrieval Augmented Generation)."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        results = await rag_query_service.query(
            empresa_id=empresa_id,
            query=request.query,
            limit=request.limit,
            categoria_filter=request.categoria_filter
        )
        
        return {
            "success": True,
            **results
        }
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid_search")
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Perform hybrid search combining semantic (vector) and keyword search.
    Uses Reciprocal Rank Fusion (RRF) to combine results for better accuracy.
    
    - semantic_weight: 0.7 (default) means 70% weight on semantic similarity
    - Falls back to keyword-only search if embeddings not available
    """
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        results = await vector_search_service.hybrid_search(
            empresa_id=empresa_id,
            query=request.query,
            limit=request.limit,
            categoria_filter=request.categoria_filter,
            semantic_weight=request.semantic_weight
        )
        
        return {
            "success": True,
            **results
        }
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic_search")
async def semantic_search(
    request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Perform pure semantic (vector) search using embeddings.
    Returns results ranked by cosine similarity.
    Falls back to keyword search if embeddings not available.
    """
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        results = await vector_search_service.semantic_search(
            empresa_id=empresa_id,
            query=request.query,
            limit=request.limit,
            categoria_filter=request.categoria_filter
        )
        
        return {
            "success": True,
            "query": request.query,
            "total_results": len(results),
            "search_type": "semantic",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector_status")
async def check_vector_status(current_user: dict = Depends(get_current_user)):
    """Check if pgvector is available and embeddings are configured."""
    try:
        pgvector_available = await vector_search_service.check_pgvector_available()
        
        from services.embedding_service import embedding_service
        embeddings_configured = embedding_service._get_client() is not None
        
        return {
            "success": True,
            "pgvector_available": pgvector_available,
            "embeddings_configured": embeddings_configured,
            "embedding_model": embedding_service.model if embeddings_configured else None,
            "embedding_dimensions": embedding_service.dimensions if embeddings_configured else None,
            "search_mode": "hybrid" if (pgvector_available and embeddings_configured) else "keyword_only"
        }
    except Exception as e:
        logger.error(f"Error checking vector status: {e}")
        return {
            "success": False,
            "error": str(e),
            "search_mode": "keyword_only"
        }


@router.post("/ingest")
async def ingest_document(
    request: IngestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger document ingestion (extraction, classification, chunking)."""
    try:
        from services.ingestion_service import IngestionService
        
        empresa_id = get_user_empresa_id(current_user)
        
        doc = await knowledge_service.get_document(request.document_id, empresa_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        file_path = await knowledge_service.get_document_file_path(request.document_id, empresa_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        ingestion_service = IngestionService()
        result = await ingestion_service.process_document(
            document_id=request.document_id,
            empresa_id=empresa_id,
            file_path=file_path
        )
        
        if result.get("success"):
            extracted_text = await knowledge_service.get_document_text(request.document_id, empresa_id)
            
            if extracted_text:
                classification = await classification_service.classify_document(
                    document_id=request.document_id,
                    empresa_id=empresa_id,
                    text_content=extracted_text,
                    filename=doc.get("filename", "")
                )
                
                await chunking_service.chunk_document(
                    document_id=request.document_id,
                    empresa_id=empresa_id,
                    text=extracted_text
                )
                
                result["classification"] = classification
        
        return {
            "success": True,
            "message": "Documento procesado",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_documents(
    request: ReindexRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reindex documents (re-extract, re-classify, re-chunk)."""
    try:
        from services.ingestion_service import IngestionService
        
        empresa_id = get_user_empresa_id(current_user)
        
        if request.full_reindex:
            documents = await knowledge_service.get_all_documents(empresa_id)
            document_ids = [d["id"] for d in documents]
        elif request.document_ids:
            document_ids = request.document_ids
        else:
            raise HTTPException(status_code=400, detail="Debe especificar document_ids o full_reindex=true")
        
        ingestion_service = IngestionService()
        results = []
        errors = []
        
        for doc_id in document_ids:
            try:
                file_path = await knowledge_service.get_document_file_path(doc_id, empresa_id)
                if file_path:
                    result = await ingestion_service.process_document(
                        document_id=doc_id,
                        empresa_id=empresa_id,
                        file_path=file_path
                    )
                    
                    if result.get("success"):
                        extracted_text = await knowledge_service.get_document_text(doc_id, empresa_id)
                        doc = await knowledge_service.get_document(doc_id, empresa_id)
                        
                        if extracted_text and doc:
                            await classification_service.classify_document(
                                document_id=doc_id,
                                empresa_id=empresa_id,
                                text_content=extracted_text,
                                filename=doc.get("filename", "")
                            )
                            
                            await chunking_service.chunk_document(
                                document_id=doc_id,
                                empresa_id=empresa_id,
                                text=extracted_text
                            )
                    
                    results.append({"document_id": doc_id, "status": "success"})
                else:
                    errors.append({"document_id": doc_id, "error": "Archivo no encontrado"})
            except Exception as e:
                errors.append({"document_id": doc_id, "error": str(e)})
        
        return {
            "success": True,
            "message": f"Reindexación completada: {len(results)} exitosos, {len(errors)} errores",
            "processed": results,
            "errors": errors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reindexing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """Get processing jobs for the empresa."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        jobs = await knowledge_service.get_jobs(empresa_id, status)
        
        return {
            "success": True,
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all chunks for a document."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        chunks = await knowledge_service.get_document_chunks(document_id, empresa_id)
        
        return {
            "success": True,
            "document_id": document_id,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        logger.error(f"Error getting document chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/text")
async def get_document_extracted_text(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the extracted text content of a document."""
    try:
        empresa_id = get_user_empresa_id(current_user)
        
        text = await knowledge_service.get_document_text(document_id, empresa_id)
        if text is None:
            raise HTTPException(status_code=404, detail="Texto no encontrado")
        
        return {
            "success": True,
            "document_id": document_id,
            "text": text
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document text: {e}")
        raise HTTPException(status_code=500, detail=str(e))
