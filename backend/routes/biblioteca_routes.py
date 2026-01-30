"""
Biblioteca Routes for Bibliotecar.IA
RAG document management, upload, search, and chat endpoints.
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from pydantic import BaseModel
import logging
import os
import hashlib
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/biblioteca", tags=["biblioteca"])
security = HTTPBearer(auto_error=False)

LARGE_FILE_THRESHOLD = 1_000_000  # 1MB threshold for large files
LISTA_69B_KEYWORDS = ['69-b', '69b', 'lista_69', 'listado_69', 'efos']

rag_processor = None
agent_kb_service = None
openai_client = None
session_factory = None


def init_biblioteca_services(sf, llm_client=None):
    """Initialize biblioteca services with session factory and optional LLM client."""
    global rag_processor, agent_kb_service, openai_client, session_factory
    from services.knowledge_base.rag_processor import RAGProcessor
    from services.knowledge_base.agent_kb_service import AgentKBService
    from services.knowledge_base.embeddings_service import embeddings_service
    from services.openai_provider import openai_client as oai_client

    session_factory = sf
    openai_client = oai_client  # Use OpenAI client from provider
    rag_processor = RAGProcessor(sf, openai_client)
    agent_kb_service = AgentKBService(sf, embeddings_service)
    logger.info("Biblioteca services initialized with RAG processor")


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    session_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    agente_id: Optional[str] = None
    categoria: Optional[str] = None
    limit: int = 10


class SolicitudRequest(BaseModel):
    categoria: str
    descripcion: str
    solicitado_por: str
    razon: str
    prioridad: str = 'media'


@router.get("/stats")
async def get_stats(empresa_id: Optional[str] = None):
    """Get real KB statistics from kb_metricas table."""
    if not rag_processor:
        return {
            "total_documentos": 0,
            "total_chunks": 0,
            "promedio_calidad": 0,
            "por_categoria": {},
            "por_agente": {},
            "completitud": {"general": 0},
            "alertas": []
        }
    
    try:
        stats = await rag_processor.get_stats(empresa_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "total_documentos": 0,
            "total_chunks": 0,
            "promedio_calidad": 0,
            "por_categoria": {},
            "por_agente": {},
            "completitud": {"general": 0},
            "alertas": [],
            "error": str(e)
        }


def _is_lista_69b_file(filename: str) -> bool:
    """Check if the filename indicates a Lista 69-B file."""
    filename_lower = filename.lower()
    return any(keyword in filename_lower for keyword in LISTA_69B_KEYWORDS)


def _is_large_csv(filename: str, content: bytes) -> bool:
    """Check if file is a large CSV (>1MB)."""
    return (
        filename.lower().endswith(('.csv', '.xls', '.xlsx')) and 
        len(content) > LARGE_FILE_THRESHOLD
    )


async def _store_large_file_metadata(
    filename: str,
    content: bytes,
    categoria: str,
    empresa_id: Optional[str]
) -> dict:
    """
    Store large file with metadata only (skip RAG processing).
    Used for Lista 69-B and other large data files that would timeout.
    """
    from sqlalchemy import text
    
    if not session_factory:
        return {
            'success': False,
            'error': 'Service not initialized'
        }
    
    try:
        hash_contenido = hashlib.sha256(content).hexdigest()
        doc_id = str(uuid4())
        
        extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        
        is_69b = _is_lista_69b_file(filename)
        effective_categoria = 'lista_69b' if is_69b else categoria
        
        upload_dir = os.path.join('backend', 'uploads', 'kb')
        os.makedirs(upload_dir, exist_ok=True)
        
        clean_name = filename.replace('/', '_').replace('\\', '_')
        safe_filename = f"{doc_id}_{clean_name}"
        file_path = os.path.join(upload_dir, safe_filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        
        async with session_factory() as session:
            existing = await session.execute(
                text('SELECT id FROM kb_documentos WHERE hash_contenido = :hash'),
                {'hash': hash_contenido}
            )
            if existing.fetchone():
                return {
                    'success': False,
                    'error': 'Documento duplicado - ya existe en la base de conocimiento',
                    'skipped_rag': True
                }
            
            await session.execute(
                text('''
                    INSERT INTO kb_documentos 
                    (id, nombre, tipo_archivo, categoria, subcategoria, hash_contenido,
                     tamaño_bytes, empresa_id, estado, procesado, activo, es_version_vigente,
                     fuente, created_at, updated_at, metadata)
                    VALUES 
                    (:id, :nombre, :tipo, :cat, :subcat, :hash,
                     :size, :empresa, :estado, :procesado, TRUE, TRUE,
                     :fuente, NOW(), NOW(), :metadata)
                '''),
                {
                    'id': doc_id,
                    'nombre': filename,
                    'tipo': extension,
                    'cat': effective_categoria,
                    'subcat': 'lista_69b' if is_69b else 'general',
                    'hash': hash_contenido,
                    'size': len(content),
                    'empresa': empresa_id,
                    'estado': 'metadata_only',
                    'procesado': False,
                    'fuente': 'SAT' if is_69b else 'upload',
                    'metadata': f'{{"archivo_grande": true, "skip_rag": true, "ruta": "{file_path}", "es_lista_69b": {str(is_69b).lower()}}}'
                }
            )
            await session.commit()
        
        message = (
            f"Archivo grande detectado ({len(content) / 1_000_000:.1f} MB). "
            f"Se guardó con metadatos sin procesamiento RAG completo."
        )
        if is_69b:
            message += " Este archivo de Lista 69-B ya está indexado en la tabla especializada lista_69b."
        
        return {
            'success': True,
            'documento_id': doc_id,
            'chunks_created': 0,
            'agents_notified': ['A6', 'A7'] if is_69b else [],
            'categoria': effective_categoria,
            'ley_codigo': None,
            'skipped_rag': True,
            'message': message,
            'file_path': file_path
        }
        
    except Exception as e:
        logger.error(f"Error storing large file metadata for {filename}: {e}")
        return {
            'success': False,
            'error': str(e),
            'skipped_rag': True
        }


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    categoria: str = Form("casos_referencia"),
    empresa_id: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Upload and process documents through the RAG pipeline.

    - Classifies documents using Claude AI
    - Creates intelligent chunks (by articles for laws, semantic for others)
    - Generates embeddings
    - Assigns chunks to agents A1-A7
    - Updates metrics

    For large CSV files (>1MB) like Lista 69-B, RAG processing is skipped
    to prevent timeout. These files are stored with metadata only.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="Al menos un archivo es requerido")

        if not rag_processor and not session_factory:
            raise HTTPException(status_code=503, detail="Servicio RAG no inicializado")

        results = []
        for file in files:
            if not file or not file.filename:
                results.append({
                    "filename": "unknown",
                    "success": False,
                    "error": "Nombre de archivo inválido"
                })
                continue
            try:
                if not file.filename:
                    raise HTTPException(status_code=400, detail="Filename es requerido")

                content = await file.read()

                if not content:
                    raise HTTPException(status_code=400, detail=f"Archivo {file.filename} está vacío")

                if _is_large_csv(file.filename, content):
                    logger.info(f"Large file detected: {file.filename} ({len(content)} bytes) - skipping RAG processing")
                    result = await _store_large_file_metadata(
                        filename=file.filename,
                        content=content,
                        categoria=categoria,
                        empresa_id=empresa_id
                    )
                    results.append({
                        "filename": file.filename,
                        "success": result.get('success', False),
                        "documento_id": result.get('documento_id'),
                        "chunks_created": result.get('chunks_created', 0),
                        "agents_notified": result.get('agents_notified', []),
                        "categoria": result.get('categoria'),
                        "ley_codigo": result.get('ley_codigo'),
                        "skipped_rag": True,
                        "message": result.get('message', 'Archivo grande procesado sin RAG'),
                        "errors": [result.get('error')] if result.get('error') else []
                    })
                    continue

                if not rag_processor:
                    raise HTTPException(status_code=503, detail="Servicio RAG no inicializado")

                result = await rag_processor.process_document(
                    file_content=content,
                    filename=file.filename,
                    categoria_hint=categoria,
                    empresa_id=empresa_id
                )
                results.append({
                    "filename": file.filename,
                    "success": result.get('success', False),
                    "documento_id": result.get('documento_id'),
                    "chunks_created": result.get('chunks_created', 0),
                    "agents_notified": result.get('agents_notified', []),
                    "categoria": result.get('categoria'),
                    "ley_codigo": result.get('ley_codigo'),
                    "errors": result.get('errors', [])
                })
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing {file.filename if file else 'unknown'}: {e}")
                results.append({
                    "filename": file.filename if file else "unknown",
                    "success": False,
                    "error": str(e)
                })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_documents: {e}")
        if "permission" in str(e).lower():
            status_code = 403
        elif "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=f"Error al procesar documentos: {str(e)}")

    successful = len([r for r in results if r.get("success")])
    failed = len([r for r in results if not r.get("success")])
    skipped_rag = len([r for r in results if r.get("skipped_rag")])

    return {
        "processed": successful,
        "failed": failed,
        "skipped_rag": skipped_rag,
        "total_chunks": sum(r.get("chunks_created", 0) for r in results),
        "results": results,
        "message": f"Procesados: {successful}, Fallidos: {failed}" + (f", Sin RAG (archivos grandes): {skipped_rag}" if skipped_rag > 0 else "")
    }


@router.get("/search")
async def search_kb_get(
    query: str = Query(..., description="Search query"),
    agente_id: Optional[str] = Query(None, description="Filter by agent"),
    categoria: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Max results")
):
    """Semantic search endpoint (GET method)."""
    if not rag_processor:
        return {"results": [], "count": 0}
    
    try:
        results = await rag_processor.semantic_search(
            query=query,
            agente_id=agente_id,
            categoria=categoria,
            limit=limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return {"results": [], "count": 0, "error": str(e)}


@router.post("/search")
async def search_kb(request: SearchRequest):
    """Semantic search endpoint (POST method)."""
    if not rag_processor:
        return {"results": [], "count": 0}
    
    try:
        results = await rag_processor.semantic_search(
            query=request.query,
            agente_id=request.agente_id,
            categoria=request.categoria,
            limit=request.limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return {"results": [], "count": 0, "error": str(e)}


@router.post("/chat")
async def chat_with_biblioteca(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Chat with Bibliotecar.IA assistant using RAG context."""
    if not rag_processor:
        return {
            "response": "El servicio de Bibliotecar.IA está inicializándose. Por favor intenta de nuevo.",
            "documents_found": 0,
            "stats": {"documentos": 0, "chunks": 0, "completitud": 0}
        }
    
    try:
        stats = await rag_processor.get_stats()
        
        search_results = await rag_processor.semantic_search(
            query=request.message,
            limit=5
        )
        
        contexto_kb = ""
        if search_results:
            contexto_kb = "\n\n--- DOCUMENTOS RELEVANTES ---\n"
            for r in search_results:
                ley_info = f" ({r['ley_codigo']})" if r.get('ley_codigo') else ""
                articulo_info = f" Art. {r['articulo']}" if r.get('articulo') else ""
                contexto_kb += f"\n[{r['documento']}{ley_info}{articulo_info} - {r['categoria']}]\n"
                contexto_kb += f"{r['contenido'][:600]}...\n"
                contexto_kb += f"(Relevancia: {r.get('similarity', 0):.2f})\n"
            contexto_kb += "--- FIN DOCUMENTOS ---\n"
        
        if openai_client:
            por_agente = stats.get('por_agente', {})
            agentes_info = ", ".join([f"{k}: {v} chunks" for k, v in por_agente.items()]) if por_agente else "Sin asignaciones"
            
            system_prompt = f'''Eres la Dra. Elena Vázquez Archivista, curadora del acervo legal de Bibliotecar.IA.
Tienes 20 años de experiencia en taxonomías legales mexicanas y optimización RAG.

ESTADO ACTUAL DEL ACERVO:
- Documentos procesados: {stats['total_documentos']}
- Chunks RAG totales: {stats['total_chunks']}
- Completitud general: {stats['completitud'].get('general', 0):.1f}%
- Distribución por agentes: {agentes_info}

CATEGORÍAS DISPONIBLES:
- marco_legal: Leyes y códigos (CFF, LISR, LIVA, reglamentos)
- jurisprudencias: Tesis, criterios de SCJN, TFJA, PRODECON
- criterios_sat: Criterios normativos y no vinculativos
- catalogos_sat: Catálogos del SAT (c_ClaveProdServ, etc.)
- efos/lista_69b: Proveedores en lista negra
- casos_referencia: Casos prácticos y precedentes
- plantillas: Contratos y formatos

Tu rol:
1. Ayudar a ingestar y clasificar documentos fiscales mexicanos
2. Explicar cómo se asignan chunks a los agentes A1-A7
3. Responder preguntas usando el contexto RAG de documentos encontrados
4. Guiar sobre documentos faltantes o que necesitan actualización

MAPEO DE AGENTES:
- A1 (Sponsor/Estrategia): Razón de negocios, CFF Art. 5-A
- A3 (Fiscal): CFF, LISR, LIVA, criterios SAT
- A4 (Legal): Contratos, NOM-151, CFF procedimientos
- A5 (Finanzas): LISR deducciones, costos, inversiones
- A6 (Proveedores): Lista 69-B, EFOs, materialidad
- A7 (Defensa): TFJA, PRODECON, litigio fiscal

{contexto_kb}

Responde siempre en español mexicano profesional. Si encuentras documentos relevantes, cítalos específicamente.'''

            messages = [{"role": "system", "content": system_prompt}]
            for h in (request.history or [])[-10:]:
                messages.append({
                    "role": h.get("role", "user"),
                    "content": h.get("content", "")
                })
            messages.append({"role": "user", "content": request.message})

            response = openai_client.chat.completions.create(
                model='gpt-4o',
                max_tokens=2000,
                messages=messages
            )

            response_text = response.choices[0].message.content if response.choices else "No pude generar una respuesta."
        else:
            por_cat = stats.get('por_categoria', {})
            cat_info = "\n".join([f"  - {k}: {v} docs" for k, v in por_cat.items()]) if por_cat else "  Sin categorías"
            
            response_text = f'''¡Hola! Soy la Dra. Elena Vázquez, curadora de Bibliotecar.IA.

**Estado actual del acervo:**
- Documentos: {stats['total_documentos']}
- Chunks RAG: {stats['total_chunks']}
- Completitud: {stats['completitud'].get('general', 0):.1f}%

**Por categoría:**
{cat_info}

{'**Documentos encontrados para tu consulta:** ' + str(len(search_results)) if search_results else ''}

Puedo ayudarte a:
- 📥 Cargar documentos al acervo (leyes, jurisprudencias, criterios SAT)
- 🔍 Buscar información específica con búsqueda semántica
- 📊 Ver métricas y estado de completitud
- 🤖 Explicar cómo se asignan chunks a los agentes A1-A7

¿En qué puedo ayudarte?'''
        
        return {
            "response": response_text,
            "documents_found": len(search_results),
            "stats": {
                "documentos": stats['total_documentos'],
                "chunks": stats['total_chunks'],
                "completitud": stats['completitud'].get('general', 0),
                "por_categoria": stats.get('por_categoria', {}),
                "por_agente": stats.get('por_agente', {})
            },
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {
            "response": f"Hubo un error al procesar tu mensaje: {str(e)}",
            "documents_found": 0,
            "stats": {"documentos": 0, "chunks": 0, "completitud": 0}
        }


@router.get("/documentos")
async def list_documentos(
    categoria: Optional[str] = None,
    empresa_id: Optional[str] = None,
    ley_codigo: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List documents in the knowledge base with optional filters."""
    if not session_factory:
        return {"documentos": [], "total": 0, "limit": limit, "offset": offset}
    
    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            where_parts = ["(activo = TRUE OR activo IS NULL)"]
            params = {'limit': limit, 'offset': offset}
            
            if categoria:
                where_parts.append("categoria = :cat")
                params['cat'] = categoria
            
            if empresa_id:
                where_parts.append("empresa_id = :empresa")
                params['empresa'] = empresa_id
            
            if ley_codigo:
                where_parts.append("ley_codigo = :ley")
                params['ley'] = ley_codigo
            
            where_sql = f"WHERE {' AND '.join(where_parts)}"
            
            result = await session.execute(
                text(f'''
                    SELECT id, nombre, tipo_archivo, categoria, subcategoria, version,
                           es_version_vigente, fuente, estado, tamaño_bytes, created_at,
                           ley_codigo, total_chunks, procesado,
                           (SELECT COUNT(*) FROM kb_chunks WHERE documento_id = kb_documentos.id) as chunks_count
                    FROM kb_documentos
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                '''),
                params
            )
            docs = result.fetchall()
            
            count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
            count_result = await session.execute(
                text(f'SELECT COUNT(*) FROM kb_documentos {where_sql}'),
                count_params
            )
            total = count_result.scalar() or 0
            
            return {
                "documentos": [{
                    "id": str(row[0]),
                    "nombre": row[1],
                    "tipo_archivo": row[2],
                    "categoria": row[3],
                    "subcategoria": row[4],
                    "version": row[5],
                    "es_version_vigente": row[6],
                    "fuente": row[7],
                    "estado": row[8],
                    "tamaño_bytes": row[9],
                    "created_at": row[10].isoformat() if row[10] else None,
                    "ley_codigo": row[11],
                    "total_chunks": row[12] or row[14],
                    "procesado": row[13]
                } for row in docs],
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {"documentos": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}


@router.get("/chunks")
async def list_chunks(
    documento_id: Optional[str] = None,
    agente_id: Optional[str] = None,
    categoria: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List chunks with optional filters."""
    if not session_factory:
        return {"chunks": [], "total": 0}
    
    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            where_parts = []
            params = {'limit': limit, 'offset': offset}
            
            if documento_id:
                where_parts.append("c.documento_id = :doc_id")
                params['doc_id'] = documento_id
            
            if agente_id:
                where_parts.append(":agente = ANY(c.agentes_asignados)")
                params['agente'] = agente_id
            
            if categoria:
                where_parts.append("c.categoria_chunk = :cat")
                params['cat'] = categoria
            
            where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
            
            result = await session.execute(
                text(f'''
                    SELECT c.id, c.documento_id, c.contenido, c.chunk_index,
                           c.articulo, c.tipo_contenido, c.agentes_asignados,
                           c.score_calidad, d.nombre as doc_nombre, d.ley_codigo
                    FROM kb_chunks c
                    JOIN kb_documentos d ON d.id = c.documento_id
                    {where_sql}
                    ORDER BY c.created_at DESC
                    LIMIT :limit OFFSET :offset
                '''),
                params
            )
            chunks = result.fetchall()
            
            return {
                "chunks": [{
                    "id": str(row[0]),
                    "documento_id": str(row[1]),
                    "contenido": row[2][:500] + "..." if len(row[2]) > 500 else row[2],
                    "chunk_index": row[3],
                    "articulo": row[4],
                    "tipo_contenido": row[5],
                    "agentes_asignados": row[6] or [],
                    "score_calidad": row[7],
                    "documento_nombre": row[8],
                    "ley_codigo": row[9]
                } for row in chunks],
                "total": len(chunks),
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error listing chunks: {e}")
        return {"chunks": [], "total": 0, "error": str(e)}


@router.delete("/documentos/{documento_id}")
async def delete_documento(
    documento_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a document and its chunks from the knowledge base."""
    if not documento_id:
        raise HTTPException(status_code=400, detail="documento_id es requerido")

    if not session_factory:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")

    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            await session.execute(
                text('DELETE FROM kb_chunk_agente WHERE chunk_id IN (SELECT id FROM kb_chunks WHERE documento_id = :doc_id)'),
                {'doc_id': documento_id}
            )
            await session.execute(
                text('DELETE FROM kb_chunks WHERE documento_id = :doc_id'),
                {'doc_id': documento_id}
            )
            await session.execute(
                text('DELETE FROM kb_documentos WHERE id = :doc_id'),
                {'doc_id': documento_id}
            )
            await session.commit()

            return {"success": True, "deleted": documento_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/metricas")
async def get_metricas():
    """Get detailed metrics from kb_metricas table."""
    if not session_factory:
        return {"metricas": None}
    
    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            result = await session.execute(
                text('''
                    SELECT fecha, total_documentos, total_chunks, 
                           por_categoria, por_agente, completitud_general, updated_at
                    FROM kb_metricas
                    ORDER BY fecha DESC
                    LIMIT 30
                ''')
            )
            rows = result.fetchall()
            
            if not rows:
                return {"metricas": [], "latest": None}
            
            latest = rows[0]
            return {
                "latest": {
                    "fecha": latest[0].isoformat() if latest[0] else None,
                    "total_documentos": latest[1],
                    "total_chunks": latest[2],
                    "por_categoria": latest[3] or {},
                    "por_agente": latest[4] or {},
                    "completitud_general": latest[5],
                    "updated_at": latest[6].isoformat() if latest[6] else None
                },
                "historico": [{
                    "fecha": row[0].isoformat() if row[0] else None,
                    "total_documentos": row[1],
                    "total_chunks": row[2],
                    "completitud_general": row[5]
                } for row in rows]
            }
    except Exception as e:
        logger.error(f"Error getting metricas: {e}")
        return {"metricas": None, "error": str(e)}


@router.get("/alertas")
async def get_alertas():
    """Get knowledge base alerts."""
    if not session_factory:
        return {"alertas": [], "count": 0}
    
    try:
        from sqlalchemy import text
        
        alertas = []
        
        async with session_factory() as session:
            result = await session.execute(
                text('''
                    SELECT categoria, COUNT(*) 
                    FROM kb_documentos 
                    WHERE activo = TRUE OR activo IS NULL
                    GROUP BY categoria
                ''')
            )
            categorias = {row[0]: row[1] for row in result.fetchall()}
            
            required_cats = ['marco_legal', 'jurisprudencias', 'criterios_sat']
            for cat in required_cats:
                if cat not in categorias or categorias.get(cat, 0) < 3:
                    alertas.append({
                        "tipo": "faltante",
                        "categoria": cat,
                        "mensaje": f"La categoría '{cat}' tiene pocos documentos ({categorias.get(cat, 0)})",
                        "prioridad": "alta"
                    })
            
            old_docs = await session.execute(
                text('''
                    SELECT nombre, categoria, updated_at 
                    FROM kb_documentos 
                    WHERE updated_at < NOW() - INTERVAL '6 months'
                    AND (activo = TRUE OR activo IS NULL)
                    LIMIT 10
                ''')
            )
            for row in old_docs.fetchall():
                alertas.append({
                    "tipo": "actualizacion",
                    "documento": row[0],
                    "categoria": row[1],
                    "mensaje": f"Documento '{row[0]}' no se ha actualizado desde {row[2]}",
                    "prioridad": "media"
                })
        
        return {"alertas": alertas, "count": len(alertas)}
    except Exception as e:
        logger.error(f"Error getting alertas: {e}")
        return {"alertas": [], "count": 0, "error": str(e)}


@router.get("/solicitudes")
async def get_solicitudes(agente_id: Optional[str] = None):
    """Get pending document requests from agents."""
    if not agent_kb_service:
        return {"solicitudes": [], "count": 0}
    
    try:
        solicitudes = await agent_kb_service.get_solicitudes_pendientes(agente_id)
        return {"solicitudes": solicitudes, "count": len(solicitudes)}
    except Exception as e:
        logger.error(f"Error getting solicitudes: {e}")
        return {"solicitudes": [], "count": 0, "error": str(e)}


@router.post("/solicitudes")
async def crear_solicitud(
    request: SolicitudRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a document request."""
    try:
        if not request or not request.categoria:
            raise HTTPException(status_code=400, detail="categoria es requerida")

        if not agent_kb_service:
            raise HTTPException(status_code=503, detail="Servicio no inicializado")

        solicitud_id = await agent_kb_service.crear_solicitud(
            categoria=request.categoria,
            descripcion=request.descripcion or "",
            solicitado_por=request.solicitado_por or "sistema",
            razon=request.razon or "",
            prioridad=request.prioridad or "media"
        )

        if solicitud_id:
            return {"success": True, "id": solicitud_id}
        else:
            raise HTTPException(status_code=503, detail="No se pudo crear la solicitud")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating solicitud: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/agente/{agente_id}/contexto")
async def get_contexto_agente(
    agente_id: str,
    query: str
):
    """Get RAG context for a specific agent."""
    if not agent_kb_service:
        return {"contexto": "", "agente_id": agente_id}
    
    try:
        contexto = await agent_kb_service.get_contexto_para_agente(agente_id, query)
        return {"contexto": contexto, "agente_id": agente_id}
    except Exception as e:
        logger.error(f"Error getting agent context: {e}")
        return {"contexto": "", "agente_id": agente_id, "error": str(e)}


@router.get("/agente/{agente_id}/chunks")
async def get_chunks_agente(
    agente_id: str,
    limit: int = 20
):
    """Get chunks assigned to a specific agent."""
    if not session_factory:
        return {"chunks": [], "agente_id": agente_id}
    
    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            result = await session.execute(
                text('''
                    SELECT c.id, c.contenido, c.articulo, c.tipo_contenido,
                           d.nombre, d.ley_codigo, ca.score_relevancia, ca.es_conocimiento_core
                    FROM kb_chunks c
                    JOIN kb_documentos d ON d.id = c.documento_id
                    JOIN kb_chunk_agente ca ON ca.chunk_id = c.id
                    WHERE ca.agente_id = :agente
                    ORDER BY ca.score_relevancia DESC
                    LIMIT :limit
                '''),
                {'agente': agente_id, 'limit': limit}
            )
            
            chunks = [{
                "id": str(row[0]),
                "contenido": row[1][:300] + "..." if len(row[1]) > 300 else row[1],
                "articulo": row[2],
                "tipo_contenido": row[3],
                "documento": row[4],
                "ley_codigo": row[5],
                "score_relevancia": row[6],
                "es_conocimiento_core": row[7]
            } for row in result.fetchall()]
            
            return {"chunks": chunks, "agente_id": agente_id, "count": len(chunks)}
    except Exception as e:
        logger.error(f"Error getting agent chunks: {e}")
        return {"chunks": [], "agente_id": agente_id, "error": str(e)}


class VersionUpdateRequest(BaseModel):
    version: Optional[str] = None
    fecha_documento: Optional[str] = None
    ultima_reforma: Optional[str] = None
    notas_version: Optional[str] = None


@router.post("/documento/{doc_id}/reingestar")
async def reingestar_documento(
    doc_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Reprocess a document: delete previous chunks, increment attempts, and reprocess.
    """
    try:
        if not doc_id:
            raise HTTPException(status_code=400, detail="doc_id es requerido")

        if not session_factory:
            raise HTTPException(status_code=503, detail="Servicio no inicializado")

        if not rag_processor:
            raise HTTPException(status_code=503, detail="Procesador RAG no inicializado")
        from sqlalchemy import text
        from datetime import datetime
        
        async with session_factory() as session:
            doc_result = await session.execute(
                text('''
                    SELECT id, nombre, contenido_completo, categoria, empresa_id
                    FROM kb_documentos 
                    WHERE id = :doc_id
                '''),
                {'doc_id': doc_id}
            )
            doc = doc_result.fetchone()
            
            if not doc:
                raise HTTPException(status_code=404, detail=f"Documento {doc_id} no encontrado")
            
            logger.info(f"Reingestando documento: {doc[1]} (ID: {doc_id})")
            
            await session.execute(
                text('DELETE FROM kb_chunk_agente WHERE chunk_id IN (SELECT id FROM kb_chunks WHERE documento_id = :doc_id)'),
                {'doc_id': doc_id}
            )
            await session.execute(
                text('DELETE FROM kb_chunks WHERE documento_id = :doc_id'),
                {'doc_id': doc_id}
            )
            
            await session.execute(
                text('''
                    UPDATE kb_documentos 
                    SET procesado = FALSE,
                        intentos_proceso = COALESCE(intentos_proceso, 0) + 1,
                        ultimo_intento_proceso = :now,
                        total_chunks = 0
                    WHERE id = :doc_id
                '''),
                {'doc_id': doc_id, 'now': datetime.utcnow()}
            )
            await session.commit()
            
            contenido_texto = doc[2]
            if not contenido_texto:
                return {
                    "success": False,
                    "documento_id": doc_id,
                    "chunks": 0,
                    "mensaje": "Documento no tiene contenido de texto almacenado para reprocesar"
                }
            
            clasificacion = {
                'categoria': doc[3] or 'casos_referencia',
                'subcategoria': 'general',
                'ley_codigo': None,
                'version': None,
                'es_vigente': True,
                'fuente': 'otro',
                'metadata': {'titulo': doc[1]}
            }
            
            chunks = await rag_processor._crear_chunks_inteligentes(contenido_texto, clasificacion)
            
            from services.knowledge_base.embeddings_service import embeddings_service
            embeddings = await embeddings_service.generate_embeddings_batch(
                [c['contenido'] for c in chunks]
            )
            
            for i, chunk in enumerate(chunks):
                if embeddings and i < len(embeddings) and embeddings[i]:
                    chunk['embedding'] = embeddings[i]
                chunk['agentes'] = rag_processor._asignar_agentes(chunk['contenido'], clasificacion)
            
            import json as json_lib
            async with session_factory() as save_session:
                for idx, chunk in enumerate(chunks):
                    embedding = chunk.get('embedding')
                    embedding_str = None
                    if embedding:
                        embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                    
                    chunk_result = await save_session.execute(
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
                            'doc_id': doc_id,
                            'contenido': chunk['contenido'],
                            'embedding': embedding_str,
                            'idx': idx,
                            'tokens': chunk.get('tokens', 0),
                            'meta': json_lib.dumps(chunk.get('metadata', {})),
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
                        await save_session.execute(
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
                
                await save_session.execute(
                    text('''
                        UPDATE kb_documentos 
                        SET procesado = TRUE,
                            total_chunks = :chunks,
                            error_procesamiento = NULL
                        WHERE id = :doc_id
                    '''),
                    {'doc_id': doc_id, 'chunks': len(chunks)}
                )
                await save_session.commit()
            
            logger.info(f"Documento {doc_id} reingesta exitosa: {len(chunks)} chunks creados")
            
            return {
                "success": True,
                "documento_id": doc_id,
                "chunks": len(chunks),
                "mensaje": f"Documento reprocesado exitosamente con {len(chunks)} chunks"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reingesting document {doc_id}: {e}")
        try:
            async with session_factory() as session:
                await session.execute(
                    text('''
                        UPDATE kb_documentos
                        SET error_procesamiento = :error
                        WHERE id = :doc_id
                    '''),
                    {'doc_id': doc_id, 'error': str(e)}
                )
                await session.commit()
        except:
            pass
        if "not found" in str(e).lower():
            status_code = 404
        elif "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/pendientes")
async def get_documentos_pendientes():
    """
    Get documents pending processing (procesado=FALSE and activo=TRUE).
    """
    if not session_factory:
        return {"documentos": [], "total": 0}
    
    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            result = await session.execute(
                text('''
                    SELECT id, nombre, created_at, intentos_proceso, error_procesamiento
                    FROM kb_documentos
                    WHERE procesado = FALSE 
                      AND (activo = TRUE OR activo IS NULL)
                    ORDER BY created_at DESC
                ''')
            )
            docs = result.fetchall()
            
            return {
                "documentos": [{
                    "id": str(row[0]),
                    "nombre": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                    "intentos_proceso": row[3] or 0,
                    "error_procesamiento": row[4]
                } for row in docs],
                "total": len(docs)
            }
    except Exception as e:
        logger.error(f"Error getting pending documents: {e}")
        return {"documentos": [], "total": 0, "error": str(e)}


@router.post("/reingestar-todos")
async def reingestar_todos_pendientes(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Process all pending documents sequentially.
    """
    if not session_factory:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")

    if not rag_processor:
        raise HTTPException(status_code=503, detail="Procesador RAG no inicializado")

    try:
        from sqlalchemy import text
        
        pendientes_response = await get_documentos_pendientes()
        pendientes = pendientes_response.get("documentos", [])
        
        total = len(pendientes)
        exitosos = 0
        fallidos = 0
        errores = []
        
        logger.info(f"Iniciando reingesta de {total} documentos pendientes")
        
        for doc in pendientes:
            try:
                result = await reingestar_documento(doc["id"], credentials)
                if result.get("success"):
                    exitosos += 1
                else:
                    fallidos += 1
                    errores.append({
                        "documento_id": doc["id"],
                        "nombre": doc["nombre"],
                        "error": result.get("mensaje", "Error desconocido")
                    })
            except Exception as e:
                fallidos += 1
                errores.append({
                    "documento_id": doc["id"],
                    "nombre": doc["nombre"],
                    "error": str(e)
                })
        
        logger.info(f"Reingesta completada: {exitosos} exitosos, {fallidos} fallidos de {total} total")
        
        return {
            "total": total,
            "exitosos": exitosos,
            "fallidos": fallidos,
            "errores": errores
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk reingestion: {e}")
        if "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/documento/{doc_id}/stats")
async def get_documento_stats(doc_id: str):
    """
    Get detailed statistics for a specific document.
    """
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id es requerido")

    if not session_factory:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")

    try:
        from sqlalchemy import text
        
        async with session_factory() as session:
            doc_result = await session.execute(
                text('''
                    SELECT id, nombre, version, created_at, ultima_reforma, 
                           procesado, intentos_proceso, total_chunks, categoria,
                           ley_codigo, fecha_documento
                    FROM kb_documentos 
                    WHERE id = :doc_id
                '''),
                {'doc_id': doc_id}
            )
            doc = doc_result.fetchone()
            
            if not doc:
                raise HTTPException(status_code=404, detail=f"Documento {doc_id} no encontrado")
            
            chunks_result = await session.execute(
                text('''
                    SELECT 
                        COUNT(*) as total_chunks,
                        COUNT(DISTINCT articulo) FILTER (WHERE articulo IS NOT NULL) as total_articulos,
                        tipo_contenido,
                        COUNT(*) as count_por_tipo
                    FROM kb_chunks
                    WHERE documento_id = :doc_id
                    GROUP BY tipo_contenido
                '''),
                {'doc_id': doc_id}
            )
            chunks_stats = chunks_stats_raw = chunks_result.fetchall()
            
            chunks_por_tipo = {}
            total_chunks = 0
            total_articulos = 0
            for row in chunks_stats_raw:
                total_chunks = row[0] if row[0] else 0
                total_articulos = row[1] if row[1] else 0
                if row[2]:
                    chunks_por_tipo[row[2]] = row[3]
            
            agentes_result = await session.execute(
                text('''
                    SELECT DISTINCT ca.agente_id
                    FROM kb_chunk_agente ca
                    JOIN kb_chunks c ON c.id = ca.chunk_id
                    WHERE c.documento_id = :doc_id
                '''),
                {'doc_id': doc_id}
            )
            agentes = [row[0] for row in agentes_result.fetchall()]
            
            uso_result = await session.execute(
                text('''
                    SELECT COALESCE(SUM(veces_recuperado), 0)
                    FROM kb_chunks
                    WHERE documento_id = :doc_id
                '''),
                {'doc_id': doc_id}
            )
            veces_recuperado = uso_result.scalar() or 0
            
            return {
                "documento": {
                    "id": str(doc[0]),
                    "nombre": doc[1],
                    "version": doc[2],
                    "fecha_carga": doc[3].isoformat() if doc[3] else None,
                    "ultima_reforma": doc[4],
                    "procesado": doc[5],
                    "intentos_proceso": doc[6] or 0,
                    "categoria": doc[8],
                    "ley_codigo": doc[9],
                    "fecha_documento": doc[10].isoformat() if doc[10] else None
                },
                "estadisticas": {
                    "total_chunks": doc[7] or total_chunks,
                    "total_articulos": total_articulos,
                    "chunks_por_tipo": chunks_por_tipo,
                    "agentes_asignados": agentes,
                    "uso": {
                        "veces_recuperado": veces_recuperado
                    }
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document stats for {doc_id}: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.put("/documento/{doc_id}/version")
async def actualizar_version_documento(
    doc_id: str,
    request: VersionUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update document version fields.
    """
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id es requerido")

    if not request:
        raise HTTPException(status_code=400, detail="request es requerido")

    if not session_factory:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")

    try:
        from sqlalchemy import text
        from datetime import datetime
        
        async with session_factory() as session:
            doc_check = await session.execute(
                text('SELECT id FROM kb_documentos WHERE id = :doc_id'),
                {'doc_id': doc_id}
            )
            if not doc_check.fetchone():
                raise HTTPException(status_code=404, detail=f"Documento {doc_id} no encontrado")
            
            update_fields = []
            params = {'doc_id': doc_id}
            
            if request.version is not None:
                update_fields.append("version = :version")
                params['version'] = request.version
            
            if request.fecha_documento is not None:
                update_fields.append("fecha_documento = :fecha_documento")
                try:
                    params['fecha_documento'] = datetime.fromisoformat(request.fecha_documento.replace('Z', '+00:00'))
                except:
                    params['fecha_documento'] = request.fecha_documento
            
            if request.ultima_reforma is not None:
                update_fields.append("ultima_reforma = :ultima_reforma")
                params['ultima_reforma'] = request.ultima_reforma
            
            if request.notas_version is not None:
                update_fields.append("notas_version = :notas_version")
                params['notas_version'] = request.notas_version
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
            
            update_fields.append("updated_at = :updated_at")
            params['updated_at'] = datetime.utcnow()
            
            query = f"UPDATE kb_documentos SET {', '.join(update_fields)} WHERE id = :doc_id"
            await session.execute(text(query), params)
            await session.commit()
            
            result = await session.execute(
                text('''
                    SELECT id, nombre, version, fecha_documento, ultima_reforma, 
                           notas_version, updated_at
                    FROM kb_documentos 
                    WHERE id = :doc_id
                '''),
                {'doc_id': doc_id}
            )
            updated = result.fetchone()
            
            logger.info(f"Documento {doc_id} version actualizada")
            
            return {
                "success": True,
                "documento": {
                    "id": str(updated[0]),
                    "nombre": updated[1],
                    "version": updated[2],
                    "fecha_documento": updated[3].isoformat() if updated[3] else None,
                    "ultima_reforma": updated[4],
                    "notas_version": updated[5],
                    "updated_at": updated[6].isoformat() if updated[6] else None
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document version for {doc_id}: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/estado-acervo")
async def get_estado_acervo():
    """
    Get the status of the required document collection (acervo) per agent.
    Returns loaded vs missing documents organized by agent (A1-A7).
    """
    from config.acervo_requerido import get_acervo_requerido, get_codigos_aceptados_map
    
    acervo_config = get_acervo_requerido()
    codigos_map = get_codigos_aceptados_map()
    
    documentos_cargados = {}
    chunks_por_documento = {}
    
    if session_factory:
        try:
            from sqlalchemy import text
            
            async with session_factory() as session:
                result = await session.execute(
                    text('''
                        SELECT 
                            d.id,
                            d.nombre,
                            d.ley_codigo,
                            d.categoria,
                            d.subcategoria,
                            COALESCE(d.total_chunks, 0) as total_chunks,
                            (SELECT COUNT(*) FROM kb_chunks WHERE documento_id = d.id) as chunks_count,
                            d.version,
                            d.created_at,
                            d.ultima_reforma,
                            d.procesado
                        FROM kb_documentos d
                        WHERE d.activo = TRUE OR d.activo IS NULL
                    ''')
                )
                docs = result.fetchall()
                
                for row in docs:
                    doc_id = str(row[0])
                    nombre = row[1] or ""
                    ley_codigo = row[2] or ""
                    categoria = row[3] or ""
                    subcategoria = row[4] or ""
                    chunks = max(row[5] or 0, row[6] or 0)
                    version = row[7] or "1.0"
                    created_at = row[8]
                    ultima_reforma = row[9]
                    procesado = row[10] if row[10] is not None else True
                    
                    check_values = [
                        ley_codigo.lower() if ley_codigo else "",
                        subcategoria.lower() if subcategoria else "",
                        categoria.lower() if categoria else "",
                        nombre.lower() if nombre else ""
                    ]
                    
                    doc_info = {
                        "doc_db_id": doc_id,
                        "nombre_db": nombre,
                        "chunks": chunks,
                        "version": version,
                        "fecha_carga": created_at.isoformat() if created_at else None,
                        "ultima_reforma": ultima_reforma,
                        "pendiente_procesar": not procesado
                    }
                    
                    for check_val in check_values:
                        if check_val and check_val in codigos_map:
                            match_info = codigos_map[check_val]
                            key = f"{match_info['agente_id']}_{match_info['documento_id']}"
                            if key not in documentos_cargados or chunks > chunks_por_documento.get(key, 0):
                                documentos_cargados[key] = doc_info
                                chunks_por_documento[key] = chunks
                    
                    for codigo, match_info in codigos_map.items():
                        if (codigo in nombre.lower() or 
                            codigo in (ley_codigo or "").lower() or
                            codigo in (subcategoria or "").lower()):
                            key = f"{match_info['agente_id']}_{match_info['documento_id']}"
                            if key not in documentos_cargados or chunks > chunks_por_documento.get(key, 0):
                                documentos_cargados[key] = doc_info
                                chunks_por_documento[key] = chunks
                
        except Exception as e:
            logger.error(f"Error querying documents for estado-acervo: {e}")
    
    agentes_response = []
    total_docs = 0
    total_cargados = 0
    
    for agente_id, agente_config in acervo_config.items():
        documentos_agente = []
        docs_cargados_agente = 0
        
        for doc in agente_config.get("documentos", []):
            key = f"{agente_id}_{doc['id']}"
            esta_cargado = key in documentos_cargados
            doc_info = documentos_cargados.get(key, {})
            chunks = chunks_por_documento.get(key, 0) if esta_cargado else 0
            
            documentos_agente.append({
                "id": doc["id"],
                "nombre": doc["nombre"],
                "descripcion": doc.get("descripcion", ""),
                "categoria": doc.get("categoria", ""),
                "criticidad": doc.get("criticidad", "recomendado"),
                "cargado": esta_cargado,
                "chunks_count": chunks,
                "url_descarga": doc.get("url_descarga"),
                "instrucciones": doc.get("instrucciones"),
                "documento_id": doc_info.get("doc_db_id") if esta_cargado else None,
                "version": doc_info.get("version", "1.0") if esta_cargado else None,
                "fecha_carga": doc_info.get("fecha_carga") if esta_cargado else None,
                "ultima_reforma": doc_info.get("ultima_reforma") if esta_cargado else None,
                "pendiente_procesar": doc_info.get("pendiente_procesar", False) if esta_cargado else False
            })
            
            total_docs += 1
            if esta_cargado:
                docs_cargados_agente += 1
                total_cargados += 1
        
        total_docs_agente = len(documentos_agente)
        progreso = int((docs_cargados_agente / total_docs_agente * 100)) if total_docs_agente > 0 else 0
        
        agentes_response.append({
            "id": agente_id,
            "nombre": agente_config.get("nombre", agente_id),
            "icono": agente_config.get("icono", "📄"),
            "descripcion": agente_config.get("descripcion", ""),
            "progreso": progreso,
            "docs_cargados": docs_cargados_agente,
            "docs_totales": total_docs_agente,
            "documentos": documentos_agente
        })
    
    completitud_global = int((total_cargados / total_docs * 100)) if total_docs > 0 else 0
    
    total_pendientes = sum(
        1 for agente in agentes_response 
        for doc in agente.get("documentos", []) 
        if doc.get("pendiente_procesar", False)
    )
    
    return {
        "completitud_global": completitud_global,
        "total_documentos": total_docs,
        "documentos_cargados": total_cargados,
        "documentos_pendientes": total_pendientes,
        "agentes": agentes_response
    }
