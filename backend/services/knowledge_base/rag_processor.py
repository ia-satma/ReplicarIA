"""
RAG Processor for Bibliotecar.IA
Complete RAG document processing system with Claude classification,
intelligent chunking, embeddings, and agent assignment.
"""
import os
import re
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text

logger = logging.getLogger(__name__)

LEY_CODIGOS = ['CFF', 'LISR', 'LIVA', 'RCFF', 'RLISR', 'RMF', 'RIVA', 'RISR']

CATEGORIAS_VALIDAS = [
    'marco_legal', 'jurisprudencias', 'criterios_sat', 'catalogos_sat',
    'casos_referencia', 'glosarios', 'plantillas', 'efos', 'lista_69b'
]

AGENT_MAPPING = {
    'CFF': ['A1', 'A3', 'A4', 'A7'],
    'LISR': ['A3', 'A5', 'A7'],
    'LIVA': ['A3', 'A7'],
    'RCFF': ['A3', 'A4'],
    'RLISR': ['A3', 'A5'],
    'RMF': ['A3', 'A6'],
    'RIVA': ['A3', 'A7'],
    'RISR': ['A3', 'A5'],
    'jurisprudencias': ['A1', 'A3', 'A7'],
    'criterios_sat': ['A1', 'A4', 'A7'],
    'efos': ['A6', 'A7'],
    'lista_69b': ['A6', 'A7'],
    'materialidad': ['A3', 'A6', 'A7'],
    'razon_negocios': ['A1', 'A3', 'A7'],
    'deducciones': ['A3', 'A5', 'A7'],
    'general': ['A3']
}

CHUNK_CONFIG = {
    'marco_legal': {'strategy': 'by_article', 'min_chars': 500, 'max_chars': 3000, 'overlap': 100},
    'jurisprudencias': {'strategy': 'semantic', 'min_chars': 800, 'max_chars': 4000, 'overlap': 200},
    'criterios_sat': {'strategy': 'by_criterio', 'min_chars': 600, 'max_chars': 3500, 'overlap': 150},
    'catalogos_sat': {'strategy': 'by_entry', 'min_chars': 200, 'max_chars': 1500, 'overlap': 0},
    'casos_referencia': {'strategy': 'semantic', 'min_chars': 600, 'max_chars': 3500, 'overlap': 200},
    'glosarios': {'strategy': 'by_term', 'min_chars': 100, 'max_chars': 800, 'overlap': 0},
    'plantillas': {'strategy': 'full_document', 'min_chars': 200, 'max_chars': 6000, 'overlap': 0},
    'efos': {'strategy': 'semantic', 'min_chars': 500, 'max_chars': 3000, 'overlap': 100},
    'lista_69b': {'strategy': 'by_entry', 'min_chars': 100, 'max_chars': 1000, 'overlap': 0}
}


class RAGProcessor:
    """Main RAG processor for document ingestion and processing."""
    
    def __init__(self, session_factory, anthropic_client=None):
        self.session_factory = session_factory
        self.anthropic = anthropic_client
        from .embeddings_service import embeddings_service
        self.embeddings_service = embeddings_service
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        categoria_hint: str = 'casos_referencia',
        empresa_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing a document through the RAG pipeline.
        
        1. Extract text from document
        2. Classify document using Claude
        3. Identify law codes
        4. Create intelligent chunks
        5. Generate embeddings
        6. Assign chunks to agents
        7. Save to PostgreSQL
        8. Update metrics
        """
        result = {
            'success': False,
            'documento_id': None,
            'chunks_created': 0,
            'agents_notified': [],
            'categoria': None,
            'ley_codigo': None,
            'errors': []
        }
        
        try:
            texto = await self._extract_text(file_content, filename)
            if not texto or len(texto.strip()) < 50:
                raise ValueError(f"No se pudo extraer texto suficiente del documento: {filename}")
            
            hash_contenido = hashlib.sha256(texto.encode()).hexdigest()
            
            async with self.session_factory() as session:
                existing = await session.execute(
                    text('SELECT id FROM kb_documentos WHERE hash_contenido = :hash'),
                    {'hash': hash_contenido}
                )
                if existing.fetchone():
                    raise ValueError("Documento duplicado - ya existe en la base de conocimiento")
            
            clasificacion = await self._clasificar_documento(texto, filename, categoria_hint)
            result['categoria'] = clasificacion.get('categoria', categoria_hint)
            result['ley_codigo'] = clasificacion.get('ley_codigo')
            
            chunks = await self._crear_chunks_inteligentes(texto, clasificacion)
            
            embeddings = await self.embeddings_service.generate_embeddings_batch(
                [c['contenido'] for c in chunks]
            )
            
            for i, chunk in enumerate(chunks):
                if embeddings and i < len(embeddings) and embeddings[i]:
                    chunk['embedding'] = embeddings[i]
            
            for chunk in chunks:
                chunk['agentes'] = self._asignar_agentes(
                    chunk['contenido'],
                    clasificacion
                )
                result['agents_notified'].extend(chunk['agentes'])
            
            seen_agents = set()
            unique_agents = []
            for agent in result['agents_notified']:
                agent_id = agent.get('agente_id') if isinstance(agent, dict) else agent
                if agent_id not in seen_agents:
                    seen_agents.add(agent_id)
                    unique_agents.append(agent)
            result['agents_notified'] = unique_agents
            
            documento_id = await self._guardar_en_postgres(
                texto=texto,
                filename=filename,
                hash_contenido=hash_contenido,
                clasificacion=clasificacion,
                chunks=chunks,
                empresa_id=empresa_id,
                metadata=metadata
            )
            
            result['documento_id'] = documento_id
            result['chunks_created'] = len(chunks)
            
            await self._actualizar_metricas()
            
            result['success'] = True
            logger.info(f"Document processed: {filename}, {len(chunks)} chunks, agents: {result['agents_notified']}")
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            result['errors'].append(str(e))
        
        return result
    
    async def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from various document formats."""
        extension = filename.split('.')[-1].lower()
        
        if extension in ['txt', 'md']:
            return file_content.decode('utf-8', errors='ignore')
        
        elif extension == 'pdf':
            try:
                import io
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                    return text
                except ImportError:
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        text = ""
                        for page in reader.pages:
                            page_text = page.extract_text() or ""
                            text += page_text + "\n"
                        return text
                    except ImportError:
                        logger.warning("No PDF library available")
                        return f"[PDF: {filename} - Requiere instalación de pypdf]"
            except Exception as e:
                logger.error(f"Error extracting PDF text: {e}")
                return ""
        
        elif extension == 'docx':
            try:
                import io
                from docx import Document
                doc = Document(io.BytesIO(file_content))
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                logger.warning("python-docx not installed")
                return f"[DOCX: {filename} - Requiere instalación de python-docx]"
            except Exception as e:
                logger.error(f"Error extracting DOCX text: {e}")
                return ""
        
        return file_content.decode('utf-8', errors='ignore')
    
    async def _clasificar_documento(
        self,
        texto: str,
        filename: str,
        categoria_hint: str
    ) -> Dict[str, Any]:
        """Classify document using Claude AI."""
        
        ley_codigo = None
        for codigo in LEY_CODIGOS:
            if codigo.lower() in filename.lower() or codigo.lower() in texto[:5000].lower():
                ley_codigo = codigo
                break
        
        if self.anthropic:
            try:
                response = self.anthropic.messages.create(
                    model='claude-sonnet-4-5',
                    max_tokens=2000,
                    messages=[{
                        'role': 'user',
                        'content': f'''Analiza este documento fiscal mexicano y clasifícalo.

NOMBRE ARCHIVO: {filename}
CATEGORÍA SUGERIDA: {categoria_hint}

PRIMEROS 4000 CARACTERES:
{texto[:4000]}

Responde SOLO en JSON válido:
{{
    "categoria": "marco_legal|jurisprudencias|criterios_sat|catalogos_sat|casos_referencia|glosarios|plantillas|efos|lista_69b",
    "subcategoria": "cff|lisr|liva|rcff|rlisr|rmf|razon_negocios|efos|materialidad|deducciones|lista_69b|general",
    "ley_codigo": "CFF|LISR|LIVA|RCFF|RLISR|RMF|null",
    "version": "2024|2025 o null si no aplica",
    "es_vigente": true,
    "fuente": "DOF|SAT|SCJN|PRODECON|IMCP|TFJA|otro",
    "metadata": {{
        "titulo": "Título del documento",
        "articulos_principales": ["5-A", "69-B", "27"],
        "temas_clave": ["razón de negocios", "materialidad", "efos"],
        "resumen": "Breve descripción del documento"
    }}
}}'''
                    }]
                )
                
                content = response.content[0]
                if hasattr(content, 'text'):
                    json_match = re.search(r'\{[\s\S]*\}', content.text)
                    if json_match:
                        result = json.loads(json_match.group())
                        if not result.get('ley_codigo') and ley_codigo:
                            result['ley_codigo'] = ley_codigo
                        return result
                        
            except Exception as e:
                logger.error(f"Error classifying with Claude: {e}")
        
        return {
            'categoria': categoria_hint or 'casos_referencia',
            'subcategoria': 'general',
            'ley_codigo': ley_codigo,
            'version': None,
            'es_vigente': True,
            'fuente': 'otro',
            'metadata': {
                'titulo': filename,
                'articulos_principales': [],
                'temas_clave': [],
                'resumen': f'Documento: {filename}'
            }
        }
    
    async def _crear_chunks_inteligentes(
        self,
        texto: str,
        clasificacion: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create intelligent chunks based on document type."""
        
        categoria = clasificacion.get('categoria', 'casos_referencia')
        config = CHUNK_CONFIG.get(categoria, CHUNK_CONFIG['casos_referencia'])
        strategy = config['strategy']
        
        if strategy == 'by_article':
            return self._chunk_by_articles(texto, config, clasificacion)
        elif strategy == 'by_criterio':
            return self._chunk_by_criterio(texto, config)
        elif strategy == 'by_entry':
            return self._chunk_by_entry(texto, config)
        elif strategy == 'by_term':
            return self._chunk_by_term(texto, config)
        elif strategy == 'full_document':
            return self._chunk_full_document(texto, config)
        else:
            return self._chunk_semantic(texto, config)
    
    def _chunk_by_articles(
        self,
        texto: str,
        config: Dict[str, Any],
        clasificacion: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk legal documents by article structure."""
        chunks = []
        
        article_pattern = r'(Artículo\s+\d+[-A-Z]?[.-]?\s*[A-Z]?\.?)'
        parts = re.split(article_pattern, texto, flags=re.IGNORECASE)
        
        if len(parts) <= 1:
            return self._chunk_semantic(texto, config)
        
        current_article = None
        current_content = ""
        
        for i, part in enumerate(parts):
            if re.match(article_pattern, part, re.IGNORECASE):
                if current_content.strip():
                    chunks.append({
                        'contenido': current_content.strip(),
                        'articulo': current_article,
                        'tipo_contenido': 'articulo',
                        'tokens': len(current_content) // 4,
                        'metadata': {
                            'ley_codigo': clasificacion.get('ley_codigo'),
                            'articulo': current_article
                        }
                    })
                current_article = part.strip()
                current_content = part
            else:
                current_content += part
                
                if len(current_content) > config['max_chars']:
                    sub_chunks = self._split_long_content(current_content, config, current_article)
                    chunks.extend(sub_chunks)
                    current_content = ""
        
        if current_content.strip():
            chunks.append({
                'contenido': current_content.strip(),
                'articulo': current_article,
                'tipo_contenido': 'articulo',
                'tokens': len(current_content) // 4,
                'metadata': {
                    'ley_codigo': clasificacion.get('ley_codigo'),
                    'articulo': current_article
                }
            })
        
        return chunks if chunks else self._chunk_semantic(texto, config)
    
    def _chunk_by_criterio(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk SAT criteria documents."""
        chunks = []
        
        criterio_pattern = r'((?:Criterio|CRITERIO)\s+\d+[/.]\d+[/.]\d+)'
        parts = re.split(criterio_pattern, texto, flags=re.IGNORECASE)
        
        if len(parts) <= 1:
            return self._chunk_semantic(texto, config)
        
        current_criterio = None
        current_content = ""
        
        for part in parts:
            if re.match(criterio_pattern, part, re.IGNORECASE):
                if current_content.strip():
                    chunks.append({
                        'contenido': current_content.strip(),
                        'tipo_contenido': 'criterio',
                        'tokens': len(current_content) // 4,
                        'metadata': {'criterio': current_criterio}
                    })
                current_criterio = part.strip()
                current_content = part
            else:
                current_content += part
        
        if current_content.strip():
            chunks.append({
                'contenido': current_content.strip(),
                'tipo_contenido': 'criterio',
                'tokens': len(current_content) // 4,
                'metadata': {'criterio': current_criterio}
            })
        
        return chunks if chunks else self._chunk_semantic(texto, config)
    
    def _chunk_by_entry(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk catalog entries (like Lista 69-B)."""
        chunks = []
        
        lines = texto.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) > config['max_chars']:
                if current_chunk.strip():
                    chunks.append({
                        'contenido': current_chunk.strip(),
                        'tipo_contenido': 'entrada_catalogo',
                        'tokens': len(current_chunk) // 4,
                        'metadata': {}
                    })
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        if current_chunk.strip():
            chunks.append({
                'contenido': current_chunk.strip(),
                'tipo_contenido': 'entrada_catalogo',
                'tokens': len(current_chunk) // 4,
                'metadata': {}
            })
        
        return chunks
    
    def _chunk_by_term(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk glossary terms."""
        chunks = []
        
        term_pattern = r'\n([A-ZÁÉÍÓÚÑ][^:.\n]+):\s*'
        parts = re.split(term_pattern, texto)
        
        if len(parts) <= 1:
            return self._chunk_semantic(texto, config)
        
        i = 1
        while i < len(parts) - 1:
            term = parts[i].strip()
            definition = parts[i + 1].strip() if i + 1 < len(parts) else ""
            
            chunks.append({
                'contenido': f"{term}: {definition}",
                'tipo_contenido': 'termino_glosario',
                'tokens': len(definition) // 4,
                'metadata': {'termino': term}
            })
            i += 2
        
        return chunks if chunks else self._chunk_semantic(texto, config)
    
    def _chunk_full_document(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Keep document as single chunk if possible, otherwise split."""
        if len(texto) <= config['max_chars']:
            return [{
                'contenido': texto.strip(),
                'tipo_contenido': 'documento_completo',
                'tokens': len(texto) // 4,
                'metadata': {}
            }]
        return self._chunk_semantic(texto, config)
    
    def _chunk_semantic(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Semantic chunking by paragraphs with overlap."""
        chunks = []
        max_chars = config['max_chars']
        min_chars = config['min_chars']
        overlap = config['overlap']
        
        paragraphs = texto.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 2 < max_chars:
                current_chunk += para + "\n\n"
            else:
                if len(current_chunk) >= min_chars:
                    chunks.append({
                        'contenido': current_chunk.strip(),
                        'tipo_contenido': 'parrafo',
                        'tokens': len(current_chunk) // 4,
                        'metadata': {}
                    })
                    overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk += para + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                'contenido': current_chunk.strip(),
                'tipo_contenido': 'parrafo',
                'tokens': len(current_chunk) // 4,
                'metadata': {}
            })
        
        if not chunks and texto.strip():
            chunks.append({
                'contenido': texto[:max_chars].strip(),
                'tipo_contenido': 'fragmento',
                'tokens': min(len(texto), max_chars) // 4,
                'metadata': {}
            })
        
        return chunks
    
    def _split_long_content(
        self,
        content: str,
        config: Dict[str, Any],
        article: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Split long content into smaller chunks."""
        chunks = []
        max_chars = config['max_chars']
        overlap = config.get('overlap', 100)
        
        sentences = re.split(r'(?<=[.!?])\s+', content)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append({
                        'contenido': current_chunk.strip(),
                        'articulo': article,
                        'tipo_contenido': 'articulo_parte',
                        'tokens': len(current_chunk) // 4,
                        'metadata': {'articulo': article}
                    })
                overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk = overlap_text + sentence + " "
        
        if current_chunk.strip():
            chunks.append({
                'contenido': current_chunk.strip(),
                'articulo': article,
                'tipo_contenido': 'articulo_parte',
                'tokens': len(current_chunk) // 4,
                'metadata': {'articulo': article}
            })
        
        return chunks
    
    def _asignar_agentes(
        self,
        contenido: str,
        clasificacion: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Assign agents to a chunk based on content relevance."""
        agentes_base = set()
        
        ley_codigo = clasificacion.get('ley_codigo')
        if ley_codigo and ley_codigo in AGENT_MAPPING:
            agentes_base.update(AGENT_MAPPING[ley_codigo])
        
        categoria = clasificacion.get('categoria', 'general')
        if categoria in AGENT_MAPPING:
            agentes_base.update(AGENT_MAPPING[categoria])
        
        subcategoria = clasificacion.get('subcategoria', 'general')
        if subcategoria in AGENT_MAPPING:
            agentes_base.update(AGENT_MAPPING[subcategoria])
        
        contenido_lower = contenido.lower()
        
        keyword_agents = {
            'razón de negocios': ['A1', 'A3', 'A7'],
            'sustancia económica': ['A1', 'A3', 'A7'],
            '5-a': ['A1', 'A3', 'A7'],
            '69-b': ['A6', 'A7'],
            'efos': ['A6', 'A7'],
            'edos': ['A6', 'A7'],
            'lista negra': ['A6', 'A7'],
            'materialidad': ['A3', 'A6', 'A7'],
            'deducción': ['A3', 'A5'],
            'deducible': ['A3', 'A5'],
            'contrato': ['A4'],
            'cláusula': ['A4'],
            'nom-151': ['A4', 'A6'],
            'factura': ['A3', 'A6'],
            'cfdi': ['A3', 'A6'],
            'impuesto': ['A3'],
            'isr': ['A3', 'A5'],
            'iva': ['A3'],
            'tfja': ['A7'],
            'prodecon': ['A7'],
            'juicio': ['A7'],
            'defensa': ['A7'],
            'presupuesto': ['A5'],
            'costo': ['A5'],
            'inversión': ['A5'],
            'roi': ['A5']
        }
        
        for keyword, agents in keyword_agents.items():
            if keyword in contenido_lower:
                agentes_base.update(agents)
        
        if not agentes_base:
            agentes_base.add('A3')
        
        result = []
        for agente in agentes_base:
            score = self._calcular_relevancia(contenido, agente, clasificacion)
            is_core = score > 0.7
            result.append({
                'agente_id': agente,
                'score_relevancia': score,
                'es_conocimiento_core': is_core
            })
        
        return result
    
    def _calcular_relevancia(
        self,
        contenido: str,
        agente: str,
        clasificacion: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for agent-chunk assignment."""
        base_score = 0.5
        
        agent_focus = {
            'A1': ['razón de negocios', 'sustancia económica', 'estrategia', 'planeación'],
            'A3': ['fiscal', 'impuesto', 'deducción', 'isr', 'iva', 'cff', 'lisr', 'liva'],
            'A4': ['contrato', 'legal', 'cláusula', 'nom-151', 'acuerdo'],
            'A5': ['financiero', 'presupuesto', 'costo', 'inversión', 'roi', 'flujo'],
            'A6': ['proveedor', 'efos', '69-b', 'factura', 'cfdi', 'materialidad'],
            'A7': ['defensa', 'juicio', 'tfja', 'prodecon', 'recurso', 'litigio']
        }
        
        focus_words = agent_focus.get(agente, [])
        contenido_lower = contenido.lower()
        
        matches = sum(1 for word in focus_words if word in contenido_lower)
        if focus_words:
            base_score += (matches / len(focus_words)) * 0.3
        
        ley_codigo = clasificacion.get('ley_codigo')
        if ley_codigo:
            agent_laws = {
                'A1': ['CFF'],
                'A3': ['CFF', 'LISR', 'LIVA', 'RMF', 'RCFF', 'RLISR'],
                'A4': ['CFF', 'RCFF'],
                'A5': ['LISR', 'RLISR'],
                'A6': ['RMF', 'CFF'],
                'A7': ['CFF', 'LISR', 'LIVA']
            }
            if ley_codigo in agent_laws.get(agente, []):
                base_score += 0.2
        
        return min(base_score, 1.0)
    
    async def _guardar_en_postgres(
        self,
        texto: str,
        filename: str,
        hash_contenido: str,
        clasificacion: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        empresa_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save document and chunks to PostgreSQL."""
        
        async with self.session_factory() as session:
            extension = filename.split('.')[-1].lower()
            
            doc_result = await session.execute(
                text('''
                    INSERT INTO kb_documentos (
                        nombre, tipo_archivo, categoria, subcategoria, version,
                        es_version_vigente, fuente, hash_contenido, tamaño_bytes,
                        estado, metadata, empresa_id, ley_codigo, tipo_documento,
                        contenido_completo, total_caracteres, total_chunks, 
                        resumen, procesado, fecha_procesamiento, activo
                    ) VALUES (
                        :nombre, :tipo, :cat, :subcat, :version,
                        :vigente, :fuente, :hash, :size,
                        'procesado', :meta, :empresa, :ley, :tipo_doc,
                        :contenido, :chars, :chunks,
                        :resumen, TRUE, NOW(), TRUE
                    )
                    RETURNING id
                '''),
                {
                    'nombre': filename,
                    'tipo': extension,
                    'cat': clasificacion.get('categoria'),
                    'subcat': clasificacion.get('subcategoria'),
                    'version': clasificacion.get('version'),
                    'vigente': clasificacion.get('es_vigente', True),
                    'fuente': clasificacion.get('fuente'),
                    'hash': hash_contenido,
                    'size': len(texto.encode()),
                    'meta': json.dumps({**(metadata or {}), **clasificacion.get('metadata', {})}),
                    'empresa': empresa_id,
                    'ley': clasificacion.get('ley_codigo'),
                    'tipo_doc': clasificacion.get('categoria'),
                    'contenido': texto,
                    'chars': len(texto),
                    'chunks': len(chunks),
                    'resumen': clasificacion.get('metadata', {}).get('resumen', '')
                }
            )
            
            doc_row = doc_result.fetchone()
            documento_id = str(doc_row[0])
            
            for idx, chunk in enumerate(chunks):
                embedding = chunk.get('embedding')
                embedding_str = None
                if embedding:
                    embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                
                chunk_result = await session.execute(
                    text('''
                        INSERT INTO kb_chunks (
                            documento_id, contenido, contenido_embedding, chunk_index,
                            tokens, metadata, categoria_chunk, agentes_asignados,
                            score_calidad, articulo, tipo_contenido
                        ) VALUES (
                            :doc_id, :contenido, CAST(:embedding AS vector), :idx,
                            :tokens, :meta, :cat, :agentes,
                            :score, :articulo, :tipo
                        )
                        RETURNING id
                    '''),
                    {
                        'doc_id': documento_id,
                        'contenido': chunk['contenido'],
                        'embedding': embedding_str,
                        'idx': idx,
                        'tokens': chunk.get('tokens', 0),
                        'meta': json.dumps(chunk.get('metadata', {})),
                        'cat': clasificacion.get('categoria'),
                        'agentes': [a['agente_id'] for a in chunk.get('agentes', [])],
                        'score': 0.8,
                        'articulo': chunk.get('articulo'),
                        'tipo': chunk.get('tipo_contenido', 'parrafo')
                    }
                )
                
                chunk_row = chunk_result.fetchone()
                chunk_id = str(chunk_row[0])
                
                for agente_asig in chunk.get('agentes', []):
                    await session.execute(
                        text('''
                            INSERT INTO kb_chunk_agente (
                                chunk_id, agente_id, score_relevancia, es_conocimiento_core,
                                relevancia, usado_en_respuestas, feedback_positivo, feedback_negativo
                            ) VALUES (
                                :chunk, :agente, :score, :core,
                                :relevancia, 0, 0, 0
                            )
                            ON CONFLICT (chunk_id, agente_id) DO NOTHING
                        '''),
                        {
                            'chunk': chunk_id,
                            'agente': agente_asig['agente_id'],
                            'score': agente_asig['score_relevancia'],
                            'core': agente_asig['es_conocimiento_core'],
                            'relevancia': agente_asig['score_relevancia']
                        }
                    )
            
            await session.commit()
            return documento_id
    
    async def _actualizar_metricas(self) -> None:
        """Update metrics in kb_metricas table."""
        try:
            async with self.session_factory() as session:
                stats_result = await session.execute(text('''
                    SELECT 
                        COUNT(DISTINCT d.id) as total_docs,
                        COUNT(c.id) as total_chunks
                    FROM kb_documentos d
                    LEFT JOIN kb_chunks c ON c.documento_id = d.id
                    WHERE d.activo = TRUE OR d.activo IS NULL
                '''))
                stats = stats_result.fetchone()
                total_docs = stats[0] or 0
                total_chunks = stats[1] or 0
                
                cat_result = await session.execute(text('''
                    SELECT categoria, COUNT(*) as count
                    FROM kb_documentos
                    WHERE activo = TRUE OR activo IS NULL
                    GROUP BY categoria
                '''))
                por_categoria = {row[0]: row[1] for row in cat_result.fetchall()}
                
                agent_result = await session.execute(text('''
                    SELECT agente_id, COUNT(DISTINCT chunk_id) as count
                    FROM kb_chunk_agente
                    GROUP BY agente_id
                '''))
                por_agente = {row[0]: row[1] for row in agent_result.fetchall()}
                
                completitud = min((total_docs / 50.0) * 100, 100) if total_docs > 0 else 0
                
                await session.execute(text('''
                    INSERT INTO kb_metricas (
                        fecha, total_documentos, total_chunks, 
                        por_categoria, por_agente, completitud_general, updated_at
                    ) VALUES (
                        CURRENT_DATE, :docs, :chunks,
                        :por_cat, :por_agente, :completitud, NOW()
                    )
                    ON CONFLICT (fecha) DO UPDATE SET
                        total_documentos = :docs,
                        total_chunks = :chunks,
                        por_categoria = :por_cat,
                        por_agente = :por_agente,
                        completitud_general = :completitud,
                        updated_at = NOW()
                '''),
                {
                    'docs': total_docs,
                    'chunks': total_chunks,
                    'por_cat': json.dumps(por_categoria),
                    'por_agente': json.dumps(por_agente),
                    'completitud': completitud
                })
                
                await session.commit()
                logger.info(f"Metrics updated: {total_docs} docs, {total_chunks} chunks")
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def semantic_search(
        self,
        query: str,
        agente_id: Optional[str] = None,
        categoria: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings."""
        try:
            query_embedding = await self.embeddings_service.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Could not generate embedding for query, falling back to text search")
                return await self._text_search(query, agente_id, categoria, limit)
            
            embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"
            
            async with self.session_factory() as session:
                where_clauses = ["d.activo = TRUE OR d.activo IS NULL"]
                params = {'limit': limit}
                
                if agente_id:
                    where_clauses.append(":agente = ANY(c.agentes_asignados)")
                    params['agente'] = agente_id
                
                if categoria:
                    where_clauses.append("d.categoria = :categoria")
                    params['categoria'] = categoria
                
                where_sql = " AND ".join(where_clauses)
                
                query_vector = f"CAST('{embedding_str}' AS vector)"
                
                result = await session.execute(
                    text(f'''
                        SELECT 
                            c.id,
                            c.contenido,
                            c.articulo,
                            c.tipo_contenido,
                            d.nombre as documento,
                            d.categoria,
                            d.ley_codigo,
                            1 - (c.contenido_embedding <=> {query_vector}) as similarity
                        FROM kb_chunks c
                        JOIN kb_documentos d ON d.id = c.documento_id
                        WHERE c.contenido_embedding IS NOT NULL
                        AND ({where_sql})
                        ORDER BY c.contenido_embedding <=> {query_vector}
                        LIMIT :limit
                    '''),
                    params
                )
                
                rows = result.fetchall()
                
                return [{
                    'chunk_id': str(row[0]),
                    'contenido': row[1],
                    'articulo': row[2],
                    'tipo_contenido': row[3],
                    'documento': row[4],
                    'categoria': row[5],
                    'ley_codigo': row[6],
                    'similarity': float(row[7]) if row[7] else 0
                } for row in rows]
                
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return await self._text_search(query, agente_id, categoria, limit)
    
    async def _text_search(
        self,
        query: str,
        agente_id: Optional[str] = None,
        categoria: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fallback text-based search."""
        async with self.session_factory() as session:
            where_clauses = ["(d.activo = TRUE OR d.activo IS NULL)"]
            params = {'query': f'%{query}%', 'limit': limit}
            
            if agente_id:
                where_clauses.append(":agente = ANY(c.agentes_asignados)")
                params['agente'] = agente_id
            
            if categoria:
                where_clauses.append("d.categoria = :categoria")
                params['categoria'] = categoria
            
            where_sql = " AND ".join(where_clauses)
            
            result = await session.execute(
                text(f'''
                    SELECT 
                        c.id, c.contenido, c.articulo, c.tipo_contenido,
                        d.nombre, d.categoria, d.ley_codigo
                    FROM kb_chunks c
                    JOIN kb_documentos d ON d.id = c.documento_id
                    WHERE c.contenido ILIKE :query
                    AND {where_sql}
                    LIMIT :limit
                '''),
                params
            )
            
            return [{
                'chunk_id': str(row[0]),
                'contenido': row[1],
                'articulo': row[2],
                'tipo_contenido': row[3],
                'documento': row[4],
                'categoria': row[5],
                'ley_codigo': row[6],
                'similarity': 0.5
            } for row in result.fetchall()]
    
    async def get_stats(self, empresa_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current KB statistics from kb_metricas."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text('''
                        SELECT 
                            total_documentos, total_chunks, por_categoria,
                            por_agente, completitud_general, updated_at
                        FROM kb_metricas
                        ORDER BY fecha DESC
                        LIMIT 1
                    ''')
                )
                row = result.fetchone()
                
                if row:
                    return {
                        'total_documentos': row[0] or 0,
                        'total_chunks': row[1] or 0,
                        'por_categoria': row[2] or {},
                        'por_agente': row[3] or {},
                        'completitud': {'general': row[4] or 0},
                        'ultima_actualizacion': row[5].isoformat() if row[5] else None,
                        'alertas': []
                    }
                
                await self._actualizar_metricas()
                return await self.get_stats(empresa_id)
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_documentos': 0,
                'total_chunks': 0,
                'por_categoria': {},
                'por_agente': {},
                'completitud': {'general': 0},
                'alertas': [],
                'error': str(e)
            }


rag_processor = None

def init_rag_processor(session_factory, anthropic_client=None):
    """Initialize the global RAG processor instance."""
    global rag_processor
    rag_processor = RAGProcessor(session_factory, anthropic_client)
    return rag_processor
