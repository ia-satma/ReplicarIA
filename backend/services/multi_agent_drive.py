import os
import logging
from typing import Dict, Optional
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class MultiAgentDriveService:
    """Servicio de Drive que maneja múltiples cuentas de agentes"""
    
    def __init__(self):
        self.services = {}
        self.token_base_path = Path(__file__).parent.parent
        self._initialize_all_agents()
    
    def _initialize_all_agents(self):
        """Inicializar servicios de Drive para todos los agentes"""
        from services.agent_service import AGENT_CONFIGURATIONS
        
        for agent_id, config in AGENT_CONFIGURATIONS.items():
            if agent_id == "PROVEEDOR_IA":
                continue
            
            token_file = config.get('token_file')
            if token_file:
                token_path = self.token_base_path / token_file
                if token_path.exists():
                    service = self._get_drive_service(str(token_path))
                    if service:
                        self.services[agent_id] = {
                            'drive': service,
                            'email': config['email'],
                            'folder_id': config['drive_folder_id']
                        }
                        logger.info(f"✅ Drive service initialized for {config['name']} ({config['email']})")
    
    def _get_drive_service(self, token_path: str):
        """Obtener servicio de Drive con token específico"""
        try:
            if not os.path.exists(token_path):
                logger.error(f"Token not found: {token_path}")
                return None
            
            creds = Credentials.from_authorized_user_file(
                token_path,
                ['https://www.googleapis.com/auth/drive.file',
                 'https://www.googleapis.com/auth/drive.readonly',
                 'https://www.googleapis.com/auth/drive.metadata.readonly']
            )
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('drive', 'v3', credentials=creds)
            return service
            
        except Exception as e:
            logger.error(f"Error authenticating Drive: {str(e)}")
            return None
    
    def list_files_in_folder(self, agent_id: str, folder_id: str = None, recursive: bool = True, max_depth: int = 5) -> list:
        """Lista archivos en carpeta del agente usando SU token, con opción recursiva"""
        
        if agent_id not in self.services:
            logger.error(f"Agent {agent_id} not initialized")
            return []
        
        service = self.services[agent_id]['drive']
        if not folder_id:
            folder_id = self.services[agent_id]['folder_id']
        
        all_files = []
        
        if recursive:
            all_files = self._list_files_recursive(service, folder_id, max_depth=max_depth)
        else:
            all_files = self._list_files_single(service, folder_id)
        
        logger.info(f"✅ {agent_id}: {len(all_files)} archivos encontrados (recursive={recursive})")
        return all_files
    
    def _list_files_single(self, service, folder_id: str) -> list:
        """Lista archivos solo en nivel actual (no recursivo)"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                pageSize=100
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def _list_files_recursive(self, service, folder_id: str, current_depth: int = 0, max_depth: int = 5) -> list:
        """Lista archivos recursivamente excluyendo carpetas no deseadas"""
        
        if current_depth >= max_depth:
            return []
        
        exclude_folders = ["Plantillas", "Borradores", "Temporal", ".trash", ".Trash"]
        all_files = []
        
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                pageSize=100
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                item_name = item.get('name', '')
                mime_type = item.get('mimeType', '')
                
                # Excluir carpetas no deseadas
                if any(excluded in item_name for excluded in exclude_folders):
                    continue
                
                # Excluir archivos temporales
                if item_name.startswith('~$'):
                    continue
                
                # Si es carpeta, buscar recursivamente
                if mime_type == 'application/vnd.google-apps.folder':
                    subfolder_files = self._list_files_recursive(
                        service,
                        item['id'],
                        current_depth + 1,
                        max_depth
                    )
                    all_files.extend(subfolder_files)
                else:
                    # Es un archivo real, agregarlo
                    all_files.append(item)
            
            return all_files
            
        except Exception as e:
            logger.error(f"Error in recursive listing: {str(e)}")
            return []
    
    def get_file_content(self, agent_id: str, file_id: str, mime_type: str) -> Optional[str]:
        """Obtiene contenido de archivo usando token del agente"""
        
        if agent_id not in self.services:
            return None
        
        service = self.services[agent_id]['drive']
        
        try:
            import io
            from googleapiclient.http import MediaIoBaseDownload
            import PyPDF2
            from docx import Document as DocxDocument
            
            # Descargar archivo
            request = service.files().get_media(fileId=file_id)
            
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_buffer.seek(0)
            
            # Extraer texto según tipo
            if 'google-apps.document' in mime_type:
                # Google Doc nativo - exportar como texto
                request = service.files().export_media(fileId=file_id, mimeType='text/plain')
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                return fh.getvalue().decode('utf-8')
            
            elif 'pdf' in mime_type or mime_type.endswith('.pdf'):
                # PDF
                try:
                    pdf_reader = PyPDF2.PdfReader(file_buffer)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
                except Exception as e:
                    logger.error(f"Error extrayendo PDF: {e}")
                    return None
            
            elif 'wordprocessingml' in mime_type or mime_type.endswith(('.docx', '.doc')):
                # Word/DOCX
                try:
                    doc = DocxDocument(file_buffer)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    return text.strip()
                except Exception as e:
                    logger.error(f"Error extrayendo DOCX: {str(e)}")
                    return None
            
            else:
                # Intentar como texto plano
                try:
                    return file_buffer.getvalue().decode('utf-8')
                except Exception as e:
                    logger.warning(f"Archivo binario no soportado: {mime_type} - {e}")
                    return None
                
        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            return None
