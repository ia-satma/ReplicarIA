import os
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

CHUNK_CONFIG = {
    'marco_legal': {'strategy': 'by_article', 'min_tokens': 300, 'max_tokens': 800, 'overlap': 50},
    'jurisprudencias': {'strategy': 'semantic', 'min_tokens': 500, 'max_tokens': 1200, 'overlap': 100},
    'criterios_sat': {'strategy': 'by_criterio', 'min_tokens': 400, 'max_tokens': 1000, 'overlap': 50},
    'catalogos_sat': {'strategy': 'by_entry', 'min_tokens': 100, 'max_tokens': 500, 'overlap': 0},
    'casos_referencia': {'strategy': 'semantic', 'min_tokens': 400, 'max_tokens': 1000, 'overlap': 100},
    'glosarios': {'strategy': 'by_term', 'min_tokens': 50, 'max_tokens': 300, 'overlap': 0},
    'plantillas': {'strategy': 'full_document', 'min_tokens': 100, 'max_tokens': 2000, 'overlap': 0}
}

CATEGORIA_AGENTES = {
    'cff': ['A3', 'A4', 'A7'],
    'lisr': ['A3', 'A5', 'A7'],
    'liva': ['A3', 'A5'],
    'rcff': ['A3', 'A4'],
    'rlisr': ['A3', 'A5'],
    'rmf': ['A3', 'A6'],
    'razon_negocios': ['A1', 'A3', 'A7'],
    'efos': ['A3', 'A6', 'A7'],
    'materialidad': ['A3', 'A6', 'A7'],
    'deducciones': ['A3', 'A5', 'A7'],
    'criterios_normativos': ['A3', 'A6'],
    'criterios_no_vinculativos': ['A3', 'A6'],
    'c_claveprodserv': ['A3', 'A6'],
    'lista_69b': ['A6', 'A7'],
    'lista_69b_bis': ['A6', 'A7'],
    'general': ['A3']
}

class DocumentProcessor:
    def __init__(self, session_factory, anthropic_client=None):
        self.session_factory = session_factory
        self.anthropic = anthropic_client
        from .embeddings_service import embeddings_service
        self.embeddings_service = embeddings_service
    
    async def extract_text(self, file_content: bytes, filename: str) -> str:
        extension = filename.split('.')[-1].lower()
        
        if extension == 'txt' or extension == 'md':
            return file_content.decode('utf-8', errors='ignore')
        
        elif extension == 'pdf':
            try:
                import io
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
                except ImportError:
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() or ""
                        return text
                    except ImportError:
                        logger.warning("No PDF library available")
                        return f"[PDF: {filename} - Install pypdf for text extraction]"
            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
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
                return f"[DOCX: {filename} - Install python-docx for text extraction]"
            except Exception as e:
                logger.error(f"Error extracting DOCX: {e}")
                return ""
        
        return file_content.decode('utf-8', errors='ignore')
    
    async def clasificar_documento(self, texto: str, categoria_hint: str, filename: str) -> Dict[str, Any]:
        if self.anthropic:
            try:
                response = self.anthropic.messages.create(
                    model='claude-sonnet-4-5',
                    max_tokens=2000,
                    messages=[{
                        'role': 'user',
                        'content': f'''Analiza este documento fiscal mexicano y extrae su metadata.

NOMBRE ARCHIVO: {filename}
CATEGORÍA SUGERIDA: {categoria_hint}

PRIMEROS 3000 CARACTERES:
{texto[:3000]}

Responde SOLO en JSON válido:
{{
  "categoria": "marco_legal|jurisprudencias|criterios_sat|catalogos_sat|casos_referencia|glosarios|plantillas",
  "subcategoria": "cff|lisr|liva|rcff|rmf|razon_negocios|efos|materialidad|deducciones|lista_69b|c_claveprodserv|general",
  "version": "v2025.01 o similar si es ley, null si no aplica",
  "esVigente": true,
  "fechaVigencia": null,
  "fechaPublicacion": null,
  "fuente": "DOF|SAT|SCJN|PRODECON|IMCP|otro",
  "metadata": {{
    "titulo": "Título completo del documento",
    "articulos_principales": [],
    "temas_clave": [],
    "resumen_ejecutivo": "Una oración describiendo el documento"
  }}
}}'''
                    }]
                )
                content = response.content[0]
                if hasattr(content, 'text'):
                    json_match = re.search(r'\{[\s\S]*\}', content.text)
                    if json_match:
                        return json.loads(json_match.group())
            except Exception as e:
                logger.error(f"Error clasificando con Claude: {e}")
        
        return {
            "categoria": categoria_hint or "casos_referencia",
            "subcategoria": "general",
            "version": None,
            "esVigente": True,
            "fechaVigencia": None,
            "fechaPublicacion": None,
            "fuente": "otro",
            "metadata": {
                "titulo": filename,
                "articulos_principales": [],
                "temas_clave": [],
                "resumen_ejecutivo": f"Documento: {filename}"
            }
        }
    
    def chunk_document_simple(self, texto: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        max_chars = config.get('max_tokens', 800) * 4
        min_chars = config.get('min_tokens', 300) * 4
        overlap_chars = config.get('overlap', 50) * 4
        
        chunks = []
        paragraphs = texto.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if len(current_chunk) >= min_chars:
                    chunks.append({
                        "contenido": current_chunk.strip(),
                        "tokens": len(current_chunk) // 4,
                        "metadata": {}
                    })
                    overlap_text = current_chunk[-overlap_chars:] if overlap_chars > 0 else ""
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk += para + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                "contenido": current_chunk.strip(),
                "tokens": len(current_chunk) // 4,
                "metadata": {}
            })
        
        if not chunks and texto.strip():
            chunks.append({
                "contenido": texto.strip()[:max_chars],
                "tokens": min(len(texto), max_chars) // 4,
                "metadata": {}
            })
        
        return chunks
    
    def determinar_agentes(self, subcategoria: str, metadata: Dict[str, Any]) -> List[str]:
        agentes_base = CATEGORIA_AGENTES.get(subcategoria, CATEGORIA_AGENTES['general'])
        agentes = set(agentes_base)
        
        contenido_lower = json.dumps(metadata).lower()
        
        if '69-b' in contenido_lower or 'efos' in contenido_lower:
            agentes.add('A6')
            agentes.add('A7')
        if 'razón de negocios' in contenido_lower or 'sustancia económica' in contenido_lower:
            agentes.add('A1')
            agentes.add('A7')
        if 'deducción' in contenido_lower or 'deducible' in contenido_lower:
            agentes.add('A3')
            agentes.add('A5')
        if 'contrato' in contenido_lower or 'cláusula' in contenido_lower:
            agentes.add('A4')
        
        return list(agentes)
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        categoria: str,
        empresa_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        errors = []
        metadata = metadata or {}
        
        texto = await self.extract_text(file_content, filename)
        if not texto.strip():
            raise ValueError(f"No se pudo extraer texto del documento: {filename}")
        
        hash_contenido = hashlib.sha256(texto.encode()).hexdigest()
        
        async with self.session_factory() as session:
            result = await session.execute(
                text('SELECT id FROM kb_documentos WHERE hash_contenido = :hash'),
                {'hash': hash_contenido}
            )
            existing = result.fetchone()
            
            if existing:
                raise ValueError(f"Documento duplicado. Ya existe con ID: {existing[0]}")
            
            clasificacion = await self.clasificar_documento(texto, categoria, filename)
            extension = filename.split('.')[-1].lower()
            
            fecha_vigencia = None
            fecha_publicacion = None
            if clasificacion.get('fechaVigencia'):
                try:
                    fecha_vigencia = datetime.fromisoformat(clasificacion['fechaVigencia'])
                except:
                    pass
            if clasificacion.get('fechaPublicacion'):
                try:
                    fecha_publicacion = datetime.fromisoformat(clasificacion['fechaPublicacion'])
                except:
                    pass
            
            doc_result = await session.execute(
                text('''
                    INSERT INTO kb_documentos (
                        nombre, tipo_archivo, categoria, subcategoria, version,
                        es_version_vigente, fecha_vigencia, fecha_publicacion, fuente,
                        hash_contenido, tamaño_bytes, estado, metadata, empresa_id
                    ) VALUES (
                        :nombre, :tipo, :cat, :subcat, :version,
                        :vigente, :fvig, :fpub, :fuente,
                        :hash, :size, 'procesando', :meta, :empresa
                    )
                    RETURNING id
                '''),
                {
                    'nombre': filename,
                    'tipo': extension,
                    'cat': clasificacion.get('categoria'),
                    'subcat': clasificacion.get('subcategoria'),
                    'version': clasificacion.get('version'),
                    'vigente': clasificacion.get('esVigente', True),
                    'fvig': fecha_vigencia,
                    'fpub': fecha_publicacion,
                    'fuente': clasificacion.get('fuente'),
                    'hash': hash_contenido,
                    'size': len(file_content),
                    'meta': json.dumps({**metadata, **clasificacion.get('metadata', {})}),
                    'empresa': empresa_id
                }
            )
            await session.commit()
            
            doc_row = doc_result.fetchone()
            documento_id = str(doc_row[0])
            
            config = CHUNK_CONFIG.get(categoria, CHUNK_CONFIG['casos_referencia'])
            chunks = self.chunk_document_simple(texto, config)
            
            agentes_notificados = set()
            chunks_creados = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    embedding = await self.embeddings_service.generate_embedding(chunk['contenido'])
                    agentes = self.determinar_agentes(clasificacion.get('subcategoria', 'general'), chunk.get('metadata', {}))
                    for a in agentes:
                        agentes_notificados.add(a)
                    
                    score_calidad = 70.0
                    
                    chunk_result = await session.execute(
                        text('''
                            INSERT INTO kb_chunks (
                                documento_id, contenido, contenido_embedding, chunk_index,
                                tokens, metadata, categoria_chunk, agentes_asignados, score_calidad
                            ) VALUES (
                                :doc_id, :contenido, :embedding, :idx,
                                :tokens, :meta, :cat, :agentes, :score
                            )
                            RETURNING id
                        '''),
                        {
                            'doc_id': doc_row[0],
                            'contenido': chunk['contenido'],
                            'embedding': str(embedding) if embedding else None,
                            'idx': i,
                            'tokens': chunk.get('tokens', 0),
                            'meta': json.dumps(chunk.get('metadata', {})),
                            'cat': clasificacion.get('subcategoria'),
                            'agentes': agentes,
                            'score': score_calidad
                        }
                    )
                    await session.commit()
                    
                    chunk_row = chunk_result.fetchone()
                    
                    for agente in agentes:
                        await session.execute(
                            text('''
                                INSERT INTO kb_chunk_agente (chunk_id, agente_id, relevancia)
                                VALUES (:chunk_id, :agente, 1.0)
                            '''),
                            {'chunk_id': chunk_row[0], 'agente': agente}
                        )
                    await session.commit()
                    
                    chunks_creados += 1
                except Exception as e:
                    logger.error(f"Error procesando chunk {i}: {e}")
                    errors.append(str(e))
            
            await session.execute(
                text('''
                    UPDATE kb_documentos SET estado = 'procesado', updated_at = NOW()
                    WHERE id = :doc_id
                '''),
                {'doc_id': doc_row[0]}
            )
            
            if clasificacion.get('categoria') == 'marco_legal' and clasificacion.get('esVigente'):
                await session.execute(
                    text('''
                        UPDATE kb_documentos SET es_version_vigente = FALSE
                        WHERE categoria = 'marco_legal' 
                        AND subcategoria = :subcat 
                        AND id != :doc_id
                    '''),
                    {'subcat': clasificacion.get('subcategoria'), 'doc_id': doc_row[0]}
                )
            
            await session.commit()
        
        return {
            "documento_id": documento_id,
            "chunks": chunks_creados,
            "agentes_notificados": list(agentes_notificados),
            "errores": errors,
            "clasificacion": clasificacion
        }
    
    async def get_kb_stats(self, empresa_id: Optional[str] = None) -> Dict[str, Any]:
        async with self.session_factory() as session:
            if empresa_id:
                stats_result = await session.execute(
                    text('''
                        SELECT 
                            COUNT(DISTINCT d.id) as total_documentos,
                            COALESCE(COUNT(c.id), 0) as total_chunks,
                            COALESCE(AVG(c.score_calidad), 0) as promedio_calidad
                        FROM kb_documentos d
                        LEFT JOIN kb_chunks c ON c.documento_id = d.id
                        WHERE d.empresa_id = :empresa
                    '''),
                    {'empresa': empresa_id}
                )
            else:
                stats_result = await session.execute(
                    text('''
                        SELECT 
                            COUNT(DISTINCT d.id) as total_documentos,
                            COALESCE(COUNT(c.id), 0) as total_chunks,
                            COALESCE(AVG(c.score_calidad), 0) as promedio_calidad
                        FROM kb_documentos d
                        LEFT JOIN kb_chunks c ON c.documento_id = d.id
                    ''')
                )
            
            stats = stats_result.fetchone()
            
            cat_result = await session.execute(
                text('SELECT categoria, COUNT(*) as cnt FROM kb_documentos GROUP BY categoria')
            )
            por_categoria = {row[0]: row[1] for row in cat_result.fetchall() if row[0]}
            
            completitud = await self.calcular_completitud(session)
            alertas = await self.get_alertas(session)
            
            return {
                "total_documentos": stats[0] or 0,
                "total_chunks": stats[1] or 0,
                "promedio_calidad": float(stats[2] or 0),
                "por_categoria": por_categoria,
                "completitud": completitud,
                "alertas": alertas
            }
    
    async def calcular_completitud(self, session) -> Dict[str, float]:
        requisitos = {
            'marco_legal': ['cff', 'lisr', 'liva', 'rcff', 'rlisr', 'rmf'],
            'jurisprudencias': ['razon_negocios', 'efos', 'materialidad', 'deducciones'],
            'criterios_sat': ['criterios_normativos', 'criterios_no_vinculativos'],
            'catalogos_sat': ['c_claveprodserv', 'lista_69b'],
            'casos_referencia': [],
            'glosarios': ['glosario_fiscal'],
            'plantillas': ['defensa', 'contratos']
        }
        
        completitud = {}
        
        for cat, reqs in requisitos.items():
            if not reqs:
                result = await session.execute(
                    text('SELECT COUNT(*) FROM kb_documentos WHERE categoria = :cat'),
                    {'cat': cat}
                )
                count = result.scalar() or 0
                completitud[cat] = min(100, (count / 5) * 100)
            else:
                result = await session.execute(
                    text('SELECT DISTINCT subcategoria FROM kb_documentos WHERE categoria = :cat'),
                    {'cat': cat}
                )
                subcats = [row[0] for row in result.fetchall() if row[0]]
                cumplidos = len([r for r in reqs if r in subcats])
                completitud[cat] = (cumplidos / len(reqs)) * 100
        
        valores = list(completitud.values())
        completitud['general'] = sum(valores) / len(valores) if valores else 0
        
        return completitud
    
    async def get_alertas(self, session) -> List[Dict[str, Any]]:
        alertas = []
        
        result = await session.execute(
            text('''
                SELECT updated_at FROM kb_documentos 
                WHERE subcategoria = 'lista_69b' 
                ORDER BY updated_at DESC LIMIT 1
            ''')
        )
        lista69b = result.fetchone()
        
        if not lista69b:
            alertas.append({
                'tipo': 'critica',
                'mensaje': 'No existe lista 69-B en el sistema. A6 Proveedor no puede verificar EFOS.',
                'categoria': 'catalogos_sat'
            })
        elif lista69b[0]:
            dias_antiguedad = (datetime.now() - lista69b[0].replace(tzinfo=None)).days
            if dias_antiguedad > 15:
                alertas.append({
                    'tipo': 'alta',
                    'mensaje': f'Lista 69-B tiene {dias_antiguedad} días de antigüedad. El SAT actualiza cada 2 semanas.',
                    'categoria': 'catalogos_sat'
                })
        
        año_actual = datetime.now().year
        result = await session.execute(
            text('SELECT version FROM kb_documentos WHERE subcategoria = :sub AND version LIKE :year'),
            {'sub': 'rmf', 'year': f'%{año_actual}%'}
        )
        rmf = result.fetchone()
        
        if not rmf:
            alertas.append({
                'tipo': 'alta',
                'mensaje': f'No existe RMF {año_actual}. Puede haber criterios desactualizados.',
                'categoria': 'marco_legal'
            })
        
        return alertas
    
    async def search_kb(
        self,
        query: str,
        agente_id: Optional[str] = None,
        categoria: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embeddings_service.generate_embedding(query)
        
        async with self.session_factory() as session:
            await session.execute(
                text('INSERT INTO kb_search_log (query, agente_id, results_count) VALUES (:q, :a, 0)'),
                {'q': query, 'a': agente_id}
            )
            await session.commit()
            
            where_parts = ["d.estado = 'procesado'"]
            params = {'limit': limit}
            
            if agente_id:
                where_parts.append(":agente = ANY(c.agentes_asignados)")
                params['agente'] = agente_id
            
            if categoria:
                where_parts.append("d.categoria = :cat")
                params['cat'] = categoria
            
            where_sql = " AND ".join(where_parts)
            
            if query_embedding:
                params['embedding'] = str(query_embedding)
                sql = f'''
                    SELECT 
                        c.id,
                        c.contenido,
                        c.metadata,
                        d.nombre as documento,
                        d.version,
                        d.categoria,
                        d.subcategoria
                    FROM kb_chunks c
                    JOIN kb_documentos d ON d.id = c.documento_id
                    WHERE {where_sql}
                    ORDER BY c.created_at DESC
                    LIMIT :limit
                '''
            else:
                sql = f'''
                    SELECT 
                        c.id,
                        c.contenido,
                        c.metadata,
                        d.nombre as documento,
                        d.version,
                        d.categoria,
                        d.subcategoria
                    FROM kb_chunks c
                    JOIN kb_documentos d ON d.id = c.documento_id
                    WHERE {where_sql}
                    ORDER BY c.created_at DESC
                    LIMIT :limit
                '''
            
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            
            return [{
                "id": str(row[0]),
                "contenido": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "documento": row[3],
                "version": row[4],
                "categoria": row[5],
                "subcategoria": row[6],
                "similarity": 0.8
            } for row in rows]
