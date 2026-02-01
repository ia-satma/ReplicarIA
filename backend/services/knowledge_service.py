"""
Knowledge Repository Service
Corporate knowledge management with file explorer functionality
"""
import os
import uuid
import hashlib
import logging
import asyncio
import aiofiles
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncpg

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection is unavailable"""
    pass

DATABASE_URL = os.environ.get('DATABASE_URL', '')
KNOWLEDGE_UPLOADS_DIR = "backend/uploads/knowledge"


def safe_uuid(id_string: str) -> uuid.UUID:
    """
    Convert an ID string to UUID safely.
    If the string is already a valid UUID, return it.
    Otherwise, generate a deterministic UUID from the string using UUID5.
    This allows compatibility with legacy IDs like 'satma-001'.
    """
    if not id_string:
        raise ValueError("ID string cannot be empty")

    try:
        # Try parsing as UUID directly
        return uuid.UUID(id_string)
    except (ValueError, AttributeError):
        # Generate deterministic UUID from string using namespace
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return uuid.uuid5(namespace, id_string)


async def get_db_connection():
    """Get asyncpg connection for database operations"""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured")
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


class KnowledgeService:
    """Service for managing knowledge repository operations."""
    
    def __init__(self):
        os.makedirs(KNOWLEDGE_UPLOADS_DIR, exist_ok=True)
    
    def _get_empresa_dir(self, empresa_id: str) -> str:
        """Get the upload directory for a specific empresa."""
        empresa_dir = os.path.join(KNOWLEDGE_UPLOADS_DIR, f"empresa_{empresa_id}")
        os.makedirs(empresa_dir, exist_ok=True)
        return empresa_dir
    
    async def browse(self, empresa_id: Optional[str], path: str = "/") -> Dict[str, Any]:
        """List folders and documents at a given path.

        Args:
            empresa_id: The empresa to filter by. None = superadmin sees all.
            path: The path to browse.
        """
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")

        try:
            normalized_path = path.rstrip('/') or '/'

            # For superadmins (empresa_id=None), show all data
            if empresa_id is None:
                folders = await conn.fetch(
                    """
                    SELECT id, path, name, parent_path, created_at, empresa_id
                    FROM knowledge_folders
                    WHERE parent_path = $1
                    ORDER BY name
                    """,
                    normalized_path
                )

                documents = await conn.fetch(
                    """
                    SELECT id, path, filename, mime_type, size_bytes, status, created_at, updated_at, metadata, empresa_id
                    FROM knowledge_documents
                    WHERE path = $1 AND status != 'archived'
                    ORDER BY filename
                    """,
                    normalized_path
                )
            else:
                folders = await conn.fetch(
                    """
                    SELECT id, path, name, parent_path, created_at
                    FROM knowledge_folders
                    WHERE empresa_id = $1 AND parent_path = $2
                    ORDER BY name
                    """,
                    safe_uuid(empresa_id),
                    normalized_path
                )

                documents = await conn.fetch(
                    """
                    SELECT id, path, filename, mime_type, size_bytes, status, created_at, updated_at, metadata
                    FROM knowledge_documents
                    WHERE empresa_id = $1 AND path = $2 AND status != 'archived'
                    ORDER BY filename
                    """,
                    safe_uuid(empresa_id),
                    normalized_path
                )
            
            return {
                "path": normalized_path,
                "folders": [
                    {
                        "id": str(f['id']),
                        "name": f['name'],
                        "path": f['path'],
                        "created_at": f['created_at'].isoformat() if f['created_at'] else None
                    }
                    for f in folders
                ],
                "documents": [
                    {
                        "id": str(d['id']),
                        "filename": d['filename'],
                        "mime_type": d['mime_type'],
                        "size_bytes": d['size_bytes'],
                        "status": d['status'],
                        "created_at": d['created_at'].isoformat() if d['created_at'] else None,
                        "updated_at": d['updated_at'].isoformat() if d['updated_at'] else None,
                        "metadata": d['metadata'] if isinstance(d['metadata'], dict) else {}
                    }
                    for d in documents
                ]
            }
        finally:
            await conn.close()
    
    async def create_folder(self, empresa_id: str, path: str, name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder at the given path."""
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            parent_path = path.rstrip('/') or '/'
            folder_path = f"{parent_path}/{name}".replace('//', '/')
            
            existing = await conn.fetchrow(
                """
                SELECT id FROM knowledge_folders
                WHERE empresa_id = $1 AND path = $2
                """,
                safe_uuid(empresa_id),
                folder_path
            )
            
            if existing:
                raise ValueError(f"Folder already exists: {folder_path}")
            
            folder_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO knowledge_folders (id, empresa_id, path, name, parent_path, created_by, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                folder_id,
                safe_uuid(empresa_id),
                folder_path,
                name,
                parent_path,
                uuid.UUID(user_id) if user_id else None
            )
            
            empresa_dir = self._get_empresa_dir(empresa_id)
            fs_path = os.path.join(empresa_dir, folder_path.lstrip('/'))
            os.makedirs(fs_path, exist_ok=True)
            
            await self.log_audit(str(folder_id), "folder_created", user_id, {"path": folder_path, "name": name})
            
            return {
                "id": str(folder_id),
                "path": folder_path,
                "name": name,
                "parent_path": parent_path
            }
        finally:
            await conn.close()
    
    async def upload_file(
        self, 
        empresa_id: str, 
        path: str, 
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to the knowledge repository."""
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            normalized_path = path.rstrip('/') or '/'
            
            checksum = hashlib.sha256(content).hexdigest()
            size_bytes = len(content)
            
            doc_id = uuid.uuid4()
            
            empresa_dir = self._get_empresa_dir(empresa_id)
            fs_dir = os.path.join(empresa_dir, normalized_path.lstrip('/'))
            os.makedirs(fs_dir, exist_ok=True)
            
            safe_filename = f"{doc_id}_{filename}"
            fs_path = os.path.join(fs_dir, safe_filename)
            
            async with aiofiles.open(fs_path, 'wb') as f:
                await f.write(content)
            
            await conn.execute(
                """
                INSERT INTO knowledge_documents 
                (id, empresa_id, path, filename, mime_type, size_bytes, checksum_sha256, status, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'uploaded', $8, NOW(), NOW())
                """,
                doc_id,
                safe_uuid(empresa_id),
                normalized_path,
                filename,
                mime_type,
                size_bytes,
                checksum,
                uuid.UUID(user_id) if user_id else None
            )
            
            await self.log_audit(str(doc_id), "document_uploaded", user_id, {
                "filename": filename,
                "path": normalized_path,
                "size_bytes": size_bytes
            })
            
            asyncio.create_task(
                self._trigger_ingestion(str(doc_id), empresa_id, fs_path)
            )
            
            return {
                "id": str(doc_id),
                "filename": filename,
                "path": normalized_path,
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "checksum_sha256": checksum,
                "status": "uploaded"
            }
        finally:
            await conn.close()
    
    async def _trigger_ingestion(self, document_id: str, empresa_id: str, file_path: str) -> None:
        """Trigger background ingestion processing for an uploaded document."""
        try:
            from services.ingestion_service import ingestion_service
            from services.classification_service import classification_service, chunking_service
            
            result = await ingestion_service.process_document(document_id, empresa_id, file_path)
            
            if result.get("success"):
                logger.info(f"Ingestion completed for document {document_id}: {result.get('word_count', 0)} words")
                
                extracted_text = await self.get_document_text(document_id, empresa_id)
                
                if extracted_text:
                    doc = await self.get_document(document_id, empresa_id)
                    filename = doc.get("filename", "") if doc else ""
                    
                    classification = await classification_service.classify_document(
                        document_id=document_id,
                        empresa_id=empresa_id,
                        text_content=extracted_text,
                        filename=filename
                    )
                    logger.info(f"Classification completed for document {document_id}: {classification.get('categoria', 'unknown')}")
                    
                    chunks = await chunking_service.chunk_document(
                        document_id=document_id,
                        empresa_id=empresa_id,
                        text=extracted_text
                    )
                    logger.info(f"Chunking completed for document {document_id}: {len(chunks)} chunks created")
            else:
                logger.warning(f"Ingestion failed for document {document_id}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error triggering ingestion for document {document_id}: {e}")
    
    async def get_document(self, document_id: str, empresa_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            if empresa_id:
                doc = await conn.fetchrow(
                    """
                    SELECT id, empresa_id, path, filename, mime_type, size_bytes, checksum_sha256, status, created_by, created_at, updated_at, metadata
                    FROM knowledge_documents
                    WHERE id = $1 AND empresa_id = $2
                    """,
                    uuid.UUID(document_id),
                    safe_uuid(empresa_id)
                )
            else:
                doc = await conn.fetchrow(
                    """
                    SELECT id, empresa_id, path, filename, mime_type, size_bytes, checksum_sha256, status, created_by, created_at, updated_at, metadata
                    FROM knowledge_documents
                    WHERE id = $1
                    """,
                    uuid.UUID(document_id)
                )
            
            if not doc:
                return None
            
            return {
                "id": str(doc['id']),
                "empresa_id": str(doc['empresa_id']),
                "path": doc['path'],
                "filename": doc['filename'],
                "mime_type": doc['mime_type'],
                "size_bytes": doc['size_bytes'],
                "checksum_sha256": doc['checksum_sha256'],
                "status": doc['status'],
                "created_by": str(doc['created_by']) if doc['created_by'] else None,
                "created_at": doc['created_at'].isoformat() if doc['created_at'] else None,
                "updated_at": doc['updated_at'].isoformat() if doc['updated_at'] else None,
                "metadata": dict(doc['metadata']) if doc['metadata'] else {}
            }
        finally:
            await conn.close()
    
    async def get_document_file_path(self, document_id: str, empresa_id: str) -> Optional[str]:
        """Get the filesystem path for a document."""
        doc = await self.get_document(document_id, empresa_id)
        if not doc:
            return None
        
        empresa_dir = self._get_empresa_dir(empresa_id)
        path = doc['path'].lstrip('/')
        safe_filename = f"{document_id}_{doc['filename']}"
        fs_path = os.path.join(empresa_dir, path, safe_filename)
        
        if os.path.exists(fs_path):
            return fs_path
        return None
    
    async def delete_document(self, document_id: str, empresa_id: str, user_id: Optional[str] = None, hard_delete: bool = False) -> bool:
        """Delete or archive a document."""
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            doc = await conn.fetchrow(
                """
                SELECT id, filename, path FROM knowledge_documents
                WHERE id = $1 AND empresa_id = $2
                """,
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
            
            if not doc:
                return False
            
            if hard_delete:
                fs_path = await self.get_document_file_path(document_id, empresa_id)
                if fs_path and os.path.exists(fs_path):
                    os.remove(fs_path)
                
                await conn.execute(
                    "DELETE FROM knowledge_documents WHERE id = $1",
                    uuid.UUID(document_id)
                )
                action = "document_deleted"
            else:
                await conn.execute(
                    "UPDATE knowledge_documents SET status = 'archived', updated_at = NOW() WHERE id = $1",
                    uuid.UUID(document_id)
                )
                action = "document_archived"
            
            await self.log_audit(document_id, action, user_id, {
                "filename": doc['filename'],
                "path": doc['path']
            })
            
            return True
        finally:
            await conn.close()
    
    async def log_audit(self, document_id: Optional[str], action: str, actor_id: Optional[str], detail: Dict[str, Any] = None) -> None:
        """Log an audit event."""
        conn = await get_db_connection()
        if not conn:
            logger.warning("Cannot log audit - database unavailable")
            return
        
        try:
            import json
            await conn.execute(
                """
                INSERT INTO knowledge_audit (id, document_id, action, actor_id, timestamp, detail)
                VALUES ($1, $2, $3, $4, NOW(), $5)
                """,
                uuid.uuid4(),
                uuid.UUID(document_id) if document_id else None,
                action,
                uuid.UUID(actor_id) if actor_id else None,
                json.dumps(detail or {})
            )
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        finally:
            await conn.close()
    
    async def update_document_status(self, document_id: str, status: str, empresa_id: str) -> bool:
        """Update document processing status."""
        valid_statuses = ['uploaded', 'processing', 'ready', 'archived', 'indexed', 'error']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            result = await conn.execute(
                """
                UPDATE knowledge_documents 
                SET status = $1, updated_at = NOW()
                WHERE id = $2 AND empresa_id = $3
                """,
                status,
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
            return result == "UPDATE 1"
        finally:
            await conn.close()
    
    async def initialize_folder_structure(self, empresa_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Initialize the predefined folder hierarchy for a new empresa."""
        folder_structure = [
            "/empresa",
            "/empresa/info_general",
            "/empresa/planeacion_estrategica",
            "/empresa/politicas",
            "/empresa/manuales",
            "/fiscal",
            "/fiscal/normativa_sat",
            "/fiscal/criterios_juridicos",
            "/fiscal/casos_precedentes",
            "/clientes",
            "/proveedores",
            "/pcloud",
            "/pcloud/A1_Sponsor",
            "/pcloud/A1_Sponsor/kb",
            "/pcloud/A2_PMO",
            "/pcloud/A2_PMO/kb",
            "/pcloud/A3_Fiscal",
            "/pcloud/A3_Fiscal/kb",
            "/pcloud/A4_Legal",
            "/pcloud/A4_Legal/kb",
            "/pcloud/A5_Finanzas",
            "/pcloud/A5_Finanzas/kb",
            "/pcloud/A6_Proveedor",
            "/pcloud/A6_Proveedor/kb",
            "/pcloud/A7_Defense",
            "/pcloud/A7_Defense/kb",
        ]
        
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        created_folders = []
        skipped_folders = []
        
        try:
            for folder_path in folder_structure:
                parts = folder_path.strip('/').split('/')
                folder_name = parts[-1]
                parent_path = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else '/'
                parent_path = parent_path.rstrip('/') or '/'
                
                existing = await conn.fetchrow(
                    """
                    SELECT id FROM knowledge_folders
                    WHERE empresa_id = $1 AND path = $2
                    """,
                    safe_uuid(empresa_id),
                    folder_path
                )
                
                if existing:
                    skipped_folders.append(folder_path)
                    continue
                
                folder_id = uuid.uuid4()
                await conn.execute(
                    """
                    INSERT INTO knowledge_folders (id, empresa_id, path, name, parent_path, created_by, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    """,
                    folder_id,
                    safe_uuid(empresa_id),
                    folder_path,
                    folder_name,
                    parent_path,
                    uuid.UUID(user_id) if user_id else None
                )
                
                empresa_dir = self._get_empresa_dir(empresa_id)
                fs_path = os.path.join(empresa_dir, folder_path.lstrip('/'))
                os.makedirs(fs_path, exist_ok=True)
                
                created_folders.append(folder_path)
            
            await self.log_audit(None, "folder_structure_initialized", user_id, {
                "created_folders": created_folders,
                "skipped_folders": skipped_folders
            })
            
            return {
                "created_folders": created_folders,
                "skipped_folders": skipped_folders,
                "total_created": len(created_folders),
                "total_skipped": len(skipped_folders)
            }
        finally:
            await conn.close()
    
    async def get_stats(self, empresa_id: Optional[str]) -> Dict[str, Any]:
        """Get repository statistics for an empresa.

        Args:
            empresa_id: The empresa to filter by. None = superadmin sees all.
        """
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")

        try:
            # For superadmins (empresa_id=None), show stats for all empresas
            if empresa_id is None:
                total_docs = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count, COALESCE(SUM(size_bytes), 0) as total_size
                    FROM knowledge_documents
                    WHERE status != 'archived'
                    """
                )

                status_counts = await conn.fetch(
                    """
                    SELECT status, COUNT(*) as count
                    FROM knowledge_documents
                    WHERE status != 'archived'
                    GROUP BY status
                    """
                )

                last_upload = await conn.fetchrow(
                    """
                    SELECT created_at
                    FROM knowledge_documents
                    WHERE status != 'archived'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )

                folder_count = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count
                    FROM knowledge_folders
                    """
                )
            else:
                total_docs = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count, COALESCE(SUM(size_bytes), 0) as total_size
                    FROM knowledge_documents
                    WHERE empresa_id = $1 AND status != 'archived'
                    """,
                    safe_uuid(empresa_id)
                )

                status_counts = await conn.fetch(
                    """
                    SELECT status, COUNT(*) as count
                    FROM knowledge_documents
                    WHERE empresa_id = $1 AND status != 'archived'
                    GROUP BY status
                    """,
                    safe_uuid(empresa_id)
                )

                last_upload = await conn.fetchrow(
                    """
                    SELECT created_at
                    FROM knowledge_documents
                    WHERE empresa_id = $1 AND status != 'archived'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    safe_uuid(empresa_id)
                )

                folder_count = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count
                    FROM knowledge_folders
                    WHERE empresa_id = $1
                    """,
                    safe_uuid(empresa_id)
                )

            status_dict = {row['status']: row['count'] for row in status_counts}

            return {
                "total_documents": total_docs['count'] if total_docs else 0,
                "total_size_bytes": total_docs['total_size'] if total_docs else 0,
                "total_folders": folder_count['count'] if folder_count else 0,
                "last_upload": last_upload['created_at'].isoformat() if last_upload and last_upload['created_at'] else None,
                "documents_by_status": status_dict
            }
        finally:
            await conn.close()
    
    async def search(self, empresa_id: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents by filename."""
        if not query or len(query.strip()) < 2:
            return []
        
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            search_pattern = f"%{query.strip()}%"
            
            documents = await conn.fetch(
                """
                SELECT id, path, filename, mime_type, size_bytes, status, created_at, updated_at
                FROM knowledge_documents
                WHERE empresa_id = $1 AND status != 'archived'
                AND (LOWER(filename) LIKE LOWER($2) OR LOWER(path) LIKE LOWER($2))
                ORDER BY created_at DESC
                LIMIT $3
                """,
                safe_uuid(empresa_id),
                search_pattern,
                limit
            )
            
            return [
                {
                    "id": str(d['id']),
                    "path": d['path'],
                    "filename": d['filename'],
                    "mime_type": d['mime_type'],
                    "size_bytes": d['size_bytes'],
                    "status": d['status'],
                    "created_at": d['created_at'].isoformat() if d['created_at'] else None,
                    "updated_at": d['updated_at'].isoformat() if d['updated_at'] else None
                }
                for d in documents
            ]
        finally:
            await conn.close()
    
    async def get_document_text(self, document_id: str, empresa_id: str) -> Optional[str]:
        """Get extracted text content for a document."""
        conn = await get_db_connection()
        if not conn:
            return None
        
        try:
            row = await conn.fetchrow(
                """
                SELECT extracted_text 
                FROM knowledge_document_text
                WHERE document_id = $1 AND empresa_id = $2
                """,
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
            return row['extracted_text'] if row else None
        finally:
            await conn.close()
    
    async def get_document_chunks(self, document_id: str, empresa_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        conn = await get_db_connection()
        if not conn:
            return []
        
        try:
            chunks = await conn.fetch(
                """
                SELECT id, chunk_index, contenido, tokens_count, created_at
                FROM knowledge_chunks
                WHERE document_id = $1 AND empresa_id = $2
                ORDER BY chunk_index
                """,
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
            return [
                {
                    "id": str(c['id']),
                    "chunk_index": c['chunk_index'],
                    "content": c['contenido'],
                    "tokens_count": c['tokens_count'],
                    "created_at": c['created_at'].isoformat() if c['created_at'] else None
                }
                for c in chunks
            ]
        finally:
            await conn.close()
    
    async def get_all_documents(self, empresa_id: str) -> List[Dict[str, Any]]:
        """Get all documents for an empresa."""
        conn = await get_db_connection()
        if not conn:
            return []
        
        try:
            documents = await conn.fetch(
                """
                SELECT id, path, filename, mime_type, size_bytes, status, created_at
                FROM knowledge_documents
                WHERE empresa_id = $1 AND status != 'archived'
                ORDER BY created_at DESC
                """,
                safe_uuid(empresa_id)
            )
            return [
                {
                    "id": str(d['id']),
                    "path": d['path'],
                    "filename": d['filename'],
                    "mime_type": d['mime_type'],
                    "size_bytes": d['size_bytes'],
                    "status": d['status'],
                    "created_at": d['created_at'].isoformat() if d['created_at'] else None
                }
                for d in documents
            ]
        finally:
            await conn.close()
    
    async def get_jobs(self, empresa_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get processing jobs for an empresa."""
        conn = await get_db_connection()
        if not conn:
            return []
        
        try:
            if status:
                jobs = await conn.fetch(
                    """
                    SELECT id, document_id, tipo, estado, progreso, resultado, error_message, created_at, completed_at
                    FROM knowledge_jobs
                    WHERE empresa_id = $1 AND estado = $2
                    ORDER BY created_at DESC
                    LIMIT 100
                    """,
                    safe_uuid(empresa_id),
                    status
                )
            else:
                jobs = await conn.fetch(
                    """
                    SELECT id, document_id, tipo, estado, progreso, resultado, error_message, created_at, completed_at
                    FROM knowledge_jobs
                    WHERE empresa_id = $1
                    ORDER BY created_at DESC
                    LIMIT 100
                    """,
                    safe_uuid(empresa_id)
                )
            
            return [
                {
                    "id": str(j['id']),
                    "document_id": str(j['document_id']) if j['document_id'] else None,
                    "tipo": j['tipo'],
                    "estado": j['estado'],
                    "progreso": j['progreso'],
                    "resultado": j['resultado'],
                    "error_message": j['error_message'],
                    "created_at": j['created_at'].isoformat() if j['created_at'] else None,
                    "completed_at": j['completed_at'].isoformat() if j['completed_at'] else None
                }
                for j in jobs
            ]
        finally:
            await conn.close()
    
    async def create_job(
        self,
        empresa_id: str,
        document_id: Optional[str],
        tipo: str
    ) -> str:
        """Create a processing job."""
        conn = await get_db_connection()
        if not conn:
            raise DatabaseConnectionError("Database connection unavailable")
        
        try:
            job_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO knowledge_jobs (id, empresa_id, document_id, tipo, estado, progreso, created_at)
                VALUES ($1, $2, $3, $4, 'pending', 0, NOW())
                """,
                job_id,
                safe_uuid(empresa_id),
                uuid.UUID(document_id) if document_id else None,
                tipo
            )
            return str(job_id)
        finally:
            await conn.close()
    
    async def update_job(
        self,
        job_id: str,
        estado: str,
        progreso: int = 0,
        resultado: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update a processing job."""
        conn = await get_db_connection()
        if not conn:
            return False
        
        try:
            completed_at = "NOW()" if estado in ('completed', 'error') else "NULL"
            await conn.execute(
                f"""
                UPDATE knowledge_jobs
                SET estado = $1, progreso = $2, resultado = $3, error_message = $4,
                    updated_at = NOW(), completed_at = {completed_at}
                WHERE id = $5
                """,
                estado,
                progreso,
                resultado,
                error_message,
                uuid.UUID(job_id)
            )
            return True
        finally:
            await conn.close()


knowledge_service = KnowledgeService()
