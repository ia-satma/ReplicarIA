"""
Vision Agent API Routes
Endpoints para validación de documentos PDF
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import logging

from services.vision_agent import vision_agent, ValidationResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/validate")
async def validate_document(
    file: UploadFile = File(...),
    doc_type: str = Form("contrato"),
    expected_monto: Optional[float] = Form(None),
    expected_fecha: Optional[str] = Form(None),
    expected_proveedor: Optional[str] = Form(None),
    expected_rfc: Optional[str] = Form(None),
    expected_uuid: Optional[str] = Form(None)
):
    """
    Valida un documento PDF subido.
    
    - **file**: Archivo PDF a validar
    - **doc_type**: Tipo de documento (contrato, factura, sow, comprobante, etc.)
    - **expected_monto**: Monto esperado para validación cruzada
    - **expected_fecha**: Fecha esperada (formato YYYY-MM-DD o DD/MM/YYYY)
    - **expected_proveedor**: Nombre del proveedor esperado
    - **expected_rfc**: RFC esperado
    - **expected_uuid**: UUID de CFDI esperado
    """
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    try:
        content = await file.read()
        
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 10MB)")
        
        expected_data = {}
        if expected_monto:
            expected_data["monto"] = expected_monto
        if expected_fecha:
            expected_data["fecha"] = expected_fecha
        if expected_proveedor:
            expected_data["proveedor"] = expected_proveedor
        if expected_rfc:
            expected_data["rfc"] = expected_rfc
        if expected_uuid:
            expected_data["uuid"] = expected_uuid
        
        result = vision_agent.validate_document(
            file_content=content,
            doc_type=doc_type,
            expected_data=expected_data
        )
        
        logger.info(f"Documento validado: {file.filename} - Score: {result.score}")
        
        return {
            "success": True,
            "filename": file.filename,
            "validation": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error validando documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-f5")
async def validate_f5_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    budget: Optional[float] = Form(None),
    start_date: Optional[str] = Form(None),
    vendor_name: Optional[str] = Form(None),
    vendor_rfc: Optional[str] = Form(None)
):
    """
    Validación específica para Fase F5 (Entrega Final).
    Bloquea documentos con score < 70.
    """
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    try:
        content = await file.read()
        
        project_data = {
            "project_id": project_id,
            "budget": budget,
            "start_date": start_date,
            "vendor_name": vendor_name,
            "vendor_rfc": vendor_rfc
        }
        
        result = vision_agent.validate_f5_document(content, project_data)
        
        if result.score < 70:
            return {
                "success": False,
                "blocked": True,
                "filename": file.filename,
                "validation": result.to_dict(),
                "message": f"Documento rechazado (score: {result.score}/100). Requiere revisión manual."
            }
        
        return {
            "success": True,
            "blocked": False,
            "filename": file.filename,
            "validation": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error en validación F5: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-cfdi")
async def validate_cfdi(
    file: UploadFile = File(...),
    expected_rfc: Optional[str] = Form(None),
    expected_uuid: Optional[str] = Form(None),
    expected_total: Optional[float] = Form(None)
):
    """Validación específica para facturas CFDI"""
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    try:
        content = await file.read()
        
        expected_data = {}
        if expected_rfc:
            expected_data["rfc"] = expected_rfc
        if expected_uuid:
            expected_data["uuid"] = expected_uuid
        if expected_total:
            expected_data["monto"] = expected_total
        
        result = vision_agent.validate_cfdi(content, expected_data)
        
        return {
            "success": True,
            "filename": file.filename,
            "validation": result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error validando CFDI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-types")
async def get_document_types():
    """Lista los tipos de documento soportados y sus keywords requeridas"""
    return {
        "document_types": vision_agent.REQUIRED_KEYWORDS
    }
