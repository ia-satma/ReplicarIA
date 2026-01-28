"""
Classification Service (A-CLAS)
Document classification using Claude AI with fiscal taxonomy
"""
import os
import re
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
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


FISCAL_TAXONOMY = {
    "fiscal": {
        "name": "Fiscal",
        "subcategorias": [
            "normativa_sat", "criterios_juridicos", "casos_precedentes",
            "cfdi", "declaraciones", "diot", "isr", "iva", "nomina"
        ]
    },
    "legal": {
        "name": "Legal",
        "subcategorias": [
            "contratos", "poderes", "actas", "litigios", "cumplimiento"
        ]
    },
    "financiero": {
        "name": "Financiero", 
        "subcategorias": [
            "estados_financieros", "presupuestos", "auditorias", "flujo_caja"
        ]
    },
    "empresa": {
        "name": "Empresa",
        "subcategorias": [
            "info_general", "planeacion_estrategica", "politicas", "manuales", "organigrama"
        ]
    },
    "clientes": {
        "name": "Clientes",
        "subcategorias": [
            "contratos_cliente", "facturacion", "cobranza", "correspondencia"
        ]
    },
    "proveedores": {
        "name": "Proveedores",
        "subcategorias": [
            "contratos_proveedor", "pagos", "evaluacion", "lista_negra"
        ]
    },
    "recursos_humanos": {
        "name": "Recursos Humanos",
        "subcategorias": [
            "expedientes", "nominas", "capacitacion", "evaluaciones"
        ]
    }
}

AGENT_ROUTING = {
    "fiscal": ["A3_Fiscal"],
    "legal": ["A4_Legal"],
    "financiero": ["A5_Finanzas"],
    "empresa": ["A1_Sponsor", "A2_PMO"],
    "clientes": ["A2_PMO"],
    "proveedores": ["A6_Proveedor"],
    "recursos_humanos": ["A2_PMO"]
}


async def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


class ClassificationService:
    """AI-powered document classification for fiscal taxonomy."""
    
    def __init__(self):
        self.taxonomy = FISCAL_TAXONOMY
        self.agent_routing = AGENT_ROUTING
    
    async def classify_document(
        self,
        document_id: str,
        empresa_id: str,
        text_content: str,
        filename: str = ""
    ) -> Dict[str, Any]:
        """
        Classify a document using Claude AI.
        Returns category, subcategory, confidence, tags, and agent routing.
        """
        if not text_content or len(text_content.strip()) < 50:
            return await self._fallback_classification(filename)
        
        try:
            classification = await self._classify_with_ai(text_content, filename)
            
            await self._store_classification(document_id, empresa_id, classification)
            
            classification["agents"] = self._get_agent_routing(classification.get("categoria", ""))
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return await self._fallback_classification(filename)
    
    async def _classify_with_ai(self, text: str, filename: str) -> Dict[str, Any]:
        """Use OpenAI to classify the document."""
        try:
            from services.openai_provider import chat_completion, is_configured

            if not is_configured():
                logger.warning("OpenAI not configured, using fallback classification")
                return await self._fallback_classification(filename)

            text_sample = text[:4000] if len(text) > 4000 else text

            prompt = f"""Analiza el siguiente documento y clasifícalo según la taxonomía fiscal mexicana.

TAXONOMÍA DISPONIBLE:
{json.dumps(self.taxonomy, indent=2, ensure_ascii=False)}

NOMBRE DEL ARCHIVO: {filename}

CONTENIDO DEL DOCUMENTO:
{text_sample}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "categoria": "categoria_principal",
    "subcategoria": "subcategoria_especifica",
    "confianza": 0.85,
    "tags": ["tag1", "tag2", "tag3"],
    "requires_review": false,
    "nivel_confidencialidad": "interno",
    "resumen": "Breve descripción del documento"
}}

Valores para nivel_confidencialidad: "publico", "interno", "confidencial", "restringido"
"""

            response_text = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",
                max_tokens=500
            )
            response_text = response_text.strip()
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "categoria": result.get("categoria", "empresa"),
                    "subcategoria": result.get("subcategoria", "info_general"),
                    "confianza": float(result.get("confianza", 0.5)),
                    "tags": result.get("tags", []),
                    "requires_review": result.get("requires_review", False),
                    "nivel_confidencialidad": result.get("nivel_confidencialidad", "interno"),
                    "resumen": result.get("resumen", "")
                }
            
        except Exception as e:
            logger.error(f"AI classification error: {e}")
        
        return await self._fallback_classification(filename)
    
    async def _fallback_classification(self, filename: str) -> Dict[str, Any]:
        """Rule-based fallback classification using filename patterns."""
        filename_lower = filename.lower()
        
        patterns = {
            "fiscal": ["cfdi", "factura", "sat", "isr", "iva", "diot", "nomina", "fiscal", "impuesto"],
            "legal": ["contrato", "poder", "acta", "legal", "convenio", "demanda"],
            "financiero": ["balance", "estado_financiero", "presupuesto", "auditoria", "flujo"],
            "proveedores": ["proveedor", "compra", "orden_compra", "pago_proveedor"],
            "clientes": ["cliente", "venta", "cobranza", "factura_cliente"],
            "recursos_humanos": ["empleado", "rh", "nomina_rh", "capacitacion", "expediente"]
        }
        
        for categoria, keywords in patterns.items():
            if any(kw in filename_lower for kw in keywords):
                return {
                    "categoria": categoria,
                    "subcategoria": self.taxonomy[categoria]["subcategorias"][0],
                    "confianza": 0.6,
                    "tags": [],
                    "requires_review": True,
                    "nivel_confidencialidad": "interno",
                    "resumen": f"Documento clasificado por nombre de archivo: {filename}"
                }
        
        return {
            "categoria": "empresa",
            "subcategoria": "info_general",
            "confianza": 0.3,
            "tags": [],
            "requires_review": True,
            "nivel_confidencialidad": "interno",
            "resumen": "Documento pendiente de clasificación manual"
        }
    
    async def _store_classification(
        self,
        document_id: str,
        empresa_id: str,
        classification: Dict[str, Any]
    ) -> None:
        """Store classification results in database."""
        conn = await get_db_connection()
        if not conn:
            return
        
        try:
            await conn.execute(
                """
                UPDATE knowledge_documents
                SET categoria_principal = $1,
                    subcategoria = $2,
                    clasificacion_confianza = $3,
                    tags = $4,
                    requires_review = $5,
                    nivel_confidencialidad = $6,
                    updated_at = NOW()
                WHERE id = $7 AND empresa_id = $8
                """,
                classification.get("categoria"),
                classification.get("subcategoria"),
                classification.get("confianza", 0.5),
                classification.get("tags", []),
                classification.get("requires_review", False),
                classification.get("nivel_confidencialidad", "interno"),
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
        finally:
            await conn.close()
    
    def _get_agent_routing(self, categoria: str) -> List[str]:
        """Get list of agents that should receive this document."""
        return self.agent_routing.get(categoria, ["A2_PMO"])


class ChunkingService:
    """Service for splitting documents into chunks for RAG."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    async def chunk_document(
        self,
        document_id: str,
        empresa_id: str,
        text: str
    ) -> List[Dict[str, Any]]:
        """Split document into overlapping chunks and store them."""
        if not text:
            return []
        
        chunks = self._split_into_chunks(text)
        
        await self._store_chunks(document_id, empresa_id, chunks)
        
        await self._update_chunks_count(document_id, empresa_id, len(chunks))
        
        return chunks
    
    def _split_into_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append({
                        "index": chunk_index,
                        "content": current_chunk,
                        "tokens": len(current_chunk.split())
                    })
                    chunk_index += 1
                    
                    words = current_chunk.split()
                    overlap_words = words[-self.overlap//5:] if len(words) > self.overlap//5 else []
                    current_chunk = " ".join(overlap_words) + ("\n\n" if overlap_words else "") + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append({
                "index": chunk_index,
                "content": current_chunk,
                "tokens": len(current_chunk.split())
            })
        
        return chunks
    
    async def _store_chunks(
        self,
        document_id: str,
        empresa_id: str,
        chunks: List[Dict[str, Any]]
    ) -> None:
        """Store chunks in database with embeddings for semantic search."""
        conn = await get_db_connection()
        if not conn:
            return
        
        try:
            await conn.execute(
                "DELETE FROM knowledge_chunks WHERE document_id = $1 AND empresa_id = $2",
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
            
            texts = [chunk["content"] for chunk in chunks]
            embeddings = await embedding_service.generate_batch_embeddings(texts)
            
            for chunk, emb in zip(chunks, embeddings):
                embedding_str = None
                if emb:
                    embedding_str = "[" + ",".join(map(str, emb)) + "]"
                
                if embedding_str:
                    await conn.execute(
                        """
                        INSERT INTO knowledge_chunks 
                        (id, document_id, empresa_id, chunk_index, contenido, tokens_count, embedding, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7::vector, NOW())
                        """,
                        uuid.uuid4(),
                        uuid.UUID(document_id),
                        safe_uuid(empresa_id),
                        chunk["index"],
                        chunk["content"],
                        chunk["tokens"],
                        embedding_str
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO knowledge_chunks 
                        (id, document_id, empresa_id, chunk_index, contenido, tokens_count, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, NOW())
                        """,
                        uuid.uuid4(),
                        uuid.UUID(document_id),
                        safe_uuid(empresa_id),
                        chunk["index"],
                        chunk["content"],
                        chunk["tokens"]
                    )
            
            logger.info(f"Stored {len(chunks)} chunks with embeddings for document {document_id}")
        except Exception as e:
            logger.error(f"Error storing chunks: {e}")
            raise
        finally:
            await conn.close()
    
    async def _update_chunks_count(
        self,
        document_id: str,
        empresa_id: str,
        count: int
    ) -> None:
        """Update chunks count in document record."""
        conn = await get_db_connection()
        if not conn:
            return
        
        try:
            await conn.execute(
                """
                UPDATE knowledge_documents
                SET chunks_count = $1, updated_at = NOW()
                WHERE id = $2 AND empresa_id = $3
                """,
                count,
                uuid.UUID(document_id),
                safe_uuid(empresa_id)
            )
        finally:
            await conn.close()


class RAGQueryService:
    """Service for querying the knowledge base using RAG with hybrid search."""
    
    async def query(
        self,
        empresa_id: str,
        query: str,
        limit: int = 5,
        categoria_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge base using hybrid search (semantic + keyword).
        Falls back to keyword-only if vector search fails.
        """
        try:
            from services.vector_search_service import vector_search_service
            
            hybrid_results = await vector_search_service.hybrid_search(
                empresa_id=empresa_id,
                query=query,
                limit=limit,
                categoria_filter=categoria_filter,
                semantic_weight=0.7
            )
            
            if hybrid_results.get("results"):
                return {
                    "query": query,
                    "total_results": len(hybrid_results["results"]),
                    "search_type": hybrid_results.get("search_type", "hybrid"),
                    "results": hybrid_results["results"]
                }
        except Exception as e:
            logger.warning(f"Hybrid search failed, falling back to keyword: {e}")
        
        return await self._keyword_fallback(empresa_id, query, limit, categoria_filter)
    
    async def _keyword_fallback(
        self,
        empresa_id: str,
        query: str,
        limit: int = 5,
        categoria_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback to keyword-based search."""
        conn = await get_db_connection()
        if not conn:
            return {"results": [], "query": query}
        
        try:
            query_words = [w.lower() for w in query.split() if len(w) > 2]
            
            if not query_words:
                return {"results": [], "query": query}
            
            search_pattern = "|".join(query_words)
            
            base_query = """
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
                    d.tags
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON c.document_id = d.id
                WHERE c.empresa_id = $1
                AND d.status = 'indexed'
                AND c.contenido ~* $2
            """
            
            params = [safe_uuid(empresa_id), search_pattern]
            
            if categoria_filter:
                base_query += " AND d.categoria_principal = $3"
                params.append(categoria_filter)
            
            base_query += f" ORDER BY c.tokens_count DESC LIMIT {limit}"
            
            rows = await conn.fetch(base_query, *params)
            
            results = []
            for row in rows:
                content = row['contenido']
                highlight = self._highlight_matches(content, query_words)
                
                results.append({
                    "chunk_id": str(row['chunk_id']),
                    "document_id": str(row['document_id']),
                    "filename": row['filename'],
                    "path": row['path'],
                    "categoria": row['categoria_principal'],
                    "subcategoria": row['subcategoria'],
                    "chunk_index": row['chunk_index'],
                    "content": content[:500] + "..." if len(content) > 500 else content,
                    "highlight": highlight,
                    "relevance_score": self._calculate_relevance(content, query_words)
                })
            
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                "query": query,
                "total_results": len(results),
                "search_type": "keyword",
                "results": results
            }
            
        finally:
            await conn.close()
    
    def _highlight_matches(self, text: str, query_words: List[str]) -> str:
        """Create a highlighted snippet around matching terms."""
        text_lower = text.lower()
        
        for word in query_words:
            idx = text_lower.find(word)
            if idx >= 0:
                start = max(0, idx - 100)
                end = min(len(text), idx + len(word) + 100)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet
        
        return text[:200] + "..." if len(text) > 200 else text
    
    def _calculate_relevance(self, text: str, query_words: List[str]) -> float:
        """Calculate simple relevance score based on word frequency."""
        text_lower = text.lower()
        matches = sum(text_lower.count(word) for word in query_words)
        return min(1.0, matches / 10.0)


classification_service = ClassificationService()
chunking_service = ChunkingService()
rag_query_service = RAGQueryService()
