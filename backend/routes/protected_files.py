"""
Protected file download endpoints with multi-tenant isolation.
Replaces direct StaticFiles mounts for /uploads and /reports.
"""
import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from middleware.tenant_context import (
    get_current_tenant,
    get_current_empresa_id,
    require_empresa,
    require_auth,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Protected Files"])

ROOT_DIR = Path(__file__).parent.parent
UPLOADS_DIR = ROOT_DIR / "uploads"
REPORTS_DIR = ROOT_DIR / "reports"


@router.get("/uploads/{filename}")
@require_auth
async def download_upload(filename: str):
    """
    Download a file from the uploads directory.
    Requires authentication.
    """
    file_path = UPLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    try:
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(UPLOADS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/uploads/kb/{filename}")
async def download_kb_upload(filename: str):
    """
    Download a file from the KB uploads directory.
    No auth required as KB files are public within the system.
    """
    kb_dir = UPLOADS_DIR / "kb"
    file_path = kb_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    try:
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(kb_dir.resolve())):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/reports/{filename}")
@require_empresa
async def download_report(filename: str):
    """
    Download a report file.
    Requires authentication and valid empresa context.
    Report filenames contain project IDs which should be validated against empresa.
    """
    context = get_current_tenant()
    empresa_id = get_current_empresa_id()
    
    file_path = REPORTS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    try:
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(REPORTS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    logger.info(f"Report download: user={context.user_id} empresa={empresa_id} file={filename}")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/documents/{empresa_id}/{filename}")
@require_empresa
async def download_empresa_document(empresa_id: str, filename: str):
    """
    Download a document from an empresa-specific directory.
    Validates that the user has access to the specified empresa.
    """
    context = get_current_tenant()
    current_empresa = get_current_empresa_id()
    
    if current_empresa.lower() != empresa_id.lower():
        if not context.is_admin:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a documentos de esta empresa"
            )
    
    doc_path = UPLOADS_DIR / "documentos" / empresa_id / filename
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if not doc_path.is_file():
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        resolved = doc_path.resolve()
        if not str(resolved).startswith(str(UPLOADS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    logger.info(f"Document download: user={context.user_id} empresa={empresa_id} file={filename}")
    
    return FileResponse(
        path=str(doc_path),
        filename=filename,
        media_type="application/octet-stream"
    )
