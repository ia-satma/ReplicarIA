"""
Defense Files Routes - API para documentación de proyectos en pCloud
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from jose import jwt, exceptions as jose_exceptions

from services.pcloud_service import pcloud_service
from services.defense_file_export_service import defense_file_export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/defense-files", tags=["defense-files"])

SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado - Token requerido")
    token = credentials.credentials
    payload = verify_token(token)
    return payload


class CrearEstructuraRequest(BaseModel):
    cliente_rfc: str
    anio: int
    proyecto_id: int
    proyecto_nombre: str


class DocumentarEventoRequest(BaseModel):
    proyecto_folder_id: int
    agente: str
    tipo_evento: str
    datos: Dict[str, Any]


@router.post("/crear-estructura")
async def crear_estructura_defense_file(request: CrearEstructuraRequest):
    """Crea la estructura completa de carpetas para un proyecto de Defense File"""
    if not pcloud_service.is_available():
        return {
            "success": True,
            "simulado": True,
            "mensaje": "Modo demo - estructura simulada",
            "carpetas_creadas": 30
        }
    
    try:
        result = pcloud_service.crear_estructura_defense_file(
            cliente_rfc=request.cliente_rfc,
            anio=request.anio,
            proyecto_id=request.proyecto_id,
            proyecto_nombre=request.proyecto_nombre
        )
        return result
    except Exception as e:
        logger.error(f"Error creando estructura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documentar-evento")
async def documentar_evento_agente(request: DocumentarEventoRequest):
    """Documenta un evento de un agente en la estructura de Defense File"""
    if not pcloud_service.is_available():
        return {
            "success": True,
            "simulado": True,
            "mensaje": f"Evento {request.tipo_evento} de {request.agente} documentado (demo)"
        }
    
    try:
        result = pcloud_service.documentar_evento_agente(
            proyecto_folder_id=request.proyecto_folder_id,
            agente=request.agente,
            tipo_evento=request.tipo_evento,
            datos=request.datos
        )
        return result
    except Exception as e:
        logger.error(f"Error documentando evento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{proyecto_folder_id}")
async def obtener_timeline(proyecto_folder_id: int):
    """Genera y retorna el timeline completo de un proyecto"""
    if not pcloud_service.is_available():
        return {
            "success": True,
            "simulado": True,
            "total_eventos": 0,
            "timeline": []
        }
    
    try:
        result = pcloud_service.generar_timeline_proyecto(proyecto_folder_id)
        return result
    except Exception as e:
        logger.error(f"Error generando timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def defense_files_status():
    """Verifica el estado del sistema de Defense Files"""
    disponible = pcloud_service.is_available()
    
    if disponible:
        login_result = pcloud_service.login()
        return {
            "success": True,
            "pcloud_disponible": True,
            "pcloud_conectado": login_result.get("success", False),
            "email": login_result.get("email") if login_result.get("success") else None,
            "agentes_documentados": [
                "A1_Facturar.IA", "A2_Bibliotecar.IA", "A3_Revisar.IA",
                "A4_Trafico.IA", "A5_Disenar.IA", "A6_Onboarding", "A7_Diagnostico"
            ]
        }
    
    return {
        "success": True,
        "pcloud_disponible": False,
        "modo": "demo",
        "mensaje": "Sistema en modo demo - configure PCLOUD_USERNAME y PCLOUD_PASSWORD"
    }


@router.get("/projects/{project_id}/pdf")
async def download_defense_file_pdf(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Genera y descarga el Expediente de Defensa Fiscal en formato PDF.
    Incluye:
    - Portada con datos del proyecto
    - Resumen ejecutivo
    - Fundamentos legales
    - Análisis por agente
    - Evidencia de materialidad
    - Comprobantes fiscales
    - Cadena de integridad (hash)
    """
    empresa_id = current_user.get("empresa_id") or current_user.get("company_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="No tiene empresa asignada")
    
    try:
        pdf_buffer = await defense_file_export_service.generate_defense_file_pdf(
            project_id,
            empresa_id
        )
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"expediente_defensa_{project_id}_{timestamp}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    except Exception as e:
        logger.error(f"Error generating defense file PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")
