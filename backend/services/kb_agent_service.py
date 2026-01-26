"""
KB Agent Service - Knowledge Base Manager for RAG
Dr. Elena Vázquez Archivista - Directora de Gestión del Conocimiento
"""
import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum

from services.kb_chunkers import (
    LegalDocumentChunker, JurisprudenceChunker, ContractChunker,
    CriteriaSATChunker, GlossaryChunker, DocumentChunk, ChunkType
)


class DocumentType(str, Enum):
    LEGAL_CODE = "legal_code"           # CFF, LISR, LIVA
    JURISPRUDENCE = "jurisprudence"     # Tesis, jurisprudencias
    CONTRACT = "contract"               # Contratos de servicios
    CRITERIA_SAT = "criteria_sat"       # Criterios normativos
    FINANCIAL = "financial"             # Estados financieros
    CATALOG = "catalog"                 # Catálogos SAT
    GLOSSARY = "glossary"               # Glosarios
    TEMPLATE = "template"               # Plantillas
    CASE_REFERENCE = "case_reference"   # Casos de referencia
    GENERAL = "general"                 # Otros documentos


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class KBDocument(BaseModel):
    """Represents a document in the Knowledge Base"""
    id: str
    filename: str
    filepath: str
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    chunk_count: int = 0
    token_count: int = 0
    file_hash: str
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class KBSearchResult(BaseModel):
    """Search result from KB"""
    chunk: DocumentChunk
    score: float
    highlights: List[str] = []


class KBAgentService:
    """
    Knowledge Base Manager Service
    
    Responsibilities:
    - Document ingestion and processing
    - Chunking strategy selection
    - Metadata extraction
    - Search and retrieval for RAG
    """
    
    KB_ROOT = Path("backend/knowledge_base")
    
    TYPE_PATHS = {
        DocumentType.LEGAL_CODE: "marco_legal/codigos",
        DocumentType.JURISPRUDENCE: "marco_legal/jurisprudencias",
        DocumentType.CRITERIA_SAT: "marco_legal/criterios_sat",
        DocumentType.CONTRACT: "documentos_empresa",
        DocumentType.CATALOG: "catalogos_sat",
        DocumentType.GLOSSARY: "glosarios",
        DocumentType.TEMPLATE: "plantillas",
        DocumentType.CASE_REFERENCE: "casos_referencia",
    }
    
    def __init__(self):
        self.legal_chunker = LegalDocumentChunker()
        self.juris_chunker = JurisprudenceChunker()
        self.contract_chunker = ContractChunker()
        self.criteria_chunker = CriteriaSATChunker()
        self.glossary_chunker = GlossaryChunker()
        
        self.chunks: List[DocumentChunk] = []
        self.documents: Dict[str, KBDocument] = {}
    
    def ingest_document(
        self,
        filepath: str,
        document_type: DocumentType,
        metadata: Dict[str, Any] = None
    ) -> KBDocument:
        """
        Ingest a document into the Knowledge Base.
        
        Process:
        1. Read and validate document
        2. Calculate file hash
        3. Select appropriate chunker
        4. Generate chunks with metadata
        5. Store chunks for retrieval
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Document not found: {filepath}")
        
        content = self._read_document(filepath)
        
        file_hash = self._calculate_hash(content)
        doc_id = f"{document_type.value}_{file_hash[:12]}"
        
        doc = KBDocument(
            id=doc_id,
            filename=filepath.name,
            filepath=str(filepath),
            document_type=document_type,
            status=DocumentStatus.PROCESSING,
            file_hash=file_hash,
            metadata=metadata or {}
        )
        
        try:
            chunks = self._chunk_document(content, document_type, filepath.name, str(filepath))
            
            for chunk in chunks:
                chunk.id = f"{doc_id}_{len(self.chunks)}"
                self.chunks.append(chunk)
            
            doc.chunk_count = len(chunks)
            doc.token_count = sum(c.token_count or 0 for c in chunks)
            doc.status = DocumentStatus.INDEXED
            doc.indexed_at = datetime.utcnow()
            
        except Exception as e:
            doc.status = DocumentStatus.ERROR
            doc.error_message = str(e)
        
        self.documents[doc_id] = doc
        return doc
    
    def _read_document(self, filepath: Path) -> str:
        """Read document content based on file type"""
        suffix = filepath.suffix.lower()
        
        if suffix == '.md':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), ensure_ascii=False)
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _chunk_document(
        self,
        content: str,
        document_type: DocumentType,
        filename: str,
        filepath: str
    ) -> List[DocumentChunk]:
        """Select and apply appropriate chunker"""
        
        if document_type == DocumentType.LEGAL_CODE:
            return self.legal_chunker.chunk_legal_document(content, filename, filepath)
        
        elif document_type == DocumentType.JURISPRUDENCE:
            return self.juris_chunker.chunk_jurisprudence(content, filename, filepath)
        
        elif document_type == DocumentType.CONTRACT:
            return self.contract_chunker.chunk_contract(content, filename, filepath)
        
        elif document_type == DocumentType.CRITERIA_SAT:
            is_vinculante = 'normativos' in filepath.lower()
            return self.criteria_chunker.chunk_criteria(content, filename, is_vinculante)
        
        else:
            return self._generic_chunk(content, filename, filepath, document_type)
    
    def _generic_chunk(
        self,
        content: str,
        filename: str,
        filepath: str,
        doc_type: DocumentType
    ) -> List[DocumentChunk]:
        """Generic chunking for unspecified document types"""
        chunks = []
        
        sections = content.split('\n\n')
        current_chunk = ""
        
        for section in sections:
            if len(current_chunk) + len(section) < 2000:
                current_chunk += "\n\n" + section
            else:
                if current_chunk.strip():
                    from backend.services.kb_chunkers import ChunkMetadata
                    chunks.append(DocumentChunk(
                        content=current_chunk.strip(),
                        metadata=ChunkMetadata(
                            chunk_type=ChunkType.DOCUMENT_SECTION,
                            source_document=filename,
                            source_path=filepath
                        ),
                        token_count=len(current_chunk) // 4
                    ))
                current_chunk = section
        
        if current_chunk.strip():
            from backend.services.kb_chunkers import ChunkMetadata
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                metadata=ChunkMetadata(
                    chunk_type=ChunkType.DOCUMENT_SECTION,
                    source_document=filename,
                    source_path=filepath
                ),
                token_count=len(current_chunk) // 4
            ))
        
        return chunks
    
    def search(
        self,
        query: str,
        document_types: List[DocumentType] = None,
        max_results: int = 5,
        min_score: float = 0.0
    ) -> List[KBSearchResult]:
        """
        Search the Knowledge Base for relevant chunks.
        
        In production, this would use vector similarity search.
        This implementation uses keyword matching for demo purposes.
        """
        results = []
        query_terms = set(query.lower().split())
        
        for chunk in self.chunks:
            if document_types:
                chunk_type = chunk.metadata.chunk_type
                type_mapping = {
                    ChunkType.LEGAL_ARTICLE: DocumentType.LEGAL_CODE,
                    ChunkType.LEGAL_FRACTION: DocumentType.LEGAL_CODE,
                    ChunkType.JURISPRUDENCIA_MAIN: DocumentType.JURISPRUDENCE,
                    ChunkType.JURISPRUDENCIA_SUMMARY: DocumentType.JURISPRUDENCE,
                    ChunkType.CONTRACT_CLAUSE: DocumentType.CONTRACT,
                    ChunkType.CRITERIA_SAT: DocumentType.CRITERIA_SAT,
                }
                if type_mapping.get(chunk_type) not in document_types:
                    continue
            
            content_terms = set(chunk.content.lower().split())
            keyword_terms = set(chunk.metadata.keywords) if chunk.metadata.keywords else set()
            
            content_matches = len(query_terms & content_terms)
            keyword_matches = len(query_terms & keyword_terms) * 2
            
            total_score = (content_matches + keyword_matches) / (len(query_terms) + 1)
            
            if total_score >= min_score:
                highlights = [term for term in query_terms if term in chunk.content.lower()]
                
                results.append(KBSearchResult(
                    chunk=chunk,
                    score=total_score,
                    highlights=highlights
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]
    
    def get_context_for_agent(
        self,
        agent_id: str,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant KB context for a specific agent.
        
        Each agent has preferred document types and search strategies.
        """
        agent_preferences = {
            "A1_ESTRATEGIA": [DocumentType.LEGAL_CODE, DocumentType.CASE_REFERENCE],
            "A3_FISCAL": [DocumentType.LEGAL_CODE, DocumentType.CRITERIA_SAT, DocumentType.JURISPRUDENCE],
            "A4_LEGAL": [DocumentType.CONTRACT, DocumentType.LEGAL_CODE],
            "A6_PROVEEDOR": [DocumentType.CRITERIA_SAT, DocumentType.LEGAL_CODE],
            "A7_DEFENSA": [DocumentType.LEGAL_CODE, DocumentType.JURISPRUDENCE, DocumentType.CASE_REFERENCE],
        }
        
        doc_types = agent_preferences.get(agent_id, None)
        results = self.search(query, document_types=doc_types, max_results=10)
        
        context_parts = []
        current_tokens = 0
        
        for result in results:
            chunk_tokens = result.chunk.token_count or len(result.chunk.content) // 4
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            source = result.chunk.metadata.source_document
            context_parts.append(f"[Fuente: {source}]\n{result.chunk.content}\n")
            current_tokens += chunk_tokens
        
        return "\n---\n".join(context_parts)
    
    def index_kb_directory(self, directory: str = None) -> Dict[str, int]:
        """
        Index all documents in a KB directory.
        Returns count of documents indexed by type.
        """
        if directory is None:
            directory = self.KB_ROOT
        else:
            directory = Path(directory)
        
        counts = {}
        
        for filepath in directory.rglob('*.md'):
            doc_type = self._infer_document_type(filepath)
            
            try:
                self.ingest_document(str(filepath), doc_type)
                counts[doc_type.value] = counts.get(doc_type.value, 0) + 1
            except Exception as e:
                print(f"Error indexing {filepath}: {e}")
        
        return counts
    
    def _infer_document_type(self, filepath: Path) -> DocumentType:
        """Infer document type from file path"""
        path_str = str(filepath).lower()
        
        if 'normativa' in path_str or 'cff' in path_str or 'lisr' in path_str:
            return DocumentType.LEGAL_CODE
        elif 'jurisprudencia' in path_str or 'tesis' in path_str:
            return DocumentType.JURISPRUDENCE
        elif 'criterios' in path_str:
            return DocumentType.CRITERIA_SAT
        elif 'tipologia' in path_str:
            return DocumentType.CASE_REFERENCE
        elif 'pilares' in path_str or 'efos' in path_str:
            return DocumentType.TEMPLATE
        elif 'glosario' in path_str:
            return DocumentType.GLOSSARY
        else:
            return DocumentType.GENERAL
    
    def get_stats(self) -> Dict[str, Any]:
        """Get KB statistics"""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "total_tokens": sum(c.token_count or 0 for c in self.chunks),
            "documents_by_type": {
                doc_type.value: sum(1 for d in self.documents.values() if d.document_type == doc_type)
                for doc_type in DocumentType
            },
            "documents_by_status": {
                status.value: sum(1 for d in self.documents.values() if d.status == status)
                for status in DocumentStatus
            }
        }
