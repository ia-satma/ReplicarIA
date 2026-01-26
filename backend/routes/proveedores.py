from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import base64
import logging

from middleware.tenant_context import get_current_empresa_id, get_current_user_id, require_empresa
from services.proveedor_service import ProveedorService
from services.proveedor_ocr_service import ProveedorOCRService
from services.pcloud_service import PCloudService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/proveedores", tags=["proveedores"])

proveedor_service = ProveedorService()
ocr_service = ProveedorOCRService()
pcloud_service = PCloudService()

SERVICE_UNAVAILABLE_MSG = "El servicio de proveedores no está disponible temporalmente. Por favor intente más tarde."


def check_service_available():
    if not proveedor_service.is_available():
        raise HTTPException(
            status_code=503,
            detail=SERVICE_UNAVAILABLE_MSG
        )


class ProveedorCreate(BaseModel):
    razon_social: str
    rfc: str
    regimen_fiscal: str
    tipo_persona: str = "moral"
    tipo_proveedor: str = "OTRO"
    nombre_comercial: Optional[str] = None
    clave_regimen_fiscal: Optional[str] = None
    fecha_constitucion: Optional[str] = None
    objeto_social_relevante: Optional[str] = None
    sitio_web: Optional[str] = None
    requiere_repse: bool = False
    tiene_personal_en_sitio: bool = False
    es_servicio_regulado: bool = False
    descripcion_servicios_ofrecidos: Optional[str] = None
    domicilio_fiscal: Optional[Dict[str, Any]] = None
    contacto_principal: Optional[Dict[str, Any]] = None
    capital_social: Optional[Dict[str, Any]] = None
    redes_sociales: Optional[Dict[str, Any]] = None


class ProveedorUpdate(BaseModel):
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    tipo_persona: Optional[str] = None
    tipo_proveedor: Optional[str] = None
    estatus: Optional[str] = None
    sitio_web: Optional[str] = None
    requiere_repse: Optional[bool] = None
    tiene_personal_en_sitio: Optional[bool] = None
    es_servicio_regulado: Optional[bool] = None
    descripcion_servicios_ofrecidos: Optional[str] = None
    domicilio_fiscal: Optional[Dict[str, Any]] = None
    contacto_principal: Optional[Dict[str, Any]] = None
    capital_social: Optional[Dict[str, Any]] = None
    redes_sociales: Optional[Dict[str, Any]] = None
    documentos: Optional[Dict[str, Any]] = None


class ProveedorFiltros(BaseModel):
    estatus: Optional[str] = None
    tipo_proveedor: Optional[str] = None
    nivel_riesgo: Optional[str] = None
    busqueda: Optional[str] = None


class OCRRequest(BaseModel):
    archivo_base64: str
    media_type: str


@router.post("")
@require_empresa
async def crear_proveedor(proveedor: ProveedorCreate):
    empresa_id = get_current_empresa_id()
    usuario_id = get_current_user_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    if proveedor_service.verificar_rfc_existente(proveedor.rfc, empresa_id):
        raise HTTPException(status_code=400, detail="Ya existe un proveedor con este RFC en tu empresa")
    
    result = proveedor_service.create_proveedor(proveedor.model_dump(), empresa_id, usuario_id or "system")
    
    if result.get("service_unavailable"):
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_MSG)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error creando proveedor"))
    
    return result


@router.get("")
@require_empresa
async def listar_proveedores(
    estatus: Optional[str] = None,
    tipo_proveedor: Optional[str] = None,
    nivel_riesgo: Optional[str] = None,
    busqueda: Optional[str] = None
):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    filtros = {}
    if estatus:
        filtros["estatus"] = estatus
    if tipo_proveedor:
        filtros["tipo_proveedor"] = tipo_proveedor
    if nivel_riesgo:
        filtros["nivel_riesgo"] = nivel_riesgo
    if busqueda:
        filtros["busqueda"] = busqueda
    
    proveedores = await proveedor_service.get_proveedores_by_empresa_async(empresa_id, filtros if filtros else None)
    return {"proveedores": proveedores, "total": len(proveedores)}


@router.get("/estadisticas")
@require_empresa
async def obtener_estadisticas():
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    result = proveedor_service.get_estadisticas(empresa_id)
    
    if result.get("service_unavailable"):
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_MSG)
    
    return result


@router.get("/buscar")
@require_empresa
async def buscar_proveedores(q: str):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    if len(q) < 2:
        return {"proveedores": []}
    
    proveedores = proveedor_service.search_proveedores(empresa_id, q)
    return {"proveedores": proveedores}


@router.get("/{proveedor_id}")
@require_empresa
async def obtener_proveedor(proveedor_id: str):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    proveedor = proveedor_service.get_proveedor(proveedor_id, empresa_id)
    
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return proveedor


@router.put("/{proveedor_id}")
@require_empresa
async def actualizar_proveedor(proveedor_id: str, updates: ProveedorUpdate):
    empresa_id = get_current_empresa_id()
    usuario_id = get_current_user_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    updates_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not updates_dict:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    result = proveedor_service.update_proveedor(proveedor_id, empresa_id, updates_dict, usuario_id or "system")
    
    if result.get("service_unavailable"):
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_MSG)
    
    if not result.get("success"):
        if result.get("error") == "Proveedor no encontrado":
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        raise HTTPException(status_code=500, detail=result.get("error", "Error actualizando proveedor"))
    
    return result


@router.delete("/{proveedor_id}")
@require_empresa
async def eliminar_proveedor(proveedor_id: str):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    result = proveedor_service.delete_proveedor(proveedor_id, empresa_id)
    
    if result.get("service_unavailable"):
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_MSG)
    
    if not result.get("success"):
        if result.get("error") == "Proveedor no encontrado":
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        raise HTTPException(status_code=500, detail=result.get("error", "Error eliminando proveedor"))
    
    return result


@router.post("/{proveedor_id}/recalcular-riesgo")
@require_empresa
async def recalcular_riesgo(proveedor_id: str):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    result = proveedor_service.recalcular_riesgo(proveedor_id, empresa_id)
    
    if result.get("service_unavailable"):
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_MSG)
    
    if not result.get("success"):
        if result.get("error") == "Proveedor no encontrado":
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        raise HTTPException(status_code=500, detail=result.get("error", "Error recalculando riesgo"))
    
    return result


@router.post("/ocr/constancia-fiscal")
@require_empresa
async def ocr_constancia_fiscal(request: OCRRequest):
    try:
        result = await ocr_service.extraer_constancia_fiscal(request.archivo_base64, request.media_type)
        
        if not result.get("exito"):
            error_msg = result.get("error", "Error procesando documento")
            if "no disponible" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde."
                )
            raise HTTPException(status_code=500, detail=error_msg)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en OCR constancia fiscal: {str(e)}")
        raise HTTPException(status_code=503, detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde.")


@router.post("/ocr/acta-constitutiva")
@require_empresa
async def ocr_acta_constitutiva(request: OCRRequest):
    try:
        result = await ocr_service.extraer_acta_constitutiva(request.archivo_base64, request.media_type)
        
        if not result.get("exito"):
            error_msg = result.get("error", "Error procesando documento")
            if "no disponible" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde."
                )
            raise HTTPException(status_code=500, detail=error_msg)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en OCR acta constitutiva: {str(e)}")
        raise HTTPException(status_code=503, detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde.")


@router.post("/ocr/opinion-cumplimiento")
@require_empresa
async def ocr_opinion_cumplimiento(request: OCRRequest):
    try:
        result = await ocr_service.extraer_opinion_cumplimiento(request.archivo_base64, request.media_type)
        
        if not result.get("exito"):
            error_msg = result.get("error", "Error procesando documento")
            if "no disponible" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde."
                )
            raise HTTPException(status_code=500, detail=error_msg)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en OCR opinion cumplimiento: {str(e)}")
        raise HTTPException(status_code=503, detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde.")


@router.post("/ocr/repse")
@require_empresa
async def ocr_repse(request: OCRRequest):
    try:
        result = await ocr_service.extraer_repse(request.archivo_base64, request.media_type)
        
        if not result.get("exito"):
            error_msg = result.get("error", "Error procesando documento")
            if "no disponible" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde."
                )
            raise HTTPException(status_code=500, detail=error_msg)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en OCR REPSE: {str(e)}")
        raise HTTPException(status_code=503, detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde.")


@router.post("/ocr/clasificar")
@require_empresa
async def ocr_clasificar_documento(request: OCRRequest):
    try:
        result = await ocr_service.clasificar_documento(request.archivo_base64, request.media_type)
        
        if not result.get("exito"):
            error_msg = result.get("error", "Error clasificando documento")
            if "no disponible" in error_msg.lower():
                raise HTTPException(
                    status_code=503, 
                    detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde."
                )
            raise HTTPException(status_code=500, detail=error_msg)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en OCR clasificar: {str(e)}")
        raise HTTPException(status_code=503, detail="El servicio de OCR no está disponible temporalmente. Por favor intente más tarde.")


@router.post("/{proveedor_id}/pcloud/crear-carpeta")
@require_empresa
async def crear_carpeta_proveedor_pcloud(proveedor_id: str):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    proveedor = proveedor_service.get_proveedor(proveedor_id, empresa_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    login_result = pcloud_service.login()
    if not login_result.get("success"):
        raise HTTPException(status_code=500, detail="Error conectando a pCloud")
    
    revisar_result = pcloud_service.find_revisar_ia_folder()
    if not revisar_result.get("success"):
        raise HTTPException(status_code=500, detail="No se encontró carpeta REVISAR.ia en pCloud")
    
    empresas_folder = None
    revisar_contents = pcloud_service.list_folder(folder_id=pcloud_service.revisar_ia_folder_id)
    if revisar_contents.get("success"):
        for item in revisar_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "").upper() == "EMPRESAS":
                empresas_folder = item.get("id")
                break
    
    if not empresas_folder:
        create_result = pcloud_service.create_folder(pcloud_service.revisar_ia_folder_id, "EMPRESAS")
        if create_result.get("success") and create_result.get("folder_id"):
            empresas_folder = create_result.get("folder_id")
        else:
            raise HTTPException(status_code=500, detail="Error creando carpeta EMPRESAS")
    
    empresa_folder = None
    empresas_contents = pcloud_service.list_folder(folder_id=empresas_folder)
    if empresas_contents.get("success"):
        for item in empresas_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "") == empresa_id:
                empresa_folder = item.get("id")
                break
    
    if not empresa_folder:
        create_result = pcloud_service.create_folder(empresas_folder, empresa_id)
        if create_result.get("success") and create_result.get("folder_id"):
            empresa_folder = create_result.get("folder_id")
        elif create_result.get("already_exists"):
            empresas_contents = pcloud_service.list_folder(folder_id=empresas_folder)
            for item in empresas_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "") == empresa_id:
                    empresa_folder = item.get("id")
                    break
        else:
            raise HTTPException(status_code=500, detail="Error creando carpeta de empresa")
    
    proveedores_folder = None
    empresa_contents = pcloud_service.list_folder(folder_id=empresa_folder)
    if empresa_contents.get("success"):
        for item in empresa_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "").upper() == "PROVEEDORES":
                proveedores_folder = item.get("id")
                break
    
    if not proveedores_folder:
        create_result = pcloud_service.create_folder(empresa_folder, "PROVEEDORES")
        if create_result.get("success") and create_result.get("folder_id"):
            proveedores_folder = create_result.get("folder_id")
        elif create_result.get("already_exists"):
            empresa_contents = pcloud_service.list_folder(folder_id=empresa_folder)
            for item in empresa_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").upper() == "PROVEEDORES":
                    proveedores_folder = item.get("id")
                    break
    
    proveedor_folder_name = f"{proveedor.get('rfc', proveedor_id)}_{proveedor.get('razon_social', 'PROVEEDOR')[:30]}"
    proveedor_folder_name = "".join(c for c in proveedor_folder_name if c.isalnum() or c in " _-").strip()
    
    proveedor_folder = None
    proveedores_contents = pcloud_service.list_folder(folder_id=proveedores_folder)
    if proveedores_contents.get("success"):
        for item in proveedores_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "").startswith(proveedor.get('rfc', '')):
                proveedor_folder = item.get("id")
                break
    
    if not proveedor_folder:
        create_result = pcloud_service.create_folder(proveedores_folder, proveedor_folder_name)
        if create_result.get("success") and create_result.get("folder_id"):
            proveedor_folder = create_result.get("folder_id")
    
    if proveedor_folder:
        for subfolder in ["CONSTANCIA_FISCAL", "ACTA_CONSTITUTIVA", "OPINION_32D", "REPSE", "CONTRATOS", "OTROS"]:
            pcloud_service.create_folder(proveedor_folder, subfolder)
        
        proveedor_service.update_proveedor(
            proveedor_id, 
            empresa_id, 
            {
                "pcloud_folder_id": proveedor_folder,
                "pcloud_folder_path": f"/REVISAR.ia/EMPRESAS/{empresa_id}/PROVEEDORES/{proveedor_folder_name}"
            },
            "system"
        )
        
        return {
            "success": True,
            "folder_id": proveedor_folder,
            "folder_path": f"/REVISAR.ia/EMPRESAS/{empresa_id}/PROVEEDORES/{proveedor_folder_name}"
        }
    
    raise HTTPException(status_code=500, detail="Error creando estructura de carpetas")


@router.post("/{proveedor_id}/documentos/upload")
@require_empresa
async def upload_documento_proveedor(
    proveedor_id: str,
    tipo_documento: str,
    file: UploadFile = File(...)
):
    empresa_id = get_current_empresa_id()
    
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Empresa no especificada")
    
    check_service_available()
    
    proveedor = proveedor_service.get_proveedor(proveedor_id, empresa_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    if not proveedor.get("pcloud_folder_id"):
        raise HTTPException(status_code=400, detail="Primero debes crear la carpeta del proveedor en pCloud")
    
    tipo_to_subfolder = {
        "constancia_situacion_fiscal": "CONSTANCIA_FISCAL",
        "acta_constitutiva": "ACTA_CONSTITUTIVA",
        "opinion_cumplimiento": "OPINION_32D",
        "repse": "REPSE",
        "contrato": "CONTRATOS",
        "otro": "OTROS"
    }
    
    subfolder_name = tipo_to_subfolder.get(tipo_documento, "OTROS")
    
    login_result = pcloud_service.login()
    if not login_result.get("success"):
        raise HTTPException(status_code=500, detail="Error conectando a pCloud")
    
    proveedor_contents = pcloud_service.list_folder(folder_id=proveedor.get("pcloud_folder_id"))
    target_folder = None
    
    if proveedor_contents.get("success"):
        for item in proveedor_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "") == subfolder_name:
                target_folder = item.get("id")
                break
    
    if not target_folder:
        create_result = pcloud_service.create_folder(proveedor.get("pcloud_folder_id"), subfolder_name)
        if create_result.get("success") and create_result.get("folder_id"):
            target_folder = create_result.get("folder_id")
        else:
            target_folder = proveedor.get("pcloud_folder_id")
    
    content = await file.read()
    upload_result = pcloud_service.upload_file(target_folder, file.filename, content)
    
    if not upload_result.get("success"):
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {upload_result.get('error')}")
    
    file_id = upload_result.get("file_id")
    public_link_result = pcloud_service.get_or_create_public_link(file_id)
    
    return {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "public_link": public_link_result.get("public_link") if public_link_result.get("success") else None,
        "tipo_documento": tipo_documento
    }
