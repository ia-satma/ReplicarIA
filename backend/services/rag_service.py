"""
RAG Service for Revisar.ia Multi-Agent System
Provides high-level interface for document retrieval and context for agent deliberations
Integrates RagRepository and AgentKnowledgeService for grounded responses
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb not available - RAG features disabled")

try:
    from services.rag_repository import RagRepository
    RAG_REPOSITORY_AVAILABLE = True
except ImportError:
    RAG_REPOSITORY_AVAILABLE = False
    RagRepository = None
    logger.warning("RagRepository not available")

try:
    from services.agent_knowledge_service import AgentKnowledgeService, agent_knowledge_service
    AGENT_KNOWLEDGE_AVAILABLE = True
except ImportError:
    AGENT_KNOWLEDGE_AVAILABLE = False
    AgentKnowledgeService = None
    agent_knowledge_service = None
    logger.warning("AgentKnowledgeService not available")

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# SYNCED WITH: backend/config/agents_registry.py
# Colecciones ChromaDB por agente para RAG
AGENT_COLLECTIONS = {
    # Agentes Principales (7)
    "A1_SPONSOR": "estrategia_knowledge",
    "A1_ESTRATEGIA": "estrategia_knowledge",  # Alias
    "A2_PMO": "pmo_knowledge",
    "A3_FISCAL": "fiscal_knowledge",
    "A4_LEGAL": "legal_knowledge",
    "LEGAL": "legal_knowledge",  # Alias
    "A5_FINANZAS": "finanzas_knowledge",
    "A6_PROVEEDOR": "proveedor_knowledge",
    "A7_DEFENSA": "defensa_knowledge",
    # Agentes Especializados (3)
    "A8_AUDITOR": "auditor_knowledge",
    "KB_CURATOR": "knowledge_base",
    "DEVILS_ADVOCATE": "control_knowledge",
    # Subagentes Fiscales (3) - Comparten colección con A3_FISCAL
    "S1_TIPIFICACION": "fiscal_knowledge",
    "S2_MATERIALIDAD": "fiscal_knowledge",
    "S3_RIESGOS": "fiscal_knowledge",
    # Subagentes PMO (5) - Comparten colección con A2_PMO
    "S_ANALIZADOR": "pmo_knowledge",
    "S_CLASIFICADOR": "pmo_knowledge",
    "S_RESUMIDOR": "pmo_knowledge",
    "S_VERIFICADOR": "pmo_knowledge",
    "S_REDACTOR": "pmo_knowledge",
}

# Links públicos de pCloud por agente (para acceso directo)
AGENT_PCLOUD_LINKS = {
    "A1_SPONSOR": "https://u.pcloud.link/publink/show?code=kZHqng5ZeW36Cw3UbmY6lu1DsJ1QYj9hhCe7",
    "A2_PMO": "https://u.pcloud.link/publink/show?code=kZJqng5ZGDwXSRewkijTxOYa3WBCIkRXeUpV",
    "A3_FISCAL": "https://u.pcloud.link/publink/show?code=kZQqng5ZE3BXwURDwrhkgreFBT4xXbyJDOa7",
    "A4_LEGAL": None,  # Pendiente crear link público
    "A5_FINANZAS": "https://u.pcloud.link/publink/show?code=kZhqng5ZpurMT7tJ7wH9vDUXiGy2Mbju5M0X",
    "A6_PROVEEDOR": None,
    "A7_DEFENSA": None,
    "A8_AUDITOR": None,
    "KB_CURATOR": None,
    "LEGAL": None,
}


class RagService:
    """
    High-level RAG Service that integrates RagRepository and AgentKnowledgeService
    for providing grounded context to agents and preventing hallucinations.
    """
    
    def __init__(
        self,
        rag_repository: Optional[Any] = None,
        knowledge_service: Optional[Any] = None,
        persist_directory: str = "./chroma_db"
    ):
        self.persist_directory = persist_directory
        self.initialized = False
        
        if RAG_REPOSITORY_AVAILABLE:
            self.rag_repo = rag_repository or RagRepository()
            logger.info("RagService: Using RagRepository for vector storage")
        else:
            self.rag_repo = None
            logger.warning("RagService: RagRepository not available")
        
        if AGENT_KNOWLEDGE_AVAILABLE:
            self.knowledge_service = knowledge_service or agent_knowledge_service
            logger.info("RagService: Using AgentKnowledgeService for knowledge ingestion")
        else:
            self.knowledge_service = None
            logger.warning("RagService: AgentKnowledgeService not available")
        
        self.client = None
        self.embedding_function = None
        self.collections = {}
        
        self._init_chromadb()
        
        if self.rag_repo or self.client:
            self.initialized = True
            logger.info(f"✅ RagService initialized successfully")
    
    def _init_chromadb(self):
        """Initialize ChromaDB for legacy collection support"""
        if not CHROMADB_AVAILABLE:
            return
            
        if not OPENAI_API_KEY:
            logger.warning("RagService: OPENAI_API_KEY not set - legacy ChromaDB disabled")
            return
            
        try:
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
            
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            for agent_id, collection_name in AGENT_COLLECTIONS.items():
                try:
                    self.collections[agent_id] = self.client.get_or_create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"agent_id": agent_id}
                    )
                except Exception as e:
                    logger.warning(f"Could not create collection for {agent_id}: {e}")
            
            logger.info(f"RagService: ChromaDB initialized with {len(self.collections)} collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
    
    def get_context_for_agent(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5
    ) -> List[str]:
        """
        Returns list of relevant context strings from agent's knowledge base.
        Each context string includes proper citations (document title, date, source).
        
        Args:
            agent_id: The ID of the agent requesting context
            query: The query to search for relevant documents
            top_k: Maximum number of results to return
            
        Returns:
            List of formatted context strings with citations
        """
        context_strings = []
        
        if self.rag_repo:
            try:
                results = self.rag_repo.query(agent_id, query, top_k=top_k)
                
                if results and results.get('documents'):
                    docs = results['documents'][0] if results['documents'] else []
                    metas = results.get('metadatas', [[]])[0]
                    dists = results.get('distances', [[]])[0]
                    
                    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
                        relevance_score = 1.0 - dist if dist else 0.5
                        
                        if relevance_score >= 0.2:
                            title = meta.get('title') or meta.get('doc_title') or meta.get('filename', 'Documento sin título')
                            date = meta.get('created_at') or meta.get('ingested_at') or meta.get('modified', '')
                            if isinstance(date, str) and len(date) >= 10:
                                date = date[:10]
                            source = meta.get('webViewLink') or meta.get('web_view_link') or meta.get('source', 'local')
                            
                            formatted_context = f"""[Documento: {title}] (Fecha: {date}) - Fuente: {source}
Relevancia: {relevance_score:.2f}

{doc}"""
                            context_strings.append(formatted_context)
                    
                    logger.info(f"RagService: Retrieved {len(context_strings)} context items for {agent_id}")
                    
            except Exception as e:
                logger.error(f"Error querying RagRepository for {agent_id}: {e}")
        
        if not context_strings and self.collections.get(agent_id):
            try:
                collection = self.collections[agent_id]
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
                
                if results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                        distance = results["distances"][0][i] if results.get("distances") else 0.5
                        relevance = 1.0 - distance
                        
                        title = meta.get('title', 'Documento')
                        date = meta.get('date', 'N/A')
                        source = meta.get('source', 'ChromaDB')
                        
                        formatted_context = f"""[Documento: {title}] (Fecha: {date}) - Fuente: {source}
Relevancia: {relevance:.2f}

{doc}"""
                        context_strings.append(formatted_context)
                    
                    logger.info(f"RagService: Retrieved {len(context_strings)} legacy context items for {agent_id}")
                    
            except Exception as e:
                logger.error(f"Error querying ChromaDB for {agent_id}: {e}")
        
        return context_strings
    
    def get_raw_results_for_agent(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Returns raw query results including metadata and distances for answer_guard processing.
        
        Args:
            agent_id: The ID of the agent
            query: The search query
            top_k: Maximum number of results
            
        Returns:
            Dict with documents, metadatas, and distances
        """
        if self.rag_repo:
            try:
                return self.rag_repo.query(agent_id, query, top_k=top_k)
            except Exception as e:
                logger.error(f"Error getting raw results: {e}")
        
        return {"documents": [], "metadatas": [], "distances": []}
    
    def ensure_agent_knowledge_loaded(self, agent_id: str) -> Dict[str, Any]:
        """
        Checks if agent has knowledge loaded, if not ingests from folder.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict with status and count of documents
        """
        doc_count = 0
        
        if self.rag_repo:
            try:
                doc_count = self.rag_repo.count(agent_id)
            except Exception as e:
                logger.warning(f"Could not get count from RagRepository: {e}")
        
        if doc_count == 0 and self.collections.get(agent_id):
            try:
                doc_count = self.collections[agent_id].count()
            except Exception:
                pass
        
        if doc_count > 0:
            return {
                "status": "loaded",
                "agent_id": agent_id,
                "document_count": doc_count,
                "action": "none"
            }
        
        if self.knowledge_service:
            try:
                logger.info(f"No knowledge found for {agent_id}, ingesting from folder...")
                result = self.knowledge_service.ingest_agent_folder(agent_id)
                
                return {
                    "status": "ingested",
                    "agent_id": agent_id,
                    "document_count": result.get('chunks_ingested', 0),
                    "files_processed": result.get('files_processed', 0),
                    "action": "ingested_from_folder"
                }
                
            except Exception as e:
                logger.error(f"Error ingesting knowledge for {agent_id}: {e}")
                return {
                    "status": "error",
                    "agent_id": agent_id,
                    "error": str(e),
                    "action": "failed"
                }
        
        return {
            "status": "empty",
            "agent_id": agent_id,
            "document_count": 0,
            "action": "no_knowledge_service"
        }
    
    def refresh_agent_knowledge(self, agent_id: str) -> Dict[str, Any]:
        """
        Re-ingests all files from agent folder, refreshing the knowledge base.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict with ingestion results
        """
        if not self.knowledge_service:
            return {
                "success": False,
                "error": "AgentKnowledgeService not available",
                "agent_id": agent_id
            }
        
        try:
            logger.info(f"Refreshing knowledge for {agent_id}...")
            result = self.knowledge_service.ingest_agent_folder(agent_id)
            
            return {
                "success": result.get('success', False),
                "agent_id": agent_id,
                "chunks_ingested": result.get('chunks_ingested', 0),
                "files_processed": result.get('files_processed', 0),
                "errors": result.get('errors', []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error refreshing knowledge for {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e)
            }
    
    def add_document(
        self,
        agent_id: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Add a document to agent's knowledge base"""
        if self.rag_repo:
            try:
                meta = metadata or {}
                meta['doc_id'] = document_id
                chunk_id = self.rag_repo.upsert_document(agent_id, content, meta)
                return {"success": True, "chunk_id": chunk_id, "agent_id": agent_id}
            except Exception as e:
                logger.error(f"Error adding document via RagRepository: {e}")
        
        if self.collections.get(agent_id):
            try:
                doc_metadata = metadata or {}
                doc_metadata["agent_id"] = agent_id
                
                self.collections[agent_id].add(
                    ids=[document_id],
                    documents=[content],
                    metadatas=[doc_metadata]
                )
                
                return {"success": True, "document_id": document_id, "agent_id": agent_id}
                
            except Exception as e:
                logger.error(f"Error adding document via ChromaDB: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "No storage backend available"}
    
    def query(
        self,
        agent_id: str,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict] = None
    ) -> Dict:
        """Query agent's knowledge base - legacy method for compatibility"""
        if self.rag_repo:
            try:
                results = self.rag_repo.query(agent_id, query_text, top_k=n_results)
                
                documents = []
                if results.get('documents') and results['documents'][0]:
                    docs = results['documents'][0]
                    metas = results.get('metadatas', [[]])[0]
                    dists = results.get('distances', [[]])[0]
                    
                    for i, doc in enumerate(docs):
                        documents.append({
                            "id": f"doc_{i}",
                            "content": doc,
                            "metadata": metas[i] if i < len(metas) else {},
                            "distance": dists[i] if i < len(dists) else None
                        })
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "query": query_text,
                    "documents": documents,
                    "count": len(documents)
                }
                
            except Exception as e:
                logger.error(f"Error querying: {e}")
        
        collection = self.collections.get(agent_id)
        if not collection:
            return {"success": False, "error": f"Unknown agent: {agent_id}", "documents": []}
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )
            
            documents = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    documents.append({
                        "id": results["ids"][0][i] if results["ids"] else None,
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            return {
                "success": True,
                "agent_id": agent_id,
                "query": query_text,
                "documents": documents,
                "count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            return {"success": False, "error": str(e), "documents": []}
    
    def get_context_for_deliberation(
        self,
        project_description: str,
        agent_id: str,
        n_results: int = 5
    ) -> str:
        """
        Get formatted context string for agent deliberation - legacy method.
        """
        context_strings = self.get_context_for_agent(agent_id, project_description, top_k=n_results)
        
        if not context_strings:
            return ""
        
        context_parts = ["## Contexto Relevante de tu Base de Conocimiento:\n"]
        
        for i, ctx in enumerate(context_strings, 1):
            context_parts.append(f"### Documento {i}")
            context_parts.append(ctx[:1500])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_collection_stats(self, agent_id: str) -> Dict:
        """Get statistics for agent's knowledge collection"""
        stats = {
            "agent_id": agent_id,
            "pcloud_link": AGENT_PCLOUD_LINKS.get(agent_id)
        }
        
        if self.rag_repo:
            try:
                stats["rag_repository_count"] = self.rag_repo.count(agent_id)
            except Exception:
                stats["rag_repository_count"] = 0
        
        collection = self.collections.get(agent_id)
        if collection:
            try:
                stats["chromadb_count"] = collection.count()
                stats["collection_name"] = AGENT_COLLECTIONS.get(agent_id, "unknown")
            except Exception:
                stats["chromadb_count"] = 0
        
        stats["total_documents"] = stats.get("rag_repository_count", 0) + stats.get("chromadb_count", 0)
        stats["success"] = True
        
        return stats
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all agent collections"""
        stats = {}
        for agent_id in AGENT_COLLECTIONS.keys():
            stats[agent_id] = self.get_collection_stats(agent_id)
        
        return {
            "initialized": self.initialized,
            "persist_directory": self.persist_directory,
            "rag_repository_available": self.rag_repo is not None,
            "knowledge_service_available": self.knowledge_service is not None,
            "agents": stats
        }


rag_service = RagService()


class RAGService(RagService):
    """Alias for backwards compatibility"""
    pass
