import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import nltk
from datetime import datetime, timezone
from services.rag_repository import RagRepository

logger = logging.getLogger(__name__)

# Descargar datos NLTK necesarios
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class ProfessionalRAGService:
    """
    Servicio RAG profesional con retrieval híbrido (semantic + BM25),
    reranking, deduplicación y citaciones obligatorias.
    """
    
    def __init__(self):
        # Usar RagRepository
        self.rag_repo = RagRepository()
        
        # Text splitter para chunking semántico
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        # BM25 indices (se cargan bajo demanda)
        self.bm25_indices = {}
        
        # Collections alias
        self.collections = {}
        for agent_id in ["A1_SPONSOR", "A2_PMO", "A3_FISCAL", "A5_FINANZAS"]:
            self.collections[agent_id] = self.rag_repo._get_collection(agent_id)
        
        logger.info("✅ Professional RAG Service initialized with RagRepository")
    
    def _initialize_collections(self):
        """Inicializar colecciones de ChromaDB para cada agente"""
        collection_names = {
            "A1_SPONSOR": "satma_prod_A1",
            "A2_PMO": "satma_prod_A2",
            "A3_FISCAL": "satma_prod_A3",
            "A5_FINANZAS": "satma_prod_A5"
        }
        
        for agent_id, col_name in collection_names.items():
            try:
                collection = self.chroma_client.get_or_create_collection(
                    name=col_name,
                    metadata={"agent_id": agent_id}
                )
                self.collections[agent_id] = collection
                logger.info(f"✅ Collection {col_name} ready for {agent_id}")
            except Exception as e:
                logger.error(f"Error creating collection for {agent_id}: {str(e)}")
    
    async def ingest_drive_folder(
        self,
        agent_id: str,
        folder_id: str
    ) -> Dict:
        """
        Ingesta documentos de una carpeta de Drive usando token del agente.
        Pipeline: extract → PII redaction → chunk → embed → upsert
        """
        
        logger.info(f"[INGESTION] Iniciando ingesta para {agent_id} from folder {folder_id}")
        
        collection = self.collections.get(agent_id)
        if not collection:
            return {"error": f"Collection not found for {agent_id}"}
        
        try:
            # Usar MultiAgentDriveService
            from services.multi_agent_drive import MultiAgentDriveService
            multi_drive = MultiAgentDriveService()
            
            # Listar archivos en Drive del agente
            files = multi_drive.list_files_in_folder(agent_id, folder_id)
            
            if not files:
                logger.warning(f"No files found for {agent_id}")
                return {"success": False, "error": "No files found", "docs_processed": 0, "chunks_added": 0}
            
            chunks_added = 0
            docs_processed = 0
            
            for file in files[:20]:  # Procesar primeros 20 archivos
                file_id = file.get('id')
                file_name = file.get('name')
                mime_type = file.get('mimeType', '')
                
                logger.info(f"  Procesando: {file_name} (type: {mime_type})")
                
                # Extraer texto
                content = multi_drive.get_file_content(agent_id, file_id, mime_type)
                
                logger.info(f"    Contenido extraído: {len(content) if content else 0} caracteres")
                
                if not content:
                    logger.warning(f"    SKIP: Sin contenido")
                    continue
                
                if content.startswith('[Archivo binario'):
                    logger.warning(f"    SKIP: Binario no soportado")
                    continue
                
                if len(content) < 50:
                    logger.warning(f"    SKIP: Contenido muy corto ({len(content)} chars)")
                    continue
                
                # PII redaction básica
                content_clean = self._basic_pii_redaction(content)
                
                # Chunking semántico
                chunks = self.text_splitter.split_text(content_clean)
                
                logger.info(f"    Chunking: {len(chunks)} chunks generados")
                
                if not chunks:
                    logger.warning(f"    SKIP: No se generaron chunks")
                    continue
                
                # Preparar metadatos y upsert
                for i, chunk in enumerate(chunks):
                    # Generar webViewLink si falta
                    web_link = file.get('webViewLink', '')
                    if not web_link:
                        if 'google-apps.document' in mime_type:
                            web_link = f"https://docs.google.com/document/d/{file_id}/view"
                        elif 'google-apps.spreadsheet' in mime_type:
                            web_link = f"https://docs.google.com/spreadsheets/d/{file_id}/view"
                        elif 'google-apps.presentation' in mime_type:
                            web_link = f"https://docs.google.com/presentation/d/{file_id}/view"
                        else:
                            web_link = f"https://drive.google.com/file/d/{file_id}/view"
                    
                    metadata = {
                        "doc_title": file_name,
                        "file_id": file_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "created_at": file.get('createdTime', datetime.now(timezone.utc).isoformat()),
                        "doctype": self._infer_doctype(file_name, mime_type),
                        "jurisdiction": "MX",
                        "agent_id": agent_id,
                        "source": "google_drive",
                        "web_view_link": web_link  # ← AHORA CON FALLBACK
                    }
                    
                    # UPSERT usando RagRepository
                    doc_id = self.rag_repo.upsert_document(
                        agent_id=agent_id,
                        text=chunk,
                        metadata=metadata
                    )
                    
                    if doc_id:
                        chunks_added += 1
                
                docs_processed += 1
                logger.info(f"  ✅ {file_name}: {len(chunks)} chunks guardados en vector store")
            
            logger.info(f"✅ Ingestion completa: {docs_processed} docs, {chunks_added} chunks")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "docs_processed": docs_processed,
                "chunks_added": chunks_added
            }
            
        except Exception as e:
            logger.error(f"Error en ingestion para {agent_id}: {str(e)}")
            return {"error": str(e), "docs_processed": 0, "chunks_added": 0}
    
    def query_hybrid(
        self,
        agent_id: str,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.20
    ) -> List[Dict]:
        """
        Consulta híbrida: semantic (ChromaDB) + lexical (BM25) + rerank
        """
        
        collection = self.collections.get(agent_id)
        if not collection:
            logger.warning(f"No collection for {agent_id}")
            return []
        
        try:
            # 1. Semantic search con ChromaDB
            query_embedding = self.embeddings.embed_query(query)
            
            semantic_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Filtrar por score threshold
            results = []
            if semantic_results['documents'] and len(semantic_results['documents']) > 0:
                for i, doc in enumerate(semantic_results['documents'][0]):
                    distance = semantic_results['distances'][0][i]
                    score = 1 - distance  # Convertir distance a similarity score
                    
                    if score >= score_threshold:
                        metadata = semantic_results['metadatas'][0][i]
                        results.append({
                            "text": doc,
                            "score": score,
                            "metadata": metadata,
                            "source": "semantic"
                        })
            
            # 2. Lexical search con BM25 (boost términos legales)
            # TODO: Implementar BM25 parallel search y fusión
            
            # 3. Deduplicación
            results = self._deduplicate_results(results)
            
            # 4. Reranking (simple: mantener orden por score)
            results = sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]
            
            logger.info(f"✅ Query híbrido para {agent_id}: {len(results)} resultados")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en query híbrido: {str(e)}")
            return []
    
    def format_context_with_citations(self, results: List[Dict]) -> str:
        """
        Formatea resultados con citaciones formales obligatorias
        """
        if not results:
            return "[NO HAY FUENTES DISPONIBLES EN LA BASE DE CONOCIMIENTO]"
        
        context = "=== FUENTES CONSULTADAS ===\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            doc_title = metadata.get('doc_title', 'Documento')
            created_at = metadata.get('created_at', 'Fecha desconocida')
            web_link = metadata.get('web_view_link', 'Link no disponible')
            
            context += f"Fuente {i}:\n"
            context += f"[Documento: {doc_title}]\n"
            context += f"(Fecha: {created_at[:10]})\n"
            context += f"Enlace: {web_link}\n\n"
            context += f"Contenido:\n{result['text']}\n\n"
            context += "─" * 80 + "\n\n"
        
        context += "\n=== FIN DE FUENTES ===\n\n"
        context += "INSTRUCCIÓN: DEBES citar estas fuentes en tu análisis usando el formato mostrado.\n"
        
        return context
    
    def _basic_pii_redaction(self, text: str) -> str:
        """Redacción básica de PII: emails"""
        import re
        # Redactar emails
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        return text
    
    def _infer_doctype(self, filename: str, mime_type: str) -> str:
        """Inferir tipo de documento"""
        if 'spreadsheet' in mime_type or filename.endswith(('.xlsx', '.xls')):
            return 'spreadsheet'
        elif 'document' in mime_type or filename.endswith('.docx'):
            return 'document'
        elif 'pdf' in mime_type:
            return 'pdf'
        else:
            return 'other'
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Deduplicar resultados similares"""
        seen_texts = set()
        deduped = []
        
        for result in results:
            text_hash = hash(result['text'][:100])  # Hash primeros 100 chars
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                deduped.append(result)
        
        return deduped
    
    def get_collection_stats(self, agent_id: str) -> Dict:
        """Obtener estadísticas de la colección de un agente"""
        try:
            count = self.rag_repo.count(agent_id)
            return {
                "agent_id": agent_id,
                "total_chunks": count,
                "collection_name": self.rag_repo._colname(agent_id)
            }
        except Exception as e:
            return {"error": str(e)}
