"""
Vector Search Service for RAG
Implements semantic search with pgvector and hybrid search combining keywords + vectors
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
import asyncpg

from services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')


def safe_uuid(id_string: str) -> uuid.UUID:
    """Convert ID string to UUID safely, generating deterministic UUID for non-UUID strings."""
    if not id_string:
        raise ValueError("ID string cannot be empty")
    try:
        return uuid.UUID(id_string)
    except (ValueError, AttributeError):
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return uuid.uuid5(namespace, id_string)


async def get_db_connection():
    """Get a database connection."""
    if not DATABASE_URL:
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


class VectorSearchService:
    """Service for semantic and hybrid document search."""
    
    def __init__(self):
        self.embedder = embedding_service
    
    async def semantic_search(
        self,
        empresa_id: str,
        query: str,
        limit: int = 10,
        categoria_filter: Optional[str] = None,
        similarity_threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.
        Uses cosine distance with pgvector.
        """
        query_embedding = await self.embedder.generate_embedding(query)
        
        if not query_embedding:
            logger.warning("Could not generate query embedding, falling back to keyword search")
            return await self._keyword_search(empresa_id, query, limit, categoria_filter)
        
        conn = await get_db_connection()
        if not conn:
            return []
        
        try:
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            sql = """
                SELECT 
                    c.id as chunk_id,
                    c.contenido,
                    c.chunk_index,
                    c.tokens_count,
                    d.id as document_id,
                    d.filename,
                    d.path,
                    d.categoria_principal,
                    d.subcategoria,
                    d.tags,
                    1 - (c.embedding <=> $1::vector) as similarity
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON c.document_id = d.id
                WHERE c.empresa_id = $2
                AND d.status = 'indexed'
                AND c.embedding IS NOT NULL
                AND 1 - (c.embedding <=> $1::vector) > $3
            """
            
            params = [embedding_str, safe_uuid(empresa_id), similarity_threshold]
            
            if categoria_filter:
                sql += " AND d.categoria_principal = $4"
                params.append(categoria_filter)
            
            sql += f" ORDER BY similarity DESC LIMIT {limit}"
            
            rows = await conn.fetch(sql, *params)
            
            results = []
            for row in rows:
                results.append({
                    "chunk_id": str(row['chunk_id']),
                    "document_id": str(row['document_id']),
                    "filename": row['filename'],
                    "path": row['path'],
                    "categoria": row['categoria_principal'],
                    "subcategoria": row['subcategoria'],
                    "chunk_index": row['chunk_index'],
                    "content": row['contenido'][:500] + "..." if len(row['contenido']) > 500 else row['contenido'],
                    "full_content": row['contenido'],
                    "similarity": float(row['similarity']),
                    "search_type": "semantic"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return await self._keyword_search(empresa_id, query, limit, categoria_filter)
        finally:
            await conn.close()
    
    async def _keyword_search(
        self,
        empresa_id: str,
        query: str,
        limit: int = 10,
        categoria_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search using PostgreSQL regex."""
        conn = await get_db_connection()
        if not conn:
            return []
        
        try:
            query_words = [w.lower() for w in query.split() if len(w) > 2]
            if not query_words:
                return []
            
            search_pattern = "|".join(query_words)
            
            sql = """
                SELECT 
                    c.id as chunk_id,
                    c.contenido,
                    c.chunk_index,
                    c.tokens_count,
                    d.id as document_id,
                    d.filename,
                    d.path,
                    d.categoria_principal,
                    d.subcategoria
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON c.document_id = d.id
                WHERE c.empresa_id = $1
                AND d.status = 'indexed'
                AND c.contenido ~* $2
            """
            
            params = [safe_uuid(empresa_id), search_pattern]
            
            if categoria_filter:
                sql += " AND d.categoria_principal = $3"
                params.append(categoria_filter)
            
            sql += f" ORDER BY c.tokens_count DESC LIMIT {limit}"
            
            rows = await conn.fetch(sql, *params)
            
            results = []
            for row in rows:
                content = row['contenido']
                relevance = self._calculate_keyword_relevance(content, query_words)
                
                results.append({
                    "chunk_id": str(row['chunk_id']),
                    "document_id": str(row['document_id']),
                    "filename": row['filename'],
                    "path": row['path'],
                    "categoria": row['categoria_principal'],
                    "subcategoria": row['subcategoria'],
                    "chunk_index": row['chunk_index'],
                    "content": content[:500] + "..." if len(content) > 500 else content,
                    "full_content": content,
                    "similarity": relevance,
                    "search_type": "keyword"
                })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results
            
        finally:
            await conn.close()
    
    def _calculate_keyword_relevance(self, text: str, query_words: List[str]) -> float:
        """Calculate relevance score based on word frequency."""
        text_lower = text.lower()
        matches = sum(text_lower.count(word) for word in query_words)
        return min(1.0, matches / 10.0)
    
    async def hybrid_search(
        self,
        empresa_id: str,
        query: str,
        limit: int = 10,
        categoria_filter: Optional[str] = None,
        semantic_weight: float = 0.7
    ) -> Dict[str, Any]:
        """
        Hybrid search combining semantic and keyword results.
        Uses Reciprocal Rank Fusion (RRF) for combining rankings.
        """
        semantic_results = await self.semantic_search(
            empresa_id, query, limit * 2, categoria_filter
        )
        
        keyword_results = await self._keyword_search(
            empresa_id, query, limit * 2, categoria_filter
        )
        
        fused_results = self._rrf_fusion(
            semantic_results, 
            keyword_results, 
            limit,
            semantic_weight=semantic_weight
        )
        
        return {
            "query": query,
            "total_results": len(fused_results),
            "search_type": "hybrid",
            "semantic_count": len(semantic_results),
            "keyword_count": len(keyword_results),
            "results": fused_results
        }
    
    def _rrf_fusion(
        self, 
        semantic_list: List[Dict], 
        keyword_list: List[Dict], 
        limit: int,
        k: int = 60,
        semantic_weight: float = 0.7
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion - combines rankings from multiple retrieval methods.
        Higher weight for semantic means more trust in vector similarity.
        """
        scores = {}
        items = {}
        
        for rank, item in enumerate(semantic_list):
            chunk_id = item["chunk_id"]
            scores[chunk_id] = scores.get(chunk_id, 0) + semantic_weight / (k + rank + 1)
            if chunk_id not in items:
                items[chunk_id] = item
        
        keyword_weight = 1 - semantic_weight
        for rank, item in enumerate(keyword_list):
            chunk_id = item["chunk_id"]
            scores[chunk_id] = scores.get(chunk_id, 0) + keyword_weight / (k + rank + 1)
            if chunk_id not in items:
                items[chunk_id] = item
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for chunk_id in sorted_ids[:limit]:
            item = items[chunk_id].copy()
            item["rrf_score"] = scores[chunk_id]
            item["search_type"] = "hybrid"
            results.append(item)
        
        return results
    
    async def store_embedding(
        self,
        chunk_id: str,
        empresa_id: str,
        embedding: List[float]
    ) -> bool:
        """Store an embedding for a chunk."""
        conn = await get_db_connection()
        if not conn:
            return False
        
        try:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            await conn.execute("""
                UPDATE knowledge_chunks
                SET embedding = $1::vector
                WHERE id = $2 AND empresa_id = $3
            """, embedding_str, uuid.UUID(chunk_id), safe_uuid(empresa_id))
            
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            return False
        finally:
            await conn.close()
    
    async def check_pgvector_available(self) -> bool:
        """Check if pgvector extension is installed and working."""
        conn = await get_db_connection()
        if not conn:
            return False
        
        try:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to check pgvector: {e}")
            return False
        finally:
            await conn.close()


vector_search_service = VectorSearchService()
