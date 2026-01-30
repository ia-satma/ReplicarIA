"""
Knowledge Base Routes for Bibliotecar.IA
Interactive KB management chatbot endpoints with real PostgreSQL RAG
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import shutil
import uuid
import logging
from services.bibliotecaria_service import BibliotecaService
from services.file_analysis_service import FileAnalysisService
from services.knowledge_base.kb_document_processor import kb_processor
from models.kb_models import (
    IngestionRequest, IngestionResult, KBDashboard,
    ChatMessage, DocumentType
)

logger = logging.getLogger(__name__)
file_analysis_service = FileAnalysisService()

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

biblioteca_service = BibliotecaService()

document_processor = kb_processor
session_factory = None

def init_kb_rag_services(sf, llm_client=None):
    global document_processor, session_factory
    session_factory = sf
    logger.info("KB RAG services initialized with PostgreSQL (kb_processor)")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime


class SearchRequest(BaseModel):
    query: str
    document_types: Optional[List[str]] = None
    max_results: int = 5


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    chunk_type: str


@router.get("/dashboard")
async def get_dashboard(
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
):
    """Get knowledge base dashboard summary with real PostgreSQL data"""
    try:
        empresa_id = int(x_empresa_id) if x_empresa_id and x_empresa_id.isdigit() else None
        stats = await kb_processor.get_kb_stats(empresa_id)
        completitud = stats.get("completitud", {})
        return {
            "total_documentos": stats.get("total_documentos", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "completitud_general": completitud.get("general", 0) / 100,
            "score_promedio": stats.get("promedio_calidad", 0) / 100,
            "por_categoria": stats.get("por_categoria", {}),
            "ultima_actualizacion": datetime.utcnow().isoformat(),
            "alertas": stats.get("alertas", []),
            "categorias": [
                {
                    "nombre": {"marco_legal": "Marco Legal", "jurisprudencias": "Jurisprudencias", 
                               "criterios_sat": "Criterios SAT", "catalogos_sat": "Catálogos SAT",
                               "casos_referencia": "Casos de Referencia", "glosarios": "Glosarios", 
                               "plantillas": "Plantillas"}.get(cat, cat.title()),
                    "icono": {"marco_legal": "⚖️", "jurisprudencias": "📜", "criterios_sat": "📋", 
                              "catalogos_sat": "📁", "casos_referencia": "📂", "glosarios": "📖", "plantillas": "📝"}.get(cat, "📄"),
                    "estado": "completo" if comp >= 80 else "actualizable" if comp >= 50 else "incompleto" if comp >= 20 else "critico",
                    "completitud": comp / 100,
                    "documentos": stats.get("por_categoria", {}).get(cat, 0),
                    "alertas": len([a for a in stats.get("alertas", []) if a.get("categoria") == cat]),
                    "ultima_actualizacion": datetime.utcnow().isoformat()
                }
                for cat, comp in completitud.items() if cat != "general"
            ],
            "solicitudes": []
        }
    except Exception as e:
        logger.error(f"Error getting real dashboard: {e}")
        return biblioteca_service.get_dashboard()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
) -> ChatResponse:
    """Send message to Bibliotecar.IA chatbot"""
    session_id = request.session_id or str(datetime.now().timestamp())
    
    response = biblioteca_service.process_message(
        session_id=session_id,
        user_message=request.message,
        empresa_id=x_empresa_id
    )
    
    return ChatResponse(
        response=response,
        session_id=session_id,
        timestamp=datetime.utcnow()
    )


@router.get("/chat/greeting")
async def get_greeting() -> Dict[str, str]:
    """Get Bibliotecar.IA greeting message"""
    return {"greeting": biblioteca_service.GREETING}


@router.get("/chat/session/{session_id}")
async def get_session_history(session_id: str) -> Dict[str, Any]:
    """Get chat session history"""
    context = biblioteca_service.get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in context.messages
        ]
    }


@router.post("/ingest")
async def ingest_document(
    request: IngestionRequest,
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict[str, Any]:
    """Ingest a new document into the knowledge base using PostgreSQL RAG"""
    try:
        empresa_id = int(x_empresa_id) if x_empresa_id and x_empresa_id.isdigit() else None
        result = await kb_processor.procesar_documento(
            content=request.content.encode('utf-8') if isinstance(request.content, str) else request.content,
            filename=request.title or "documento.txt",
            categoria=request.tipo.value if hasattr(request.tipo, 'value') else str(request.tipo),
            empresa_id=empresa_id,
            metadata={"usuario": x_user_id, "descripcion": request.content[:500]}
        )
        return {
            "id": result.documento_id,
            "status": "success",
            "chunks_creados": result.chunks,
            "agentes_notificados": result.agentes_notificados,
            "errores": result.errores
        }
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        return {"id": None, "status": "error", "message": str(e)}


@router.post("/search")
async def search_kb(
    request: SearchRequest,
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
) -> List[SearchResult]:
    """Search the knowledge base using semantic search"""
    try:
        results = await kb_processor.search_semantic(
            query=request.query,
            limit=request.max_results,
            categoria=request.categoria if hasattr(request, 'categoria') else None,
            agente_id=request.agente_id if hasattr(request, 'agente_id') else None
        )
        
        return [
            SearchResult(
                content=r.get("contenido", "")[:500],
                source=r.get("source", ""),
                score=float(r.get("score", 0)),
                chunk_type=r.get("categoria", "general")
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        return []


@router.get("/versions/{ordenamiento}")
async def get_version_tree(ordenamiento: str) -> Dict[str, Any]:
    """Get version tree for an ordenamiento (e.g., CFF, LISR)"""
    return biblioteca_service.get_version_tree(ordenamiento)


@router.get("/alerts")
async def get_alerts() -> List[Dict[str, Any]]:
    """Get active KB alerts"""
    return [
        {
            "id": a.id,
            "tipo": a.tipo.value,
            "prioridad": a.prioridad.value,
            "mensaje": a.mensaje,
            "categoria": a.categoria,
            "accion": a.accion,
            "fecha": a.fecha_deteccion.isoformat()
        }
        for a in biblioteca_service.alerts
    ]


@router.get("/solicitudes")
async def get_solicitudes() -> List[Dict[str, Any]]:
    """Get pending document requests from agents"""
    return [
        {
            "id": s.id,
            "documento": s.documento,
            "razon": s.razon,
            "solicitado_por": s.solicitado_por,
            "prioridad": s.prioridad.value,
            "fecha": s.fecha_solicitud.isoformat()
        }
        for s in biblioteca_service.solicitudes
    ]


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get KB statistics"""
    return biblioteca_service.kb_service.get_stats()


@router.post("/index-directory")
async def index_directory(directory: Optional[str] = None) -> Dict[str, Any]:
    """Index all documents in a KB directory"""
    counts = biblioteca_service.kb_service.index_kb_directory(directory)
    return {
        "status": "completed",
        "documents_indexed": counts,
        "total": sum(counts.values())
    }


UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "kb"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-file")
async def upload_kb_file(
    file: UploadFile = File(...),
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
) -> Dict[str, Any]:
    """Upload, analyze and process a file for the knowledge base RAG"""
    try:
        if not file:
            raise HTTPException(status_code=400, detail="File es requerido")

        filename = file.filename or "upload"
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"kb_{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        content = await file.read()
        with file_path.open("wb") as buffer:
            buffer.write(content)
        
        file_url = f"/api/files/uploads/kb/{unique_filename}"
        
        extracted_text = ""
        analysis_success = False
        
        try:
            if file_extension == '.pdf':
                extracted_text = file_analysis_service.extract_text_from_pdf(str(file_path))
            elif file_extension in ['.docx', '.doc']:
                extracted_text = file_analysis_service.extract_text_from_docx(str(file_path))
            elif file_extension in ['.txt', '.md', '.csv', '.json']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
            elif file_extension in ['.xlsx', '.xls']:
                extracted_text = f"[Archivo Excel - {filename}]"
            else:
                extracted_text = f"[Archivo {file_extension} - formato no soportado para análisis de texto]"
            
            if extracted_text and len(extracted_text.strip()) > 10 and not extracted_text.startswith('['):
                analysis_success = True
        except Exception as e:
            logger.warning(f"Could not extract text from {filename}: {e}")
            extracted_text = f"[No se pudo extraer texto del archivo {filename}: {str(e)}]"
        
        documento_id = None
        chunks_created = 0
        rag_processed = False
        pcloud_uploaded = False
        pcloud_link = None
        
        if analysis_success and extracted_text:
            try:
                from routes.biblioteca_routes import rag_processor
                if rag_processor:
                    result = await rag_processor.process_document(
                        file_content=content,
                        filename=filename,
                        categoria_hint="casos_referencia",
                        empresa_id=x_empresa_id
                    )
                    if result.get('success'):
                        documento_id = result.get('documento_id')
                        chunks_created = result.get('chunks_created', 0)
                        rag_processed = True
                        logger.info(f"Documento {filename} procesado RAG: {chunks_created} chunks")
                    else:
                        logger.warning(f"RAG processing failed for {filename}: {result.get('errors')}")
                else:
                    logger.warning("RAG processor not available, document stored but not indexed")
            except Exception as rag_error:
                logger.error(f"Error processing RAG for {filename}: {rag_error}")
        
        try:
            from services.pcloud_service import pcloud_service, AGENT_FOLDER_IDS
            if pcloud_service.is_available():
                login_result = pcloud_service.login()
                if login_result.get('success'):
                    kb_folder_id = AGENT_FOLDER_IDS.get("KNOWLEDGE_BASE", 0)
                    if kb_folder_id:
                        upload_result = pcloud_service.upload_file(kb_folder_id, filename, content)
                        if upload_result.get('success'):
                            pcloud_uploaded = True
                            file_id = upload_result.get('file_id')
                            if file_id:
                                link_result = pcloud_service.get_or_create_public_link(file_id)
                                if link_result.get('success'):
                                    pcloud_link = link_result.get('link')
                            logger.info(f"Documento {filename} respaldado en pCloud")
                        else:
                            logger.warning(f"pCloud upload failed: {upload_result.get('error')}")
        except Exception as pcloud_error:
            logger.warning(f"Error uploading to pCloud: {pcloud_error}")
        
        msg_parts = []
        if rag_processed:
            msg_parts.append(f"RAG ({chunks_created} chunks)")
        if pcloud_uploaded:
            msg_parts.append("pCloud")
        
        if msg_parts:
            message = f"Archivo '{filename}' procesado y guardado en: {', '.join(msg_parts)}"
        else:
            message = f"Archivo '{filename}' analizado pero no guardado"
        
        return {
            "success": True,
            "file_url": file_url,
            "filename": filename,
            "size": file_path.stat().st_size,
            "extracted_text": extracted_text[:50000] if extracted_text else "",
            "analysis_success": analysis_success,
            "rag_processed": rag_processed,
            "documento_id": documento_id,
            "chunks_created": chunks_created,
            "pcloud_uploaded": pcloud_uploaded,
            "pcloud_link": pcloud_link,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading KB file: {e}")
        if "file" in str(e).lower() or "not found" in str(e).lower():
            status_code = 404
        elif "permission" in str(e).lower():
            status_code = 403
        elif "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=f"Error al subir archivo: {str(e)}")


@router.get("/documentos-lista")
async def get_documentos_lista(
    categoria: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
):
    """Get list of documents in the knowledge base with their status and chunk count."""
    try:
        if not kb_processor:
            raise HTTPException(status_code=503, detail="KB processor not initialized")

        pool = await kb_processor.get_pool()

        if not pool:
            raise HTTPException(status_code=503, detail="Database pool not available")
        async with pool.acquire() as conn:
            where_clauses = []
            params = []
            param_idx = 1
            
            if categoria:
                where_clauses.append(f"categoria = ${param_idx}")
                params.append(categoria)
                param_idx += 1
            
            if x_empresa_id:
                where_clauses.append(f"(empresa_id = ${param_idx} OR empresa_id IS NULL)")
                params.append(x_empresa_id)
                param_idx += 1
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            params.extend([limit, offset])
            
            docs = await conn.fetch(f"""
                SELECT 
                    d.id,
                    d.nombre,
                    d.tipo_archivo,
                    d.categoria,
                    d.subcategoria,
                    d.version,
                    d.estado,
                    d.procesado,
                    d.total_chunks,
                    d.created_at,
                    d.updated_at,
                    (SELECT COUNT(*) FROM kb_chunks WHERE documento_id = d.id) as chunks_actual
                FROM kb_documentos d
                {where_sql}
                ORDER BY d.created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """, *params)
            
            count_params = params[:-2] if params else []
            total = await conn.fetchval(f"""
                SELECT COUNT(*) FROM kb_documentos {where_sql}
            """, *count_params) if count_params else await conn.fetchval("SELECT COUNT(*) FROM kb_documentos")
            
            pendientes = await conn.fetchval(f"""
                SELECT COUNT(*) FROM kb_documentos WHERE procesado = FALSE OR procesado IS NULL
            """)
            
            return {
                "documentos": [
                    {
                        "id": str(doc["id"]),
                        "nombre": doc["nombre"],
                        "tipo_archivo": doc["tipo_archivo"] or "txt",
                        "categoria": doc["categoria"],
                        "subcategoria": doc["subcategoria"],
                        "version": doc["version"],
                        "estado": "procesado" if doc["procesado"] else "pendiente",
                        "chunks": doc["chunks_actual"] or doc["total_chunks"] or 0,
                        "created_at": doc["created_at"].isoformat() if doc["created_at"] else None,
                        "updated_at": doc["updated_at"].isoformat() if doc["updated_at"] else None
                    }
                    for doc in docs
                ],
                "total": total or 0,
                "pendientes": pendientes or 0,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error getting documentos lista: {e}")
        return {
            "documentos": [],
            "total": 0,
            "pendientes": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e)
        }


@router.post("/reingest/{documento_id}")
async def reingest_documento(
    documento_id: str,
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
):
    """Re-ingest a document to regenerate its chunks."""
    try:
        pool = await kb_processor.get_pool()
        async with pool.acquire() as conn:
            doc = await conn.fetchrow("""
                SELECT id, nombre, contenido_completo, categoria, empresa_id
                FROM kb_documentos WHERE id = $1
            """, documento_id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Documento no encontrado")
            
            await conn.execute("""
                DELETE FROM kb_chunks WHERE documento_id = $1
            """, documento_id)
            
            await conn.execute("""
                UPDATE kb_documentos SET procesado = FALSE, total_chunks = 0, updated_at = NOW()
                WHERE id = $1
            """, documento_id)
            
            if doc["contenido_completo"]:
                result = await kb_processor.procesar_documento(
                    content=doc["contenido_completo"].encode('utf-8') if isinstance(doc["contenido_completo"], str) else doc["contenido_completo"],
                    filename=doc["nombre"],
                    categoria=doc["categoria"],
                    empresa_id=doc["empresa_id"]
                )
                return {
                    "success": True,
                    "documento_id": documento_id,
                    "chunks_created": result.chunks,
                    "message": f"Documento reingestado con {result.chunks} chunks"
                }
            else:
                return {
                    "success": False,
                    "documento_id": documento_id,
                    "message": "No se encontró contenido para reprocesar"
                }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reingesting document {documento_id}: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


AGENT_REQUIREMENTS = {
    "A1_ESTRATEGIA": {
        "id": "A1",
        "nombre": "ESTRATEGIA",
        "descripcion": "Visión Estratégica",
        "color": "from-blue-500 to-cyan-500",
        "icono": "🎯",
        "documentos_requeridos": [
            {"nombre": "Plan de Negocios", "categoria": "casos_referencia", "keywords": ["plan", "negocios", "estrategia"]},
            {"nombre": "Contratos Marco", "categoria": "plantillas", "keywords": ["contrato", "marco"]},
            {"nombre": "Visión y Pilares", "categoria": "casos_referencia", "keywords": ["vision", "pilares", "estrategico"]},
            {"nombre": "OKRs Vigentes", "categoria": "casos_referencia", "keywords": ["okr", "objetivos"]}
        ]
    },
    "A2_PMO": {
        "id": "A2",
        "nombre": "PMO",
        "descripcion": "Project Management",
        "color": "from-purple-500 to-pink-500",
        "icono": "📊",
        "documentos_requeridos": [
            {"nombre": "Cronogramas", "categoria": "plantillas", "keywords": ["cronograma", "timeline"]},
            {"nombre": "Metodologías", "categoria": "plantillas", "keywords": ["metodologia", "proceso"]},
            {"nombre": "POE Fases F0-F9", "categoria": "plantillas", "keywords": ["poe", "fases"]},
            {"nombre": "Checklists Tipología", "categoria": "plantillas", "keywords": ["checklist", "tipologia"]}
        ]
    },
    "A3_FISCAL": {
        "id": "A3",
        "nombre": "FISCAL",
        "descripcion": "Cumplimiento Fiscal",
        "color": "from-green-500 to-emerald-500",
        "icono": "⚖️",
        "documentos_requeridos": [
            {"nombre": "CFF (Código Fiscal)", "categoria": "marco_legal", "keywords": ["cff", "codigo fiscal"]},
            {"nombre": "LISR", "categoria": "marco_legal", "keywords": ["lisr", "impuesto sobre la renta"]},
            {"nombre": "LIVA", "categoria": "marco_legal", "keywords": ["liva", "iva"]},
            {"nombre": "RMF", "categoria": "marco_legal", "keywords": ["rmf", "resolucion miscelanea"]},
            {"nombre": "Criterios SAT", "categoria": "criterios_sat", "keywords": ["criterio", "sat"]}
        ]
    },
    "A4_LEGAL": {
        "id": "A4",
        "nombre": "LEGAL",
        "descripcion": "Revisión Legal",
        "color": "from-amber-500 to-orange-500",
        "icono": "📜",
        "documentos_requeridos": [
            {"nombre": "Contratos Tipo", "categoria": "plantillas", "keywords": ["contrato", "tipo", "modelo"]},
            {"nombre": "Jurisprudencia", "categoria": "jurisprudencias", "keywords": ["jurisprudencia", "tesis"]},
            {"nombre": "Marco Legal", "categoria": "marco_legal", "keywords": ["marco", "legal", "ley"]},
            {"nombre": "NOM-151 Digitalización", "categoria": "marco_legal", "keywords": ["nom", "151", "digital"]}
        ]
    },
    "A5_FINANZAS": {
        "id": "A5",
        "nombre": "FINANZAS",
        "descripcion": "Análisis Financiero",
        "color": "from-teal-500 to-green-500",
        "icono": "💰",
        "documentos_requeridos": [
            {"nombre": "Estados Financieros", "categoria": "casos_referencia", "keywords": ["estado", "financiero", "balance"]},
            {"nombre": "NIF", "categoria": "marco_legal", "keywords": ["nif", "norma", "financiera"]},
            {"nombre": "Políticas Presupuestales", "categoria": "plantillas", "keywords": ["politica", "presupuesto"]},
            {"nombre": "Benchmarks ROI", "categoria": "casos_referencia", "keywords": ["benchmark", "roi"]}
        ]
    },
    "A6_PROVEEDOR": {
        "id": "A6",
        "nombre": "PROVEEDOR",
        "descripcion": "Verificación Proveedores",
        "color": "from-red-500 to-rose-500",
        "icono": "🔍",
        "documentos_requeridos": [
            {"nombre": "Lista 69-B", "categoria": "catalogos_sat", "keywords": ["69b", "69-b", "lista"]},
            {"nombre": "Criterios EFOS", "categoria": "catalogos_sat", "keywords": ["efos", "factura", "operacion"]},
            {"nombre": "Opiniones Cumplimiento", "categoria": "catalogos_sat", "keywords": ["opinion", "cumplimiento"]},
            {"nombre": "Guía Entregables", "categoria": "plantillas", "keywords": ["guia", "entregable"]}
        ]
    },
    "A7_DEFENSA": {
        "id": "A7",
        "nombre": "DEFENSA",
        "descripcion": "Expedientes de Defensa",
        "color": "from-indigo-500 to-violet-500",
        "icono": "🛡️",
        "documentos_requeridos": [
            {"nombre": "CFF Extracto", "categoria": "marco_legal", "keywords": ["cff", "codigo fiscal"]},
            {"nombre": "LISR Extracto", "categoria": "marco_legal", "keywords": ["lisr", "renta"]},
            {"nombre": "Jurisprudencia TFJA", "categoria": "jurisprudencias", "keywords": ["jurisprudencia", "tfja"]},
            {"nombre": "Tesis Aisladas", "categoria": "jurisprudencias", "keywords": ["tesis", "aislada"]},
            {"nombre": "Criterios Defendibilidad", "categoria": "jurisprudencias", "keywords": ["defendibilidad", "defensa"]}
        ]
    }
}


@router.get("/agent-requirements")
async def get_agent_requirements(
    x_empresa_id: Optional[str] = Header(None, alias="X-Empresa-ID")
):
    """Get document requirements for each agent and their completion status."""
    try:
        if not kb_processor:
            raise HTTPException(status_code=503, detail="KB processor not initialized")

        pool = await kb_processor.get_pool()

        if not pool:
            raise HTTPException(status_code=503, detail="Database pool not available")
        async with pool.acquire() as conn:
            docs = await conn.fetch("""
                SELECT id, nombre, categoria, subcategoria
                FROM kb_documentos
                WHERE procesado = TRUE OR procesado IS NULL
            """)
            
            doc_list = [
                {
                    "id": str(doc["id"]),
                    "nombre": (doc["nombre"] or "").lower(),
                    "categoria": doc["categoria"] or "",
                    "subcategoria": doc["subcategoria"] or ""
                }
                for doc in docs
            ]
            
            def check_documento_exists(req):
                categoria = req.get("categoria", "")
                keywords = req.get("keywords", [])
                
                for doc in doc_list:
                    if categoria and doc["categoria"] == categoria:
                        for kw in keywords:
                            if kw.lower() in doc["nombre"]:
                                return True
                return False
            
            agentes_result = []
            total_requeridos = 0
            total_disponibles = 0
            agentes_listos = 0
            
            for agent_id, agent_data in AGENT_REQUIREMENTS.items():
                docs_requeridos = agent_data["documentos_requeridos"]
                docs_status = []
                disponibles = 0
                
                for doc_req in docs_requeridos:
                    existe = check_documento_exists(doc_req)
                    docs_status.append({
                        "nombre": doc_req["nombre"],
                        "categoria": doc_req["categoria"],
                        "disponible": existe
                    })
                    if existe:
                        disponibles += 1
                
                total = len(docs_requeridos)
                completitud = (disponibles / total * 100) if total > 0 else 0
                
                total_requeridos += total
                total_disponibles += disponibles
                
                if completitud == 100:
                    agentes_listos += 1
                
                agentes_result.append({
                    "id": agent_data["id"],
                    "agent_id": agent_id,
                    "nombre": agent_data["nombre"],
                    "descripcion": agent_data["descripcion"],
                    "color": agent_data["color"],
                    "icono": agent_data["icono"],
                    "documentos": docs_status,
                    "total_requeridos": total,
                    "disponibles": disponibles,
                    "completitud": round(completitud, 1),
                    "listo": completitud == 100
                })
            
            completitud_general = (total_disponibles / total_requeridos * 100) if total_requeridos > 0 else 0
            
            return {
                "agentes": agentes_result,
                "resumen": {
                    "total_agentes": len(agentes_result),
                    "agentes_listos": agentes_listos,
                    "agentes_pendientes": len(agentes_result) - agentes_listos,
                    "total_documentos_requeridos": total_requeridos,
                    "total_documentos_disponibles": total_disponibles,
                    "completitud_general": round(completitud_general, 1)
                }
            }
    except Exception as e:
        logger.error(f"Error getting agent requirements: {e}")
        agentes_result = []
        for agent_id, agent_data in AGENT_REQUIREMENTS.items():
            docs_status = [
                {"nombre": doc["nombre"], "categoria": doc["categoria"], "disponible": False}
                for doc in agent_data["documentos_requeridos"]
            ]
            agentes_result.append({
                "id": agent_data["id"],
                "agent_id": agent_id,
                "nombre": agent_data["nombre"],
                "descripcion": agent_data["descripcion"],
                "color": agent_data["color"],
                "icono": agent_data["icono"],
                "documentos": docs_status,
                "total_requeridos": len(docs_status),
                "disponibles": 0,
                "completitud": 0,
                "listo": False
            })
        
        return {
            "agentes": agentes_result,
            "resumen": {
                "total_agentes": len(agentes_result),
                "agentes_listos": 0,
                "agentes_pendientes": len(agentes_result),
                "total_documentos_requeridos": sum(len(a["documentos"]) for a in agentes_result),
                "total_documentos_disponibles": 0,
                "completitud_general": 0
            },
            "error": str(e)
        }
