from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import os
import uuid
import logging
import tempfile
import aiofiles
from datetime import datetime

from services.pcloud_service import pcloud_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])
security = HTTPBearer(auto_error=False)

ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt',
    '.png', '.jpg', '.jpeg', '.gif', '.webp',
    '.xml', '.json'
}

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'text/plain',
    'image/png',
    'image/jpeg',
    'image/jpg',
    'image/gif',
    'image/webp',
    'application/xml',
    'text/xml',
    'application/json'
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def clasificar_documento(nombre: str, mime_type: str) -> str:
    nombre_lower = nombre.lower()
    
    if 'contrato' in nombre_lower:
        return 'contrato'
    if 'factura' in nombre_lower or 'cfdi' in nombre_lower:
        return 'factura'
    if 'estado' in nombre_lower and 'financiero' in nombre_lower:
        return 'estado_financiero'
    if 'presupuesto' in nombre_lower:
        return 'presupuesto'
    if 'cronograma' in nombre_lower:
        return 'cronograma'
    if 'propuesta' in nombre_lower:
        return 'propuesta'
    if 'plan' in nombre_lower:
        return 'plan_estrategico'
    if 'acta' in nombre_lower:
        return 'acta'
    if '32-d' in nombre_lower or '32d' in nombre_lower:
        return 'opinion_32d'
    if '69-b' in nombre_lower or '69b' in nombre_lower:
        return 'verificacion_69b'
    
    if mime_type == 'application/pdf':
        return 'documento_pdf'
    if 'spreadsheet' in mime_type or 'excel' in mime_type:
        return 'hoja_calculo'
    if 'word' in mime_type:
        return 'documento_word'
    if mime_type.startswith('image/'):
        return 'imagen'
    if 'xml' in mime_type:
        return 'xml'
    if 'json' in mime_type:
        return 'json'
    
    return 'otro'


def construir_ruta_pcloud(empresa_id: str, proveedor_id: Optional[str] = None, tipo_documento: Optional[str] = None) -> str:
    ruta = f"/Revisar.IA/Empresas/{empresa_id}"
    
    if proveedor_id:
        ruta += f"/Proveedores/{proveedor_id}"
    
    carpetas_tipo = {
        'contrato': 'Contratos',
        'factura': 'Facturas',
        'estado_financiero': 'Financieros',
        'presupuesto': 'Presupuestos',
        'cronograma': 'Cronogramas',
        'propuesta': 'Propuestas',
        'plan_estrategico': 'Planes',
        'acta': 'Actas',
        'opinion_32d': 'Fiscales',
        'verificacion_69b': 'Fiscales'
    }
    
    if tipo_documento and tipo_documento in carpetas_tipo:
        ruta += f"/{carpetas_tipo[tipo_documento]}"
    else:
        ruta += '/Documentos'
    
    return ruta


def generar_respuesta_archivos(archivos: list, mensaje_usuario: Optional[str] = None) -> str:
    emoji = '📄' if len(archivos) == 1 else '📁'
    
    respuesta = f"{emoji} **Archivos recibidos correctamente**\n\n"
    respuesta += f"He recibido **{len(archivos)} archivo(s)**:\n\n"
    
    iconos = {
        'contrato': '📝',
        'factura': '🧾',
        'estado_financiero': '📊',
        'presupuesto': '💰',
        'cronograma': '📅',
        'propuesta': '📋',
        'plan_estrategico': '🎯',
        'documento_pdf': '📕',
        'hoja_calculo': '📗',
        'documento_word': '📘',
        'imagen': '🖼️',
        'xml': '📄',
        'json': '📋',
        'otro': '📎'
    }
    
    for archivo in archivos:
        icono = iconos.get(archivo.get('tipo', 'otro'), '📎')
        nombre = archivo.get('nombre', 'Sin nombre')
        tamano = archivo.get('tamaño', 0)
        tamano_str = f"{tamano / 1024:.1f} KB" if tamano < 1024 * 1024 else f"{tamano / (1024 * 1024):.1f} MB"
        respuesta += f"{icono} **{nombre}** ({tamano_str})\n"
        respuesta += f"   Tipo: {archivo.get('tipo', 'otro').replace('_', ' ').title()}\n"
        if archivo.get('pcloudLink'):
            respuesta += f"   Almacenado en la nube\n"
    
    if mensaje_usuario:
        respuesta += f"\n💬 Tu mensaje: \"{mensaje_usuario}\"\n"
    
    respuesta += "\nLos documentos están listos para análisis. ¿Deseas que los procese ahora?"
    
    return respuesta


@router.post("")
async def upload_files(
    files: List[UploadFile] = File(...),
    empresaId: Optional[str] = Form(None),
    proveedorId: Optional[str] = Form(None),
    proyectoId: Optional[str] = Form(None),
    mensaje: Optional[str] = Form(None),
    sessionId: Optional[str] = Form(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No se recibieron archivos")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 archivos permitidos")
    
    logger.info(f"📁 Recibidos {len(files)} archivo(s)")
    
    resultados = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                logger.warning(f"Tipo de archivo no permitido: {file.filename}")
                resultados.append({
                    "id": str(uuid.uuid4()),
                    "nombre": file.filename,
                    "tipo": "no_permitido",
                    "tamaño": 0,
                    "estado": "rechazado",
                    "error": f"Tipo de archivo no permitido: {ext}"
                })
                continue

            # Validate MIME type if provided
            declared_mime = file.content_type or ''
            if declared_mime and declared_mime not in ALLOWED_MIME_TYPES:
                # Allow if MIME is generic but extension is valid
                if declared_mime not in ('application/octet-stream', ''):
                    logger.warning(f"MIME type no permitido: {file.filename} ({declared_mime})")
                    resultados.append({
                        "id": str(uuid.uuid4()),
                        "nombre": file.filename,
                        "tipo": "mime_no_permitido",
                        "tamaño": 0,
                        "estado": "rechazado",
                        "error": f"Tipo MIME no permitido: {declared_mime}"
                    })
                    continue

            content = await file.read()
            file_size = len(content)
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"Archivo muy grande: {file.filename} ({file_size} bytes)")
                resultados.append({
                    "id": str(uuid.uuid4()),
                    "nombre": file.filename,
                    "tipo": "muy_grande",
                    "tamaño": file_size,
                    "estado": "rechazado",
                    "error": "El archivo excede el límite de 10MB"
                })
                continue
            
            logger.info(f"   Procesando: {file.filename} ({file_size / 1024:.1f} KB)")
            
            tipo_documento = clasificar_documento(file.filename, file.content_type or '')
            
            file_id = str(uuid.uuid4())
            temp_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")
            
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(content)
            
            pcloud_result = None
            public_link = None
            
            if pcloud_service.is_available() and empresaId:
                try:
                    folder_path = construir_ruta_pcloud(empresaId, proveedorId, tipo_documento)
                    folder_id = await pcloud_service.ensure_folder_exists(folder_path)
                    
                    if folder_id:
                        pcloud_result = await pcloud_service.upload_file(temp_path, file.filename, folder_id)
                        
                        if pcloud_result and pcloud_result.get('fileId'):
                            public_link = await pcloud_service.get_public_link(pcloud_result['fileId'])
                        
                        logger.info(f"   ☁️ Subido a pCloud: {folder_path}")
                except Exception as pcloud_error:
                    logger.warning(f"   ⚠️ Error pCloud: {pcloud_error}")
            
            resultado = {
                "id": file_id,
                "nombre": file.filename,
                "tipo": tipo_documento,
                "mimeType": file.content_type,
                "tamaño": file_size,
                "pcloudFileId": pcloud_result.get('fileId') if pcloud_result else None,
                "pcloudPath": pcloud_result.get('path') if pcloud_result else None,
                "pcloudLink": public_link,
                "estado": "recibido",
                "fechaSubida": datetime.now().isoformat()
            }
            
            resultados.append(resultado)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"❌ Error en upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass  # Directory cleanup failed or not empty, not critical
    
    archivos_exitosos = [r for r in resultados if r.get('estado') == 'recibido']
    respuesta_chat = generar_respuesta_archivos(archivos_exitosos, mensaje)
    
    return {
        "success": True,
        "archivos": resultados,
        "mensaje": respuesta_chat,
        "total": len(resultados),
        "exitosos": len(archivos_exitosos),
        "rechazados": len(resultados) - len(archivos_exitosos)
    }


@router.get("/status")
async def upload_status():
    return {
        "pcloud_available": pcloud_service.is_available(),
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_files": 10
    }
