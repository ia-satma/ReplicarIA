"""
Rutas de Gestión de Documentos - Revisar.IA
Endpoints para carga, listado y gestión de documentos de proyectos
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional, List
import hashlib
from datetime import datetime
import os
import logging

router = APIRouter(prefix="/api", tags=["documentos"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads/documentos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

documentos_db = {}


@router.post("/proyectos/{proyecto_id}/documentos")
async def cargar_documento(
    proyecto_id: str,
    archivo: UploadFile = File(...),
    tipo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    fase_asociada: str = Form(...)
):
    """Carga un documento asociado a un proyecto y fase"""
    
    try:
        contenido = await archivo.read()
        
        if len(contenido) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Archivo excede 50MB")
        
        hash_sha256 = hashlib.sha256(contenido).hexdigest()
        
        extensiones_permitidas = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.xml'
        ]
        
        nombre_archivo = archivo.filename or "documento"
        extension = os.path.splitext(nombre_archivo)[1].lower()
        
        if extension not in extensiones_permitidas:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de archivo no permitido: {extension}"
            )
        
        doc_id = f"doc_{hash_sha256[:12]}"
        timestamp = datetime.now().isoformat()
        
        ruta_archivo = os.path.join(UPLOAD_DIR, proyecto_id)
        os.makedirs(ruta_archivo, exist_ok=True)
        
        nombre_guardado = f"{doc_id}_{nombre_archivo}"
        ruta_completa = os.path.join(ruta_archivo, nombre_guardado)
        
        with open(ruta_completa, 'wb') as f:
            f.write(contenido)
        
        documento = {
            "id": doc_id,
            "proyecto_id": proyecto_id,
            "nombre_archivo": nombre_archivo,
            "tipo": tipo,
            "descripcion": descripcion or nombre_archivo,
            "fase_asociada": fase_asociada,
            "hash_sha256": hash_sha256,
            "tamano_bytes": len(contenido),
            "content_type": archivo.content_type,
            "fecha_carga": timestamp,
            "ruta_local": ruta_completa,
            "url_descarga": f"/api/proyectos/{proyecto_id}/documentos/{doc_id}/descargar",
            "pcloud_link": None,
            "validacion_ocr": None
        }
        
        if proyecto_id not in documentos_db:
            documentos_db[proyecto_id] = []
        documentos_db[proyecto_id].append(documento)
        
        logger.info(f"Documento cargado: {doc_id} para proyecto {proyecto_id}")
        
        return {
            "success": True,
            "documento": documento,
            "mensaje": f"Documento '{nombre_archivo}' cargado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cargando documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/proyectos/{proyecto_id}/documentos")
async def listar_documentos(
    proyecto_id: str,
    fase: Optional[str] = None
):
    """Lista todos los documentos de un proyecto"""
    
    docs = documentos_db.get(proyecto_id, [])
    
    if fase:
        docs = [d for d in docs if d.get("fase_asociada") == fase]
    
    docs_ordenados = sorted(
        docs, 
        key=lambda x: x.get("fecha_carga", ""), 
        reverse=True
    )
    
    return {
        "documentos": docs_ordenados,
        "total": len(docs_ordenados),
        "proyecto_id": proyecto_id
    }


@router.get("/proyectos/{proyecto_id}/documentos/{documento_id}")
async def obtener_documento(proyecto_id: str, documento_id: str):
    """Obtiene información de un documento específico"""
    
    docs = documentos_db.get(proyecto_id, [])
    
    for doc in docs:
        if doc.get("id") == documento_id:
            return {"documento": doc}
    
    raise HTTPException(status_code=404, detail="Documento no encontrado")


@router.delete("/proyectos/{proyecto_id}/documentos/{documento_id}")
async def eliminar_documento(proyecto_id: str, documento_id: str):
    """Elimina un documento (soft delete)"""
    
    docs = documentos_db.get(proyecto_id, [])
    
    for i, doc in enumerate(docs):
        if doc.get("id") == documento_id:
            doc_eliminado = docs.pop(i)
            
            logger.info(f"Documento eliminado: {documento_id}")
            
            return {
                "success": True,
                "mensaje": f"Documento '{doc_eliminado.get('nombre_archivo')}' eliminado"
            }
    
    raise HTTPException(status_code=404, detail="Documento no encontrado")


@router.get("/proyectos/{proyecto_id}/documentos/resumen")
async def resumen_documentos(proyecto_id: str):
    """Obtiene resumen de documentos por fase"""
    
    docs = documentos_db.get(proyecto_id, [])
    
    resumen = {
        "total": len(docs),
        "por_fase": {},
        "por_tipo": {},
        "tipos_faltantes": []
    }
    
    fases = ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9']
    for fase in fases:
        docs_fase = [d for d in docs if d.get("fase_asociada") == fase]
        resumen["por_fase"][fase] = len(docs_fase)
    
    for doc in docs:
        tipo = doc.get("tipo", "OTRO")
        resumen["por_tipo"][tipo] = resumen["por_tipo"].get(tipo, 0) + 1
    
    return resumen
