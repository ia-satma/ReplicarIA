import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

GOOGLE_API_AVAILABLE = False

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_API_AVAILABLE = True
except ImportError:
    Request = None
    Credentials = None
    build = None
    MediaIoBaseDownload = None
    logger.info("Google API not installed - Drive service will use pCloud fallback")

class DriveService:
    """Servicio para acceder a documentos de Google Drive usando OAuth"""
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/drive/v3"
        self.service: Any = None
        if GOOGLE_API_AVAILABLE:
            self.service = self._get_drive_service()
    
    def _get_drive_service(self) -> Any:
        """Obtener servicio de Drive autenticado con OAuth"""
        if not GOOGLE_API_AVAILABLE or Credentials is None or build is None:
            return None
            
        try:
            token_path = os.path.join(os.path.dirname(__file__), '..', 'token.json')
            
            if not os.path.exists(token_path):
                return None
            
            creds = Credentials.from_authorized_user_file(token_path, 
                ['https://www.googleapis.com/auth/drive.readonly'])
            
            if creds and creds.expired and creds.refresh_token and Request:
                creds.refresh(Request())
            
            service = build('drive', 'v3', credentials=creds)
            logger.info("Drive service authenticated successfully")
            return service
            
        except Exception as e:
            logger.debug(f"Drive service not available: {str(e)}")
            return None
    
    def list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """Lista todos los archivos en una carpeta de Drive"""
        if not self.service:
            return []
        
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            return files
                    
        except Exception as e:
            logger.error(f"Error listando archivos de Drive: {str(e)}")
            return []
    
    def get_file_content(self, file_id: str, mime_type: str) -> Optional[str]:
        """Obtiene el contenido de un archivo de Drive"""
        if not self.service or not GOOGLE_API_AVAILABLE or MediaIoBaseDownload is None:
            return None
            
        try:
            import io as io_module
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
            elif mime_type in ['text/plain', 'text/csv', 'application/json']:
                request = self.service.files().get_media(fileId=file_id)
            else:
                return None
            
            file_content = io_module.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error obteniendo contenido: {str(e)}")
            return None
    
    def search_files(self, query: str, folder_id: Optional[str] = None) -> List[Dict]:
        """Busca archivos en Drive"""
        if not self.service:
            return []
        
        try:
            search_query = f"fullText contains '{query}'"
            if folder_id:
                search_query = f"'{folder_id}' in parents and {search_query}"
            
            results = self.service.files().list(
                q=search_query,
                fields="files(id, name, mimeType, webViewLink)",
                pageSize=20
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Error buscando archivos: {str(e)}")
            return []

drive_service = DriveService()
