"""
Knowledge Base Chunking System for RAG
Specialized chunkers for Mexican legal/fiscal documents
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ChunkType(str, Enum):
    LEGAL_ARTICLE = "legal_article"
    LEGAL_FRACTION = "legal_fraction"
    JURISPRUDENCIA_MAIN = "jurisprudencia_main"
    JURISPRUDENCIA_SUMMARY = "jurisprudencia_summary"
    CONTRACT_CLAUSE = "contract_clause"
    CRITERIA_SAT = "criteria_sat"
    DOCUMENT_SECTION = "document_section"
    FAQ_ENTRY = "faq_entry"
    GLOSSARY_TERM = "glossary_term"

class ChunkMetadata(BaseModel):
    """Metadata for a document chunk"""
    chunk_type: ChunkType
    source_document: str
    source_path: Optional[str] = None
    hierarchy_path: Optional[str] = None
    article_number: Optional[str] = None
    fraction: Optional[str] = None
    title: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    keywords: List[str] = []
    references: List[str] = []
    vigencia: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentChunk(BaseModel):
    """A chunk of document content with metadata"""
    id: Optional[str] = None
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None


class LegalDocumentChunker:
    """
    Chunking especializado para leyes y códigos fiscales mexicanos.
    Respeta la estructura: Título > Capítulo > Sección > Artículo > Fracción
    """
    
    HIERARCHY_PATTERNS = {
        'titulo': r'TÍTULO\s+([IVXLCDM]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO)',
        'capitulo': r'CAPÍTULO\s+([IVXLCDM]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO)',
        'seccion': r'SECCIÓN\s+([IVXLCDM]+|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|DÉCIMA)',
        'articulo': r'Artículo\s+(\d+[-\w]*)',
        'fraccion': r'^([IVXLCDM]+)\.\s',
        'inciso': r'^([a-z])\)\s',
    }
    
    MAX_CHUNK_TOKENS = 800
    OVERLAP_TOKENS = 100
    
    def chunk_legal_document(self, text: str, source_document: str, source_path: str = None) -> List[DocumentChunk]:
        """
        Divide un documento legal en chunks semánticos.
        
        Estrategia:
        1. Identificar estructura jerárquica
        2. Crear chunks por artículo
        3. Agregar contexto de jerarquía superior
        4. Incluir referencias cruzadas
        """
        chunks = []
        articles = self._extract_articles(text)
        
        current_titulo = ""
        current_capitulo = ""
        current_seccion = ""
        
        for article in articles:
            if article.get('titulo'):
                current_titulo = article['titulo']
            if article.get('capitulo'):
                current_capitulo = article['capitulo']
            if article.get('seccion'):
                current_seccion = article['seccion']
            
            hierarchy_path = self._build_hierarchy_path(
                current_titulo, current_capitulo, current_seccion, article['number']
            )
            
            keywords = self._extract_legal_keywords(article['text'])
            references = self._extract_references(article['text'])
            
            metadata = ChunkMetadata(
                chunk_type=ChunkType.LEGAL_ARTICLE,
                source_document=source_document,
                source_path=source_path,
                hierarchy_path=hierarchy_path,
                article_number=article['number'],
                title=current_titulo,
                chapter=current_capitulo,
                section=current_seccion,
                keywords=keywords,
                references=references
            )
            
            if len(article['text']) > 1500:
                sub_chunks = self._split_by_fractions(article, metadata, source_document)
                chunks.extend(sub_chunks)
            else:
                chunk = DocumentChunk(
                    content=article['text'],
                    metadata=metadata,
                    token_count=self._estimate_tokens(article['text'])
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_articles(self, text: str) -> List[Dict[str, Any]]:
        """Extract articles from legal text"""
        articles = []
        pattern = r'(Artículo\s+\d+[-\w]*[\.\-]?\s*[\.\-]?\s*)(.*?)(?=Artículo\s+\d+|$)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            article_header = match[0].strip()
            article_text = match[1].strip()
            
            num_match = re.search(r'Artículo\s+(\d+[-\w]*)', article_header, re.IGNORECASE)
            number = num_match.group(1) if num_match else "Unknown"
            
            articles.append({
                'number': number,
                'text': f"{article_header} {article_text}",
                'fractions': self._extract_fractions(article_text)
            })
        
        return articles
    
    def _extract_fractions(self, text: str) -> List[Dict[str, str]]:
        """Extract fractions (I, II, III, etc.) from article text"""
        fractions = []
        pattern = r'^([IVXLCDM]+)\.\s+(.*?)(?=^[IVXLCDM]+\.|$)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            fractions.append({
                'number': match[0],
                'text': match[1].strip()
            })
        
        return fractions
    
    def _split_by_fractions(self, article: Dict, base_metadata: ChunkMetadata, source_doc: str) -> List[DocumentChunk]:
        """Split large article by fractions"""
        chunks = []
        fractions = article.get('fractions', [])
        
        if not fractions:
            return [DocumentChunk(
                content=article['text'][:1500],
                metadata=base_metadata,
                token_count=self._estimate_tokens(article['text'][:1500])
            )]
        
        for frac in fractions:
            frac_metadata = base_metadata.model_copy()
            frac_metadata.chunk_type = ChunkType.LEGAL_FRACTION
            frac_metadata.fraction = frac['number']
            
            content = f"Artículo {article['number']}, Fracción {frac['number']}:\n{frac['text']}"
            
            chunks.append(DocumentChunk(
                content=content,
                metadata=frac_metadata,
                token_count=self._estimate_tokens(content)
            ))
        
        return chunks
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract references to other articles"""
        references = []
        patterns = [
            r'artículo\s+(\d+[-\w]*)',
            r'artículos\s+([\d,\s\-y]+)',
            r'fracción\s+([IVXLCDM]+)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        return list(set(references))
    
    def _extract_legal_keywords(self, text: str) -> List[str]:
        """Extract legal keywords from text"""
        keywords = []
        legal_terms = [
            'deducción', 'deducible', 'acreditamiento', 'retención', 'entero',
            'comprobante', 'CFDI', 'factura', 'contribuyente', 'declaración',
            'impuesto', 'ISR', 'IVA', 'obligación', 'requisito', 'procedimiento',
            'sanción', 'multa', 'determinación', 'fiscalización', 'auditoría',
            'razón de negocios', 'materialidad', 'simulación', 'EFOS', '69-B',
            'proveedor', 'operación', 'inexistente', 'presunción'
        ]
        text_lower = text.lower()
        for term in legal_terms:
            if term.lower() in text_lower:
                keywords.append(term)
        return keywords
    
    def _build_hierarchy_path(self, titulo: str, capitulo: str, seccion: str, articulo: str) -> str:
        """Build hierarchy path string"""
        parts = []
        if titulo:
            parts.append(f"Título {titulo}")
        if capitulo:
            parts.append(f"Capítulo {capitulo}")
        if seccion:
            parts.append(f"Sección {seccion}")
        parts.append(f"Artículo {articulo}")
        return " > ".join(parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (roughly 4 chars per token for Spanish)"""
        return len(text) // 4


class JurisprudenceChunker:
    """
    Chunking especializado para tesis y jurisprudencias.
    Estructura: Rubro > Texto > Precedentes > Datos de localización
    """
    
    MAX_CHUNK_TOKENS = 1200
    OVERLAP_TOKENS = 150
    
    def chunk_jurisprudence(self, text: str, source_document: str, source_path: str = None) -> List[DocumentChunk]:
        """
        Divide una jurisprudencia en chunks significativos.
        
        Genera múltiples chunks por jurisprudencia:
        1. Chunk principal: Rubro + Texto completo
        2. Chunk de resumen: Extracto clave
        """
        chunks = []
        
        rubro = self._extract_rubro(text)
        texto_tesis = self._extract_texto_tesis(text)
        datos_localizacion = self._extract_localizacion(text)
        
        main_content = f"{rubro}\n\n{texto_tesis}"
        
        main_metadata = ChunkMetadata(
            chunk_type=ChunkType.JURISPRUDENCIA_MAIN,
            source_document=source_document,
            source_path=source_path,
            title=rubro[:200] if rubro else None,
            keywords=self._extract_legal_concepts(texto_tesis),
            references=self._extract_article_mentions(texto_tesis)
        )
        
        chunks.append(DocumentChunk(
            content=main_content,
            metadata=main_metadata,
            token_count=self._estimate_tokens(main_content)
        ))
        
        resumen = self._generate_summary(rubro, texto_tesis)
        
        summary_metadata = main_metadata.model_copy()
        summary_metadata.chunk_type = ChunkType.JURISPRUDENCIA_SUMMARY
        
        chunks.append(DocumentChunk(
            content=resumen,
            metadata=summary_metadata,
            token_count=self._estimate_tokens(resumen)
        ))
        
        return chunks
    
    def _extract_rubro(self, text: str) -> str:
        """Extract the rubro (heading) from jurisprudence"""
        lines = text.split('\n')
        rubro_lines = []
        for line in lines:
            line = line.strip()
            if line and line.isupper():
                rubro_lines.append(line)
            elif rubro_lines:
                break
        return ' '.join(rubro_lines)
    
    def _extract_texto_tesis(self, text: str) -> str:
        """Extract the main thesis text"""
        lines = text.split('\n')
        in_text = False
        text_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not line.isupper() and len(line) > 50:
                in_text = True
            if in_text:
                if line.startswith('Época:') or line.startswith('Registro:'):
                    break
                text_lines.append(line)
        
        return ' '.join(text_lines)
    
    def _extract_localizacion(self, text: str) -> Dict[str, str]:
        """Extract location data from jurisprudence"""
        data = {}
        patterns = {
            'epoca': r'Época:\s*(.+)',
            'instancia': r'Instancia:\s*(.+)',
            'materia': r'Materia[s]?:\s*(.+)',
            'numero': r'Tesis:\s*(.+)',
            'registro': r'Registro:\s*(\d+)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        return data
    
    def _extract_legal_concepts(self, text: str) -> List[str]:
        """Extract legal concepts from text"""
        concepts = []
        legal_terms = [
            'deducción', 'deducibilidad', 'acreditamiento', 'materialidad',
            'razón de negocios', 'estricta indispensabilidad', 'simulación',
            'operaciones inexistentes', 'EFOS', 'presunción', 'carga de la prueba',
            'derecho humano', 'principio', 'constitucional', 'legalidad'
        ]
        text_lower = text.lower()
        for term in legal_terms:
            if term.lower() in text_lower:
                concepts.append(term)
        return concepts
    
    def _extract_article_mentions(self, text: str) -> List[str]:
        """Extract article mentions"""
        mentions = []
        patterns = [
            r'artículo\s+(\d+[-\w]*)\s+(?:del\s+)?(?:CFF|LISR|LIVA)',
            r'(?:CFF|LISR|LIVA)\s+(?:artículo\s+)?(\d+[-\w]*)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions.extend(matches)
        return list(set(mentions))
    
    def _generate_summary(self, rubro: str, texto: str) -> str:
        """Generate executive summary"""
        sentences = texto.split('.')
        key_sentence = next(
            (s for s in sentences if len(s) > 50 and any(w in s.lower() for w in ['debe', 'procede', 'resulta', 'constituye'])),
            sentences[0] if sentences else ''
        )
        return f"RESUMEN: {rubro[:150]}...\n\nCRITERIO CLAVE: {key_sentence.strip()}."
    
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class ContractChunker:
    """
    Chunking especializado para contratos.
    Divide por cláusulas manteniendo contexto.
    """
    
    MAX_CHUNK_TOKENS = 600
    OVERLAP_TOKENS = 80
    
    def chunk_contract(self, text: str, source_document: str, source_path: str = None, 
                       contract_metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Divide contract into clause-based chunks"""
        chunks = []
        clauses = self._extract_clauses(text)
        
        for clause in clauses:
            metadata = ChunkMetadata(
                chunk_type=ChunkType.CONTRACT_CLAUSE,
                source_document=source_document,
                source_path=source_path,
                title=clause.get('title', ''),
                section=clause.get('number', ''),
                keywords=self._extract_contract_keywords(clause['text'])
            )
            
            chunks.append(DocumentChunk(
                content=clause['text'],
                metadata=metadata,
                token_count=self._estimate_tokens(clause['text'])
            ))
        
        return chunks
    
    def _extract_clauses(self, text: str) -> List[Dict[str, str]]:
        """Extract clauses from contract"""
        clauses = []
        
        pattern = r'((?:CLÁUSULA|CLAUSULA|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|DÉCIMA|\d+[\.\-])\s*[\.\-:]?\s*)(.*?)(?=(?:CLÁUSULA|CLAUSULA|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|DÉCIMA|\d+[\.\-])\s*[\.\-:]|$)'
        
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches):
            clause_header = match[0].strip()
            clause_text = match[1].strip()
            
            clauses.append({
                'number': str(i + 1),
                'title': clause_header,
                'text': f"{clause_header} {clause_text}"
            })
        
        return clauses if clauses else [{'number': '1', 'title': 'Completo', 'text': text}]
    
    def _extract_contract_keywords(self, text: str) -> List[str]:
        """Extract contract-relevant keywords"""
        keywords = []
        terms = [
            'objeto', 'alcance', 'entregables', 'contraprestación', 'pago',
            'vigencia', 'plazo', 'confidencialidad', 'propiedad intelectual',
            'terminación', 'rescisión', 'penalización', 'garantía',
            'jurisdicción', 'domicilio', 'notificaciones'
        ]
        text_lower = text.lower()
        for term in terms:
            if term in text_lower:
                keywords.append(term)
        return keywords
    
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class CriteriaSATChunker:
    """Chunking for SAT criteria documents"""
    
    def chunk_criteria(self, text: str, source_document: str, is_vinculante: bool = True) -> List[DocumentChunk]:
        """Chunk SAT criteria document"""
        chunks = []
        
        pattern = r'(\d+/\d+/\w+)\s*(.*?)(?=\d+/\d+/\w+|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            criteria_num = match[0]
            criteria_text = match[1].strip()
            
            metadata = ChunkMetadata(
                chunk_type=ChunkType.CRITERIA_SAT,
                source_document=source_document,
                article_number=criteria_num,
                keywords=['criterio SAT', 'vinculante' if is_vinculante else 'no vinculativo']
            )
            
            chunks.append(DocumentChunk(
                content=f"Criterio {criteria_num}\n\n{criteria_text}",
                metadata=metadata,
                token_count=len(criteria_text) // 4
            ))
        
        return chunks


class GlossaryChunker:
    """Chunking for glossary and FAQ entries"""
    
    def chunk_glossary(self, entries: List[Dict[str, str]], source_document: str) -> List[DocumentChunk]:
        """Chunk glossary entries"""
        chunks = []
        
        for entry in entries:
            term = entry.get('term', '')
            definition = entry.get('definition', '')
            
            metadata = ChunkMetadata(
                chunk_type=ChunkType.GLOSSARY_TERM,
                source_document=source_document,
                title=term,
                keywords=[term.lower()]
            )
            
            chunks.append(DocumentChunk(
                content=f"{term}: {definition}",
                metadata=metadata,
                token_count=len(definition) // 4
            ))
        
        return chunks
