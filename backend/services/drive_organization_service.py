import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import calendar

logger = logging.getLogger(__name__)

class DriveOrganizationService:
    """Servicio para organizar documentos en Drive por mes/año para bitácora"""
    
    def __init__(self):
        ROOT_DIR = Path(__file__).parent.parent
        self.token_base_path = ROOT_DIR
        self.temp_dir = ROOT_DIR / "temp_docs"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _get_drive_service_for_agent(self, token_file: str):
        """Obtener servicio de Drive específico del agente"""
        try:
            token_path = self.token_base_path / token_file
            
            if not token_path.exists():
                logger.error(f"Token not found: {token_path}")
                return None
            
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                ['https://www.googleapis.com/auth/drive.file',
                 'https://www.googleapis.com/auth/drive']
            )
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('drive', 'v3', credentials=creds)
            return service
            
        except Exception as e:
            logger.error(f"Error getting Drive service: {str(e)}")
            return None
    
    def get_or_create_month_folder(self, drive_service, parent_folder_id: str) -> Optional[str]:
        """
        Obtiene o crea carpeta del mes actual (ej: "2025-10 Octubre")
        dentro de la carpeta principal del agente.
        """
        try:
            now = datetime.now(timezone.utc)
            month_name = calendar.month_name[now.month]
            folder_name = f"{now.year}-{now.month:02d} {month_name}"
            
            # Buscar si ya existe
            query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = drive_service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                logger.info(f"✅ Carpeta del mes ya existe: {folder_name}")
                return files[0]['id']
            
            # Crear carpeta nueva
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            
            folder = drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            logger.info(f"✅ Carpeta del mes creada: {folder_name} (ID: {folder['id']})")
            return folder['id']
            
        except Exception as e:
            logger.error(f"Error creating month folder: {str(e)}")
            return parent_folder_id  # Fallback a carpeta principal
    
    def save_document_to_drive(
        self,
        agent_id: str,
        token_file: str,
        parent_folder_id: str,
        project_id: str,
        project_name: str,
        document_content: str,
        document_type: str = "Análisis"
    ) -> Optional[Dict]:
        """
        Guarda documento en Drive del agente, organizando por mes.
        
        Args:
            agent_id: ID del agente
            token_file: Archivo de token del agente
            parent_folder_id: Carpeta raíz del agente
            project_id: ID del proyecto
            project_name: Nombre del proyecto
            document_content: Contenido del documento
            document_type: Tipo (Análisis, PO, Contrato, etc.)
        
        Returns:
            Dict con file_id, webViewLink, pdf_path
        """
        
        drive_service = self._get_drive_service_for_agent(token_file)
        
        if not drive_service:
            logger.error(f"No se pudo obtener Drive service para {agent_id}")
            return None
        
        try:
            # Obtener o crear carpeta del mes
            month_folder_id = self.get_or_create_month_folder(drive_service, parent_folder_id)
            
            # Crear archivo temporal
            temp_file = self.temp_dir / f"{agent_id}_{project_id[:8]}_{document_type}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(document_content)
            
            # Nombre del documento
            now = datetime.now(timezone.utc)
            doc_name = f"[{agent_id}] {document_type} - {project_name[:40]} - {now.strftime('%Y%m%d_%H%M')}"
            
            # Subir a Drive en carpeta del mes
            file_metadata = {
                'name': doc_name,
                'parents': [month_folder_id],
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            media = MediaFileUpload(
                str(temp_file),
                mimetype='text/plain',
                resumable=True
            )
            
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            # Limpiar temporal
            temp_file.unlink()
            
            logger.info(f"✅ {agent_id} guardó '{document_type}' en Drive (carpeta del mes)")
            logger.info(f"   Archivo: {file['name']}")
            logger.info(f"   Link: {file['webViewLink']}")
            
            # Exportar como PDF
            pdf_path = self._export_as_pdf(drive_service, file['id'], agent_id, project_id, document_type)
            
            return {
                "file_id": file['id'],
                "file_name": file['name'],
                "web_view_link": file['webViewLink'],
                "month_folder_id": month_folder_id,
                "pdf_path": pdf_path
            }
            
        except Exception as e:
            logger.error(f"Error guardando documento en Drive para {agent_id}: {str(e)}")
            logger.error(f"   Detalles: {type(e).__name__}")
            return None
    
    def _export_as_pdf(self, drive_service, file_id: str, agent_id: str, project_id: str, doc_type: str) -> Optional[str]:
        """Exporta Google Doc como PDF"""
        try:
            request = drive_service.files().export_media(
                fileId=file_id,
                mimeType='application/pdf'
            )
            
            pdf_filename = f"{agent_id}_{doc_type}_{project_id[:8]}.pdf"
            pdf_path = self.temp_dir / pdf_filename
            
            import io
            from googleapiclient.http import MediaIoBaseDownload
            
            fh = io.FileIO(str(pdf_path), 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.close()
            
            logger.info(f"📄 PDF exportado para {agent_id}: {pdf_filename}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Error exportando PDF: {str(e)}")
            return None
