from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.drive_service import DriveService
from services.gmail_service import GmailService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
drive_service = DriveService()
gmail_service = GmailService()

# Request models
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    agent_id: Optional[str] = None

class DriveSearchRequest(BaseModel):
    folder_id: str
    query: str

# ==================== DRIVE ROUTES ====================

@router.get("/drive/folder/{folder_id}/files")
async def list_drive_files(folder_id: str):
    """Lista archivos en una carpeta específica de Drive"""
    try:
        files = drive_service.list_files_in_folder(folder_id)
        return {
            "success": True,
            "folder_id": folder_id,
            "files": files,
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drive/folder/{folder_id}/summary")
async def get_folder_summary(folder_id: str):
    """Obtiene resumen de conocimiento de una carpeta de Drive"""
    try:
        summary = drive_service.get_agent_knowledge_summary(folder_id)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting folder summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drive/file/{file_id}/content")
async def get_file_content(file_id: str, mime_type: str = "text/plain"):
    """Obtiene el contenido de un archivo de Drive"""
    try:
        content = drive_service.get_file_content(file_id, mime_type)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found or cannot be read")
        
        return {
            "success": True,
            "file_id": file_id,
            "content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drive/search")
async def search_drive_files(request: DriveSearchRequest):
    """Busca archivos en una carpeta de Drive"""
    try:
        files = drive_service.search_in_folder(request.folder_id, request.query)
        return {
            "success": True,
            "query": request.query,
            "files": files,
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drive/folder/{folder_id}/knowledge")
async def get_agent_knowledge(folder_id: str, max_files: int = 10):
    """Obtiene el contenido de texto de archivos de Drive para incluir en prompts"""
    try:
        knowledge_text = drive_service.get_agent_knowledge_text(folder_id, max_files)
        return {
            "success": True,
            "folder_id": folder_id,
            "knowledge": knowledge_text
        }
    except Exception as e:
        logger.error(f"Error getting agent knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GMAIL ROUTES ====================

@router.post("/gmail/send")
async def send_email(request: EmailRequest):
    """Envía un correo electrónico usando Gmail API"""
    try:
        # Si hay agent_id, usar la configuración del agente
        if request.agent_id:
            from services.agent_service import AGENT_CONFIGURATIONS
            agent_config = AGENT_CONFIGURATIONS.get(request.agent_id)
            if agent_config:
                result = gmail_service.send_agent_email(
                    agent_config=agent_config,
                    to=request.to,
                    subject=request.subject,
                    body=request.body
                )
            else:
                result = gmail_service.send_email(
                    to=request.to,
                    subject=request.subject,
                    body=request.body
                )
        else:
            result = gmail_service.send_email(
                to=request.to,
                subject=request.subject,
                body=request.body
            )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/inbox")
async def get_inbox(max_results: int = 10, query: str = ""):
    """Obtiene correos recientes de la bandeja de entrada"""
    try:
        emails = gmail_service.get_recent_emails(max_results=max_results, query=query)
        return {
            "success": True,
            "emails": emails,
            "total": len(emails)
        }
    except Exception as e:
        logger.error(f"Error getting inbox: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/search")
async def search_emails(query: str, max_results: int = 10):
    """Busca correos que coincidan con un criterio"""
    try:
        emails = gmail_service.search_emails(query=query, max_results=max_results)
        return {
            "success": True,
            "query": query,
            "emails": emails,
            "total": len(emails)
        }
    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/profile")
async def get_gmail_profile():
    """Obtiene información del perfil de Gmail autenticado"""
    try:
        email = gmail_service.get_user_email()
        return {
            "success": True,
            "email": email,
            "authenticated": gmail_service.service is not None
        }
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
