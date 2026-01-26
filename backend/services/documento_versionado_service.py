"""
Servicio de Versionamiento de Documentos de Clientes
Maneja subida, versionamiento, análisis IA y comparación de documentos
"""
import os
import json
import uuid
import hashlib
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import asyncpg
from anthropic import Anthropic

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOADS_BASE_PATH = Path("backend/uploads/clientes")


class DocumentoVersionadoService:
    """
    Servicio para gestión de documentos versionados de clientes.
    Soporta subida, versionamiento automático, análisis con IA y comparación.
    """
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        api_key = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_API_KEY')
        base_url = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_BASE_URL')
        
        if api_key and base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = None
            logger.warning("Anthropic AI integration not configured")
        
        self.model = "claude-sonnet-4-5"
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Obtiene o crea el pool de conexiones a PostgreSQL"""
        if self._pool is None:
            if not DATABASE_URL:
                raise RuntimeError("DATABASE_URL no está configurada")
            
            db_url = DATABASE_URL
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            self._pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
        return self._pool
    
    async def close(self):
        """Cierra el pool de conexiones"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    def _calcular_hash(self, contenido: bytes) -> str:
        """Calcula SHA-256 hash del contenido"""
        return hashlib.sha256(contenido).hexdigest()
    
    def _get_upload_path(self, cliente_id: int) -> Path:
        """Obtiene el directorio de uploads para un cliente"""
        path = UPLOADS_BASE_PATH / str(cliente_id)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    async def subir_documento(
        self,
        cliente_id: int,
        nombre_archivo: str,
        contenido: bytes,
        tipo_documento: Optional[str] = None,
        categoria: Optional[str] = None,
        subcategoria: Optional[str] = None,
        fecha_documento: Optional[datetime] = None,
        fecha_vigencia_fin: Optional[datetime] = None,
        usuario: Optional[str] = None,
        metadata_adicional: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sube un documento con detección automática de duplicados y versionamiento.
        
        Args:
            cliente_id: ID del cliente
            nombre_archivo: Nombre del archivo
            contenido: Contenido binario del archivo
            tipo_documento: Tipo del documento
            categoria: Categoría del documento
            subcategoria: Subcategoría del documento
            fecha_documento: Fecha del documento
            fecha_vigencia_fin: Fecha de vencimiento
            usuario: Usuario que sube el documento
            metadata_adicional: Metadata adicional
        
        Returns:
            Dict con información del documento creado
        """
        pool = await self._get_pool()
        
        hash_contenido = self._calcular_hash(contenido)
        
        async with pool.acquire() as conn:
            existente_hash = await conn.fetchrow(
                """
                SELECT id, documento_uuid, nombre_archivo, version 
                FROM clientes_documentos 
                WHERE cliente_id = $1 AND hash_contenido = $2 AND activo = true
                """,
                cliente_id, hash_contenido
            )
            
            if existente_hash:
                logger.info(f"Documento duplicado detectado: {nombre_archivo}")
                return {
                    "status": "duplicado",
                    "mensaje": "El documento ya existe (mismo contenido)",
                    "documento_id": existente_hash['id'],
                    "documento_uuid": existente_hash['documento_uuid'],
                    "version": existente_hash['version']
                }
            
            existente_nombre = await conn.fetchrow(
                """
                SELECT id, documento_uuid, version, nombre_archivo
                FROM clientes_documentos
                WHERE cliente_id = $1 AND nombre_archivo = $2 AND es_version_actual = true AND activo = true
                ORDER BY version DESC
                LIMIT 1
                """,
                cliente_id, nombre_archivo
            )
            
            if existente_nombre:
                documento_uuid = existente_nombre['documento_uuid']
                nueva_version = existente_nombre['version'] + 1
                version_anterior_id = existente_nombre['id']
                
                await conn.execute(
                    """
                    UPDATE clientes_documentos 
                    SET es_version_actual = false, updated_at = $1
                    WHERE documento_uuid = $2 AND es_version_actual = true
                    """,
                    datetime.utcnow(),
                    documento_uuid
                )
                
                logger.info(f"Nueva versión {nueva_version} para documento {documento_uuid}")
            else:
                documento_uuid = str(uuid.uuid4())
                nueva_version = 1
                version_anterior_id = None
            
            upload_path = self._get_upload_path(cliente_id)
            nombre_base = Path(nombre_archivo).stem
            extension = Path(nombre_archivo).suffix
            nombre_guardado = f"{nombre_base}_v{nueva_version}_{uuid.uuid4().hex[:8]}{extension}"
            ruta_archivo = upload_path / nombre_guardado
            
            ruta_archivo.write_bytes(contenido)
            
            now = datetime.utcnow()
            
            documento_id = await conn.fetchval(
                """
                INSERT INTO clientes_documentos (
                    cliente_id, documento_uuid, nombre_archivo, ruta_archivo,
                    tipo_documento, categoria, subcategoria,
                    version, es_version_actual, version_anterior_id,
                    hash_contenido, tamanio_bytes,
                    fecha_documento, fecha_vigencia_fin,
                    metadata_adicional, activo,
                    created_at, updated_at, creado_por
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                RETURNING id
                """,
                cliente_id,
                documento_uuid,
                nombre_archivo,
                str(ruta_archivo),
                tipo_documento,
                categoria,
                subcategoria,
                nueva_version,
                True,
                version_anterior_id,
                hash_contenido,
                len(contenido),
                fecha_documento,
                fecha_vigencia_fin,
                json.dumps(metadata_adicional) if metadata_adicional else None,
                True,
                now,
                now,
                usuario
            )
            
            await conn.execute(
                """
                INSERT INTO clientes_historial (
                    cliente_id, tipo_cambio, campo_modificado,
                    valor_nuevo, descripcion, origen,
                    agente_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                cliente_id,
                "documento_subido",
                "documentos",
                nombre_archivo,
                f"Documento '{nombre_archivo}' subido (versión {nueva_version})",
                "documento_versionado_service",
                usuario,
                now
            )
        
        asyncio.create_task(self.procesar_documento_async(documento_id))
        
        return {
            "status": "creado",
            "mensaje": f"Documento subido exitosamente (versión {nueva_version})",
            "documento_id": documento_id,
            "documento_uuid": documento_uuid,
            "version": nueva_version,
            "hash_contenido": hash_contenido,
            "ruta_archivo": str(ruta_archivo),
            "es_nueva_version": version_anterior_id is not None
        }
    
    async def procesar_documento_async(self, documento_id: int) -> None:
        """
        Procesa un documento de forma asíncrona con IA.
        Extrae resumen, tipo detectado, entidades y vigencia.
        
        Args:
            documento_id: ID del documento a procesar
        """
        if not self.client:
            logger.warning("Anthropic no configurado, no se puede procesar documento")
            return
        
        pool = await self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                documento = await conn.fetchrow(
                    """
                    SELECT id, cliente_id, nombre_archivo, ruta_archivo, tipo_documento
                    FROM clientes_documentos
                    WHERE id = $1
                    """,
                    documento_id
                )
                
                if not documento:
                    logger.error(f"Documento {documento_id} no encontrado")
                    return
            
            ruta = Path(documento['ruta_archivo'])
            if not ruta.exists():
                logger.error(f"Archivo no encontrado: {ruta}")
                return
            
            extension = ruta.suffix.lower()
            contenido_texto = ""
            
            if extension in ['.txt', '.md', '.csv', '.json', '.xml']:
                try:
                    contenido_texto = ruta.read_text(encoding='utf-8', errors='ignore')
                except Exception as e:
                    logger.error(f"Error leyendo archivo de texto: {e}")
                    contenido_texto = ""
            elif extension == '.pdf':
                try:
                    import fitz
                    pdf_doc = fitz.open(str(ruta))
                    contenido_texto = ""
                    for page in pdf_doc:
                        contenido_texto += page.get_text()
                    pdf_doc.close()
                except ImportError:
                    logger.warning("PyMuPDF no disponible para procesar PDF")
                    contenido_texto = f"[Archivo PDF: {documento['nombre_archivo']}]"
                except Exception as e:
                    logger.error(f"Error procesando PDF: {e}")
                    contenido_texto = f"[Error procesando PDF: {documento['nombre_archivo']}]"
            else:
                contenido_texto = f"[Archivo binario: {documento['nombre_archivo']}]"
            
            if len(contenido_texto) > 15000:
                contenido_texto = contenido_texto[:15000] + "...[truncado]"
            
            prompt = f"""Analiza el siguiente documento mexicano y extrae información estructurada.

NOMBRE DEL ARCHIVO: {documento['nombre_archivo']}

CONTENIDO:
{contenido_texto}

Extrae y responde ÚNICAMENTE con un JSON válido con esta estructura:
{{
    "resumen": "Resumen ejecutivo del documento en 2-3 oraciones en español",
    "tipo_detectado": "Tipo de documento detectado (contrato, factura, constancia, identificación, comprobante fiscal, carta, etc.)",
    "entidades": {{
        "rfcs": ["Lista de RFCs encontrados"],
        "montos": ["Lista de montos monetarios encontrados (ej: $10,000.00 MXN)"],
        "fechas": ["Lista de fechas importantes encontradas (formato YYYY-MM-DD)"],
        "nombres": ["Nombres de personas o empresas relevantes"],
        "direcciones": ["Direcciones encontradas"]
    }},
    "vigencia": {{
        "tiene_vigencia": true/false,
        "fecha_inicio": "YYYY-MM-DD o null",
        "fecha_fin": "YYYY-MM-DD o null",
        "descripcion": "Descripción de la vigencia si aplica"
    }},
    "metadata_adicional": {{
        "idioma": "es/en/otro",
        "num_paginas_estimadas": 1,
        "tiene_firma": true/false,
        "tiene_sello": true/false,
        "referencias_legales": ["Lista de artículos, leyes o normas mencionadas"]
    }},
    "confianza": 0.85
}}

Si no puedes extraer algún dato, usa null o lista vacía según corresponda."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            texto_respuesta = response.content[0].text
            
            if "```json" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0]
            elif "```" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]
            
            analisis = json.loads(texto_respuesta.strip())
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE clientes_documentos SET
                        resumen_ia = $1,
                        tipo_documento = COALESCE(tipo_documento, $2),
                        entidades_detectadas = $3,
                        metadata_extraida = $4,
                        fecha_vigencia_fin = COALESCE(fecha_vigencia_fin, $5),
                        procesado_ia = true,
                        fecha_procesado_ia = $6,
                        updated_at = $6
                    WHERE id = $7
                    """,
                    analisis.get('resumen'),
                    analisis.get('tipo_detectado'),
                    json.dumps(analisis.get('entidades', {})),
                    json.dumps(analisis),
                    self._parse_fecha(analisis.get('vigencia', {}).get('fecha_fin')),
                    datetime.utcnow(),
                    documento_id
                )
            
            logger.info(f"Documento {documento_id} procesado exitosamente con IA")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta de IA: {e}")
        except Exception as e:
            logger.error(f"Error procesando documento {documento_id}: {e}")
    
    def _parse_fecha(self, fecha_str: Optional[str]) -> Optional[datetime]:
        """Parsea una fecha string a datetime"""
        if not fecha_str or fecha_str == 'null':
            return None
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    
    async def comparar_versiones(
        self,
        documento_uuid: str,
        version_a: int,
        version_b: int
    ) -> Dict[str, Any]:
        """
        Compara dos versiones de un documento usando IA.
        
        Args:
            documento_uuid: UUID del documento
            version_a: Primera versión a comparar
            version_b: Segunda versión a comparar
        
        Returns:
            Dict con análisis de diferencias
        """
        if not self.client:
            return {
                "error": "Servicio de IA no configurado",
                "diferencias": []
            }
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            doc_a = await conn.fetchrow(
                """
                SELECT id, nombre_archivo, ruta_archivo, version, resumen_ia,
                       metadata_extraida, entidades_detectadas, created_at
                FROM clientes_documentos
                WHERE documento_uuid = $1 AND version = $2
                """,
                documento_uuid, version_a
            )
            
            doc_b = await conn.fetchrow(
                """
                SELECT id, nombre_archivo, ruta_archivo, version, resumen_ia,
                       metadata_extraida, entidades_detectadas, created_at
                FROM clientes_documentos
                WHERE documento_uuid = $1 AND version = $2
                """,
                documento_uuid, version_b
            )
        
        if not doc_a or not doc_b:
            return {
                "error": "Una o ambas versiones no existen",
                "diferencias": []
            }
        
        contenido_a = self._leer_contenido_archivo(doc_a['ruta_archivo'])
        contenido_b = self._leer_contenido_archivo(doc_b['ruta_archivo'])
        
        prompt = f"""Compara las siguientes dos versiones de un documento y describe las diferencias.

VERSIÓN {version_a} ({doc_a['created_at'].strftime('%Y-%m-%d %H:%M') if doc_a['created_at'] else 'N/A'}):
{contenido_a[:8000]}

---

VERSIÓN {version_b} ({doc_b['created_at'].strftime('%Y-%m-%d %H:%M') if doc_b['created_at'] else 'N/A'}):
{contenido_b[:8000]}

Responde ÚNICAMENTE con un JSON válido:
{{
    "resumen_cambios": "Descripción general de los cambios entre versiones en español",
    "diferencias": [
        {{
            "tipo": "adición/eliminación/modificación",
            "seccion": "Sección afectada",
            "descripcion": "Descripción del cambio"
        }}
    ],
    "impacto": "bajo/medio/alto",
    "descripcion_impacto": "Por qué el impacto es este nivel",
    "recomendaciones": ["Lista de recomendaciones basadas en los cambios"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            texto_respuesta = response.content[0].text
            
            if "```json" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0]
            elif "```" in texto_respuesta:
                texto_respuesta = texto_respuesta.split("```")[1].split("```")[0]
            
            comparacion = json.loads(texto_respuesta.strip())
            
            return {
                "documento_uuid": documento_uuid,
                "version_a": {
                    "version": version_a,
                    "id": doc_a['id'],
                    "fecha": doc_a['created_at'].isoformat() if doc_a['created_at'] else None,
                    "resumen": doc_a['resumen_ia']
                },
                "version_b": {
                    "version": version_b,
                    "id": doc_b['id'],
                    "fecha": doc_b['created_at'].isoformat() if doc_b['created_at'] else None,
                    "resumen": doc_b['resumen_ia']
                },
                **comparacion
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta de comparación: {e}")
            return {
                "error": "Error al procesar comparación con IA",
                "diferencias": []
            }
        except Exception as e:
            logger.error(f"Error comparando versiones: {e}")
            return {
                "error": str(e),
                "diferencias": []
            }
    
    def _leer_contenido_archivo(self, ruta_str: str) -> str:
        """Lee el contenido de un archivo como texto"""
        ruta = Path(ruta_str)
        if not ruta.exists():
            return "[Archivo no encontrado]"
        
        extension = ruta.suffix.lower()
        
        if extension in ['.txt', '.md', '.csv', '.json', '.xml']:
            try:
                return ruta.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                return "[Error leyendo archivo]"
        elif extension == '.pdf':
            try:
                import fitz
                pdf_doc = fitz.open(str(ruta))
                contenido = ""
                for page in pdf_doc:
                    contenido += page.get_text()
                pdf_doc.close()
                return contenido
            except ImportError:
                return "[PyMuPDF no disponible]"
            except Exception:
                return "[Error procesando PDF]"
        else:
            return f"[Archivo binario: {ruta.name}]"
    
    async def get_versiones(
        self,
        cliente_id: int,
        documento_uuid: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las versiones de un documento.
        
        Args:
            cliente_id: ID del cliente
            documento_uuid: UUID del documento
        
        Returns:
            Lista de versiones del documento
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            versiones = await conn.fetch(
                """
                SELECT 
                    id, documento_uuid, nombre_archivo, ruta_archivo,
                    tipo_documento, categoria, subcategoria,
                    version, es_version_actual, version_anterior_id,
                    hash_contenido, tamanio_bytes,
                    resumen_ia, entidades_detectadas, metadata_extraida,
                    fecha_documento, fecha_vigencia_fin,
                    procesado_ia, fecha_procesado_ia,
                    created_at, updated_at, creado_por
                FROM clientes_documentos
                WHERE cliente_id = $1 AND documento_uuid = $2 AND activo = true
                ORDER BY version DESC
                """,
                cliente_id, documento_uuid
            )
        
        resultado = []
        for v in versiones:
            resultado.append({
                "id": v['id'],
                "documento_uuid": v['documento_uuid'],
                "nombre_archivo": v['nombre_archivo'],
                "ruta_archivo": v['ruta_archivo'],
                "tipo_documento": v['tipo_documento'],
                "categoria": v['categoria'],
                "subcategoria": v['subcategoria'],
                "version": v['version'],
                "es_version_actual": v['es_version_actual'],
                "version_anterior_id": v['version_anterior_id'],
                "hash_contenido": v['hash_contenido'],
                "tamanio_bytes": v['tamanio_bytes'],
                "resumen_ia": v['resumen_ia'],
                "entidades_detectadas": json.loads(v['entidades_detectadas']) if v['entidades_detectadas'] else None,
                "metadata_extraida": json.loads(v['metadata_extraida']) if v['metadata_extraida'] else None,
                "fecha_documento": v['fecha_documento'].isoformat() if v['fecha_documento'] else None,
                "fecha_vigencia_fin": v['fecha_vigencia_fin'].isoformat() if v['fecha_vigencia_fin'] else None,
                "procesado_ia": v['procesado_ia'],
                "fecha_procesado_ia": v['fecha_procesado_ia'].isoformat() if v['fecha_procesado_ia'] else None,
                "created_at": v['created_at'].isoformat() if v['created_at'] else None,
                "updated_at": v['updated_at'].isoformat() if v['updated_at'] else None,
                "creado_por": v['creado_por']
            })
        
        return resultado
    
    async def get_documento(
        self,
        documento_id: int,
        cliente_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un documento por ID.
        
        Args:
            documento_id: ID del documento
            cliente_id: ID del cliente (para validación opcional)
        
        Returns:
            Dict con información del documento o None
        """
        pool = await self._get_pool()
        
        query = """
            SELECT 
                id, cliente_id, documento_uuid, nombre_archivo, ruta_archivo,
                tipo_documento, categoria, subcategoria,
                version, es_version_actual, version_anterior_id,
                hash_contenido, tamanio_bytes,
                resumen_ia, entidades_detectadas, metadata_extraida,
                fecha_documento, fecha_vigencia_fin,
                procesado_ia, fecha_procesado_ia,
                created_at, updated_at, creado_por, activo
            FROM clientes_documentos
            WHERE id = $1
        """
        params = [documento_id]
        
        if cliente_id:
            query += " AND cliente_id = $2"
            params.append(cliente_id)
        
        async with pool.acquire() as conn:
            doc = await conn.fetchrow(query, *params)
        
        if not doc:
            return None
        
        return {
            "id": doc['id'],
            "cliente_id": doc['cliente_id'],
            "documento_uuid": doc['documento_uuid'],
            "nombre_archivo": doc['nombre_archivo'],
            "ruta_archivo": doc['ruta_archivo'],
            "tipo_documento": doc['tipo_documento'],
            "categoria": doc['categoria'],
            "subcategoria": doc['subcategoria'],
            "version": doc['version'],
            "es_version_actual": doc['es_version_actual'],
            "version_anterior_id": doc['version_anterior_id'],
            "hash_contenido": doc['hash_contenido'],
            "tamanio_bytes": doc['tamanio_bytes'],
            "resumen_ia": doc['resumen_ia'],
            "entidades_detectadas": json.loads(doc['entidades_detectadas']) if doc['entidades_detectadas'] else None,
            "metadata_extraida": json.loads(doc['metadata_extraida']) if doc['metadata_extraida'] else None,
            "fecha_documento": doc['fecha_documento'].isoformat() if doc['fecha_documento'] else None,
            "fecha_vigencia_fin": doc['fecha_vigencia_fin'].isoformat() if doc['fecha_vigencia_fin'] else None,
            "procesado_ia": doc['procesado_ia'],
            "fecha_procesado_ia": doc['fecha_procesado_ia'].isoformat() if doc['fecha_procesado_ia'] else None,
            "created_at": doc['created_at'].isoformat() if doc['created_at'] else None,
            "updated_at": doc['updated_at'].isoformat() if doc['updated_at'] else None,
            "creado_por": doc['creado_por'],
            "activo": doc['activo']
        }
    
    async def listar_documentos_cliente(
        self,
        cliente_id: int,
        solo_actuales: bool = True,
        tipo_documento: Optional[str] = None,
        categoria: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista documentos de un cliente con filtros.
        
        Args:
            cliente_id: ID del cliente
            solo_actuales: Si True, solo retorna versiones actuales
            tipo_documento: Filtro por tipo
            categoria: Filtro por categoría
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de documentos
        """
        pool = await self._get_pool()
        
        query = """
            SELECT 
                id, documento_uuid, nombre_archivo, tipo_documento, categoria,
                version, es_version_actual, resumen_ia, tamanio_bytes,
                fecha_documento, fecha_vigencia_fin, created_at
            FROM clientes_documentos
            WHERE cliente_id = $1 AND activo = true
        """
        params = [cliente_id]
        param_idx = 2
        
        if solo_actuales:
            query += " AND es_version_actual = true"
        
        if tipo_documento:
            query += f" AND tipo_documento = ${param_idx}"
            params.append(tipo_documento)
            param_idx += 1
        
        if categoria:
            query += f" AND categoria = ${param_idx}"
            params.append(categoria)
            param_idx += 1
        
        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            docs = await conn.fetch(query, *params)
        
        return [
            {
                "id": d['id'],
                "documento_uuid": d['documento_uuid'],
                "nombre_archivo": d['nombre_archivo'],
                "tipo_documento": d['tipo_documento'],
                "categoria": d['categoria'],
                "version": d['version'],
                "es_version_actual": d['es_version_actual'],
                "resumen_ia": d['resumen_ia'],
                "tamanio_bytes": d['tamanio_bytes'],
                "fecha_documento": d['fecha_documento'].isoformat() if d['fecha_documento'] else None,
                "fecha_vigencia_fin": d['fecha_vigencia_fin'].isoformat() if d['fecha_vigencia_fin'] else None,
                "created_at": d['created_at'].isoformat() if d['created_at'] else None
            }
            for d in docs
        ]


documento_versionado_service = DocumentoVersionadoService()
