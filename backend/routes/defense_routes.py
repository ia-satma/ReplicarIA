"""
Defense File Generator Routes
Endpoints para generar y descargar expedientes de defensa fiscal
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
import os

from services.defense_generator import defense_generator
from services.defense_file_service import defense_file_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/defense", tags=["defense"])


@router.get("/generate/{project_id}")
async def generate_defense_dossier(project_id: str):
    """
    Genera el expediente de defensa completo para un proyecto.
    Retorna la ruta del ZIP generado.
    """
    try:
        df = defense_file_service.get_or_create(project_id)
        if not df.project_data and not df.deliberations:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró información para el proyecto {project_id}"
            )
        
        zip_path = defense_generator.generate_dossier(project_id)
        
        if not os.path.exists(zip_path):
            raise HTTPException(
                status_code=500,
                detail="Error generando el expediente"
            )
        
        return {
            "success": True,
            "project_id": project_id,
            "zip_path": zip_path,
            "download_url": f"/api/defense/download/{project_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando expediente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{project_id}")
async def download_defense_dossier(project_id: str):
    """
    Descarga el expediente de defensa ZIP para un proyecto.
    Genera el expediente si no existe.
    """
    try:
        zip_path = f"/tmp/expedientes/EXPEDIENTE_{project_id}.zip"
        
        if not os.path.exists(zip_path):
            zip_path = defense_generator.generate_dossier(project_id)
        
        if not os.path.exists(zip_path):
            raise HTTPException(
                status_code=404,
                detail="Expediente no encontrado"
            )
        
        return FileResponse(
            path=zip_path,
            filename=f"EXPEDIENTE_{project_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando expediente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{project_id}")
async def preview_defense_dossier(project_id: str):
    """
    Vista previa del contenido del expediente sin generar el ZIP.
    """
    try:
        df = defense_file_service.get_or_create(project_id)
        
        return {
            "project_id": project_id,
            "project_data": df.project_data,
            "compliance_checklist": df.compliance_checklist,
            "compliance_score": sum(df.compliance_checklist.values()) / len(df.compliance_checklist) * 100,
            "risk_score": 100 - (sum(df.compliance_checklist.values()) / len(df.compliance_checklist) * 100),
            "deliberation_count": len(df.deliberations),
            "document_count": len(df.documents),
            "email_count": len(df.emails),
            "pcloud_document_count": len(df.pcloud_documents),
            "folders_structure": [
                "00_INDICE_MAESTRO.pdf",
                "01_SOLICITUD_COMPRA/",
                "02_APROBACIONES/",
                "03_EVIDENCIAS_EJECUCION/",
                "04_COMPROBANTES_PAGO/",
                "05_ANALISIS_RIESGO/"
            ],
            "ready_for_download": bool(df.project_data or df.deliberations)
        }
        
    except Exception as e:
        logger.error(f"Error en preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_available_dossiers():
    """
    Lista todos los expedientes de defensa disponibles.
    """
    try:
        defense_files = defense_file_service.list_all()
        
        return {
            "count": len(defense_files),
            "dossiers": [
                {
                    "project_id": df["project_id"],
                    "project_name": df.get("project_data", {}).get("name", df["project_id"]),
                    "compliance_score": df.get("compliance_score", 0),
                    "audit_ready": df.get("audit_ready", False),
                    "deliberation_count": df.get("deliberation_count", 0),
                    "download_url": f"/api/defense/download/{df['project_id']}"
                }
                for df in defense_files
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listando expedientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
