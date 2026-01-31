"""
Knowledge Base Document Processor
Procesa documentos, genera chunks semánticos y embeddings para RAG
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import asyncpg
from openai import OpenAI

logger = logging.getLogger(__name__)

CHUNK_CONFIG = {
    "marco_legal": {"strategy": "by_article", "min_tokens": 300, "max_tokens": 800, "overlap": 50},
    "jurisprudencias": {"strategy": "semantic", "min_tokens": 500, "max_tokens": 1200, "overlap": 100},
    "criterios_sat": {"strategy": "by_criterio", "min_tokens": 400, "max_tokens": 1000, "overlap": 50},
    "catalogos_sat": {"strategy": "by_entry", "min_tokens": 100, "max_tokens": 500, "overlap": 0},
    "casos_referencia": {"strategy": "semantic", "min_tokens": 400, "max_tokens": 1000, "overlap": 100},
    "glosarios": {"strategy": "by_term", "min_tokens": 50, "max_tokens": 300, "overlap": 0},
    "plantillas": {"strategy": "full_document", "min_tokens": 100, "max_tokens": 2000, "overlap": 0}
}

CATEGORIA_AGENTES = {
    "cff": ["A3", "A4", "A7"],
    "lisr": ["A3", "A5", "A7"],
    "liva": ["A3", "A5"],
    "rcff": ["A3", "A4"],
    "rlisr": ["A3", "A5"],
    "rmf": ["A3", "A6"],
    "razon_negocios": ["A1", "A3", "A7"],
    "efos": ["A3", "A6", "A7"],
    "materialidad": ["A3", "A6", "A7"],
    "deducciones": ["A3", "A5", "A7"],
    "criterios_normativos": ["A3", "A6"],
    "criterios_no_vinculativos": ["A3", "A6"],
    "c_claveprodserv": ["A3", "A6"],
    "lista_69b": ["A6", "A7"],
    "lista_69b_bis": ["A6", "A7"],
    "general": ["A3"]
}

@dataclass
class ProcessResult:
    documento_id: str
    chunks: int
    agentes_notificados: List[str]
    errores: List[str]


class KBDocumentProcessor:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.openai_client = OpenAI()
        self.pool = None
    
    async def get_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.db_url)
        return self.pool
    
    async def extract_text(self, content: bytes, filename: str) -> str:
        extension = filename.lower().split('.')[-1]
        
        if extension == 'pdf':
            try:
                import fitz
                doc = fitz.open(stream=content, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
                return ""
        
        elif extension == 'docx':
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(content))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error extracting DOCX: {e}")
                return ""
        
        elif extension in ['txt', 'md']:
            return content.decode('utf-8', errors='ignore')
        
        else:
            return content.decode('utf-8', errors='ignore')[:50000]
    
    async def clasificar_documento(self, texto: str, categoria_hint: str, filename: str) -> Dict:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""Analiza este documento fiscal mexicano y extrae su metadata.

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
    "titulo": "Título del documento",
    "articulos_principales": [],
    "temas_clave": [],
    "resumen_ejecutivo": "Descripción breve"
  }}
}}"""
                }]
            )

            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error clasificando documento: {e}")
            return {
                "categoria": categoria_hint or "general",
                "subcategoria": "general",
                "version": None,
                "esVigente": True,
                "fechaVigencia": None,
                "fechaPublicacion": None,
                "fuente": "otro",
                "metadata": {"titulo": filename, "articulos_principales": [], "temas_clave": [], "resumen_ejecutivo": ""}
            }
    
    async def chunk_documento(self, texto: str, config: Dict, clasificacion: Dict) -> List[Dict]:
        try:
            texto_truncado = texto[:30000]

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=8000,
                messages=[{
                    "role": "user",
                    "content": f"""Divide este texto en chunks para RAG siguiendo estas reglas:

CONFIGURACIÓN:
- Estrategia: {config['strategy']}
- Tokens mínimos: {config['min_tokens']}
- Tokens máximos: {config['max_tokens']}

REGLAS DE CHUNKING PARA DOCUMENTOS FISCALES MEXICANOS:
1. Si es ley: dividir por Artículo, manteniendo contexto
2. Si es jurisprudencia: mantener rubro + considerandos + resolutivo juntos
3. Si es criterio SAT: un chunk por criterio completo
4. Nunca cortar en medio de una fracción o inciso
5. Mínimo 3 chunks, máximo 20 chunks

TEXTO:
{texto_truncado}

Responde SOLO con JSON válido:
{{
  "chunks": [
    {{
      "contenido": "Texto del chunk",
      "tokens": 450,
      "metadata": {{
        "articulo": "27",
        "fraccion": "I",
        "tipo": "definicion|requisito|sancion|procedimiento"
      }}
    }}
  ]
}}"""
                }]
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            return result.get("chunks", [])
        except Exception as e:
            logger.error(f"Error chunking documento: {e}")
            chunks = []
            words = texto.split()
            chunk_size = 500
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i+chunk_size]
                chunks.append({
                    "contenido": " ".join(chunk_words),
                    "tokens": len(chunk_words),
                    "metadata": {"tipo": "auto_chunk", "index": i // chunk_size}
                })
            return chunks[:20]
    
    async def generar_embedding(self, texto: str) -> List[float]:
        try:
            import openai
            client = openai.OpenAI()
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texto[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return [0.0] * 1536
    
    def determinar_agentes(self, subcategoria: str, metadata: Dict) -> List[str]:
        agentes_base = CATEGORIA_AGENTES.get(subcategoria, CATEGORIA_AGENTES["general"])
        agentes = set(agentes_base)
        
        contenido_lower = json.dumps(metadata).lower()
        
        if "69-b" in contenido_lower or "efos" in contenido_lower:
            agentes.add("A6")
            agentes.add("A7")
        if "razón de negocios" in contenido_lower or "sustancia económica" in contenido_lower:
            agentes.add("A1")
            agentes.add("A7")
        if "deducción" in contenido_lower or "deducible" in contenido_lower:
            agentes.add("A3")
            agentes.add("A5")
        if "contrato" in contenido_lower or "cláusula" in contenido_lower:
            agentes.add("A4")
        
        return list(agentes)
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        categoria: str,
        empresa_id: str = None,  # UUID string
        metadata: Dict = None
    ) -> ProcessResult:
        errors = []
        pool = await self.get_pool()
        
        texto = await self.extract_text(file_content, filename)
        if not texto.strip():
            raise ValueError("No se pudo extraer texto del documento")
        
        hash_contenido = hashlib.sha256(texto.encode()).hexdigest()
        
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM kb_documentos WHERE hash_contenido = $1",
                hash_contenido
            )
            if existing:
                raise ValueError(f"Documento duplicado. Ya existe con ID: {existing['id']}")
        
        clasificacion = await self.clasificar_documento(texto, categoria, filename)
        
        extension = filename.lower().split('.')[-1]
        
        async with pool.acquire() as conn:
            # Insert with UUID empresa_id
            doc_result = await conn.fetchrow("""
                INSERT INTO kb_documentos (
                    empresa_id, nombre, tipo_archivo, categoria, subcategoria, version,
                    hash_contenido, estado, metadata
                ) VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, 'procesando', $8)
                RETURNING id
            """,
                empresa_id,  # UUID string, cast in SQL
                filename,
                extension,
                clasificacion.get("categoria", categoria),
                clasificacion.get("subcategoria", "general"),
                clasificacion.get("version"),
                hash_contenido,
                json.dumps({**(metadata or {}), **clasificacion.get("metadata", {})})
            )
            documento_id = str(doc_result["id"])
        
        config = CHUNK_CONFIG.get(categoria, CHUNK_CONFIG["casos_referencia"])
        chunks = await self.chunk_documento(texto, config, clasificacion)
        
        agentes_notificados = set()
        
        async with pool.acquire() as conn:
            for i, chunk in enumerate(chunks):
                embedding = await self.generar_embedding(chunk.get("contenido", ""))
                agentes = self.determinar_agentes(clasificacion.get("subcategoria", "general"), chunk.get("metadata", {}))
                for a in agentes:
                    agentes_notificados.add(a)
                
                embedding_str = f"[{','.join(map(str, embedding))}]" if embedding else None
                chunk_result = await conn.fetchrow("""
                    INSERT INTO kb_chunks (
                        documento_id, contenido, contenido_embedding, chunk_index,
                        tokens, metadata, categoria_chunk, agentes_asignados, score_calidad
                    ) VALUES ($1, $2, $3::vector, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    doc_result["id"],
                    chunk.get("contenido", ""),
                    embedding_str,
                    i,
                    chunk.get("tokens", 0),
                    json.dumps(chunk.get("metadata", {})),
                    clasificacion.get("subcategoria", "general"),
                    agentes,
                    75.0
                )
                
                for agente in agentes:
                    await conn.execute("""
                        INSERT INTO kb_chunk_agente (chunk_id, agente_id, relevancia)
                        VALUES ($1, $2, $3)
                    """, chunk_result["id"], agente, 1.0)
            
            await conn.execute("""
                UPDATE kb_documentos SET estado = 'procesado', updated_at = NOW()
                WHERE id = $1
            """, doc_result["id"])
        
        return ProcessResult(
            documento_id=documento_id,
            chunks=len(chunks),
            agentes_notificados=list(agentes_notificados),
            errores=errors
        )
    
    async def get_kb_stats(self, empresa_id: str = None) -> Dict:
        """Get KB statistics. empresa_id is UUID string."""
        pool = await self.get_pool()

        async with pool.acquire() as conn:
            where_clause = "WHERE d.empresa_id = $1::uuid" if empresa_id else ""
            params = [empresa_id] if empresa_id else []
            
            stats = await conn.fetchrow(f"""
                SELECT 
                    COUNT(DISTINCT d.id) as total_documentos,
                    COALESCE(COUNT(c.id), 0) as total_chunks,
                    COALESCE(AVG(c.score_calidad), 0) as promedio_calidad
                FROM kb_documentos d
                LEFT JOIN kb_chunks c ON c.documento_id = d.id
                {where_clause}
            """, *params)
            
            categorias = await conn.fetch(f"""
                SELECT categoria, COUNT(*) as cnt
                FROM kb_documentos d
                {where_clause}
                GROUP BY categoria
            """, *params)
            
            por_categoria = {row["categoria"]: row["cnt"] for row in categorias}
            
            alertas = await self.get_alertas(conn)
            completitud = await self.calcular_completitud(conn)
        
        return {
            "total_documentos": stats["total_documentos"],
            "total_chunks": stats["total_chunks"],
            "promedio_calidad": float(stats["promedio_calidad"]) if stats["promedio_calidad"] else 0,
            "por_categoria": por_categoria,
            "completitud": completitud,
            "alertas": alertas
        }
    
    async def calcular_completitud(self, conn) -> Dict[str, float]:
        requisitos = {
            "marco_legal": ["cff", "lisr", "liva", "rcff", "rlisr", "rmf"],
            "jurisprudencias": ["razon_negocios", "efos", "materialidad", "deducciones"],
            "criterios_sat": ["criterios_normativos", "criterios_no_vinculativos"],
            "catalogos_sat": ["c_claveprodserv", "lista_69b"],
            "casos_referencia": [],
            "glosarios": ["glosario_fiscal"],
            "plantillas": ["defensa", "contratos"]
        }
        
        completitud = {}
        
        for cat, reqs in requisitos.items():
            if not reqs:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM kb_documentos WHERE categoria = $1",
                    cat
                )
                completitud[cat] = min(100, (count / 5) * 100) if count else 0
            else:
                existentes = await conn.fetch(
                    "SELECT DISTINCT subcategoria FROM kb_documentos WHERE categoria = $1",
                    cat
                )
                subcats = [r["subcategoria"] for r in existentes]
                cumplidos = len([r for r in reqs if r in subcats])
                completitud[cat] = (cumplidos / len(reqs)) * 100
        
        valores = list(completitud.values())
        completitud["general"] = sum(valores) / len(valores) if valores else 0
        
        return completitud
    
    async def get_alertas(self, conn) -> List[Dict]:
        alertas = []
        
        lista69b = await conn.fetchrow("""
            SELECT updated_at FROM kb_documentos 
            WHERE subcategoria = 'lista_69b' 
            ORDER BY updated_at DESC LIMIT 1
        """)
        
        if not lista69b:
            alertas.append({
                "tipo": "critica",
                "mensaje": "No existe lista 69-B en el sistema. A6 Proveedor no puede verificar EFOS.",
                "categoria": "catalogos_sat"
            })
        else:
            dias = (datetime.now() - lista69b["updated_at"]).days
            if dias > 15:
                alertas.append({
                    "tipo": "alta",
                    "mensaje": f"Lista 69-B tiene {dias} días de antigüedad. El SAT actualiza cada 2 semanas.",
                    "categoria": "catalogos_sat"
                })
        
        año_actual = datetime.now().year
        rmf = await conn.fetchrow("""
            SELECT version FROM kb_documentos 
            WHERE subcategoria = 'rmf' AND version LIKE $1
        """, f"%{año_actual}%")
        
        if not rmf:
            alertas.append({
                "tipo": "alta",
                "mensaje": f"No existe RMF {año_actual}. Puede haber criterios desactualizados.",
                "categoria": "marco_legal"
            })
        
        return alertas
    
    async def search_semantic(self, query: str, limit: int = 10, categoria: str = None, agente_id: str = None, empresa_id: str = None) -> List[Dict]:
        """
        Búsqueda semántica en el Knowledge Base.
        IMPORTANTE: empresa_id (UUID string) es OBLIGATORIO para garantizar aislamiento multi-tenant.
        Si no se proporciona, solo se retornan documentos públicos (sistema).
        """
        pool = await self.get_pool()

        query_embedding = await self.generar_embedding(query)

        async with pool.acquire() as conn:
            where_clauses = []
            params = [str(query_embedding), limit]
            param_idx = 3

            # CRITICAL: Filtro multi-tenant obligatorio
            # Si empresa_id es None, solo mostrar documentos del sistema (empresa_id IS NULL)
            # Si empresa_id tiene valor, mostrar documentos de esa empresa (UUID)
            if empresa_id is not None:
                where_clauses.append(f"d.empresa_id = ${param_idx}::uuid")
                params.append(empresa_id)
                param_idx += 1
            else:
                # Sin empresa_id, solo documentos públicos del sistema
                where_clauses.append("d.empresa_id IS NULL")

            if categoria:
                where_clauses.append(f"d.categoria = ${param_idx}")
                params.append(categoria)
                param_idx += 1

            if agente_id:
                where_clauses.append(f"${param_idx} = ANY(c.agentes_asignados)")
                params.append(agente_id)
                param_idx += 1

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            results = await conn.fetch(f"""
                SELECT
                    c.id,
                    c.contenido,
                    c.metadata,
                    c.categoria_chunk,
                    c.agentes_asignados,
                    d.nombre as documento_nombre,
                    d.categoria as documento_categoria,
                    d.empresa_id,
                    1 - (c.contenido_embedding <=> $1::vector) as similarity
                FROM kb_chunks c
                JOIN kb_documentos d ON d.id = c.documento_id
                {where_sql}
                ORDER BY c.contenido_embedding <=> $1::vector
                LIMIT $2
            """, *params)
            
            return [
                {
                    "id": str(r["id"]),
                    "contenido": r["contenido"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "categoria": r["categoria_chunk"],
                    "agentes": r["agentes_asignados"],
                    "documento": r["documento_nombre"],
                    "documento_categoria": r["documento_categoria"],
                    "empresa_id": r["empresa_id"],
                    "similarity": float(r["similarity"])
                }
                for r in results
            ]

    async def search_for_empresa(self, query: str, empresa_id: str, limit: int = 10, agente_id: str = None) -> List[Dict]:
        """
        Búsqueda específica para una empresa (UUID), garantizando aislamiento multi-tenant.
        Combina documentos de la empresa con documentos públicos del sistema.
        """
        pool = await self.get_pool()
        query_embedding = await self.generar_embedding(query)

        async with pool.acquire() as conn:
            where_clauses = []
            params = [str(query_embedding), limit]
            param_idx = 3

            # Mostrar documentos de la empresa O documentos públicos del sistema
            where_clauses.append(f"(d.empresa_id = ${param_idx}::uuid OR d.empresa_id IS NULL)")
            params.append(empresa_id)
            param_idx += 1

            if agente_id:
                where_clauses.append(f"${param_idx} = ANY(c.agentes_asignados)")
                params.append(agente_id)
                param_idx += 1

            where_sql = f"WHERE {' AND '.join(where_clauses)}"

            results = await conn.fetch(f"""
                SELECT
                    c.id,
                    c.contenido,
                    c.metadata,
                    c.categoria_chunk,
                    c.agentes_asignados,
                    d.nombre as documento_nombre,
                    d.categoria as documento_categoria,
                    d.empresa_id,
                    1 - (c.contenido_embedding <=> $1::vector) as similarity
                FROM kb_chunks c
                JOIN kb_documentos d ON d.id = c.documento_id
                {where_sql}
                ORDER BY c.contenido_embedding <=> $1::vector
                LIMIT $2
            """, *params)

            return [
                {
                    "id": str(r["id"]),
                    "contenido": r["contenido"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "categoria": r["categoria_chunk"],
                    "agentes": r["agentes_asignados"],
                    "documento": r["documento_nombre"],
                    "documento_categoria": r["documento_categoria"],
                    "empresa_id": r["empresa_id"],
                    "es_sistema": r["empresa_id"] is None,
                    "similarity": float(r["similarity"])
                }
                for r in results
            ]


kb_processor = KBDocumentProcessor()
