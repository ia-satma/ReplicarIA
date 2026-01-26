import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class AgentDocumentService:
    """Servicio para que cada agente cree documentos en su carpeta de Drive"""
    
    def __init__(self):
        # Usar path relativo
        ROOT_DIR = Path(__file__).parent.parent
        self.temp_dir = ROOT_DIR / "temp_docs"
        self.temp_dir.mkdir(exist_ok=True)
        self.token_base_path = ROOT_DIR
    
    def _get_drive_service_for_agent(self, agent_id: str):
        """Obtener servicio de Drive específico para un agente"""
        from services.agent_service import AGENT_CONFIGURATIONS
        
        agent_config = AGENT_CONFIGURATIONS.get(agent_id)
        if not agent_config:
            logger.error(f"Agent {agent_id} not found")
            return None
        
        token_file = agent_config.get('token_file')
        if not token_file:
            logger.error(f"No token file for agent {agent_id}")
            return None
        
        token_path = self.token_base_path / token_file
        
        try:
            if not token_path.exists():
                logger.error(f"Token file not found: {token_path}")
                return None
            
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                ['https://www.googleapis.com/auth/drive.file']
            )
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('drive', 'v3', credentials=creds)
            logger.info(f"✅ Drive service for {agent_id} initialized")
            return service
            
        except Exception as e:
            logger.error(f"Error initializing Drive for {agent_id}: {str(e)}")
            return None
    
    def create_agent_analysis_document(
        self,
        agent_id: str,
        agent_name: str,
        project_id: str,
        project_name: str,
        analysis: str,
        decision: str,
        folder_id: str
    ) -> Optional[Dict]:
        """
        Crea un documento de Google Docs en la carpeta del agente con su análisis.
        
        Returns:
            Dict con file_id, webViewLink, exportLink
        """
        
        # Obtener servicio de Drive específico del agente
        drive_service = self._get_drive_service_for_agent(agent_id)
        
        if not drive_service:
            logger.error(f"Drive service not available for {agent_id}")
            return None
        
        try:
            # Crear contenido del documento
            doc_content = f"""ANÁLISIS Y DICTAMEN
Agente: {agent_name}
ID Agente: {agent_id}
Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROYECTO: {project_name}
ID: {project_id}

DECISIÓN: {decision}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANÁLISIS DETALLADO:

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este documento fue generado automáticamente por {agent_name}.
Agent Network System - Revisar.ia
"""
            
            # Crear archivo temporal
            temp_file = self.temp_dir / f"{agent_id}_{project_id[:8]}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            # Nombre del documento en Drive
            doc_name = f"[{agent_id}] Análisis - {project_name[:40]} - {datetime.now(timezone.utc).strftime('%Y%m%d')}"
            
            # Metadata del archivo
            file_metadata = {
                'name': doc_name,
                'parents': [folder_id],
                'mimeType': 'application/vnd.google-apps.document'  # Google Doc
            }
            
            # Subir a Drive
            media = MediaFileUpload(
                str(temp_file),
                mimetype='text/plain',
                resumable=True
            )
            
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,mimeType'
            ).execute()
            
            # Limpiar archivo temporal
            temp_file.unlink()
            
            logger.info(f"✅ Documento creado en Drive para {agent_id}: {file['name']}")
            
            # Exportar documento como PDF para adjuntar a email
            pdf_path = self._export_doc_as_pdf(drive_service, file['id'], agent_id, project_id)
            
            return {
                "file_id": file['id'],
                "file_name": file['name'],
                "web_view_link": file['webViewLink'],
                "mime_type": file['mimeType'],
                "folder_id": folder_id,
                "pdf_path": pdf_path  # Path local del PDF para adjuntar
            }
            
        except Exception as e:
            logger.error(f"Error creando documento en Drive para {agent_id}: {str(e)}")
            return None
    
    def _export_doc_as_pdf(self, drive_service, file_id: str, agent_id: str, project_id: str) -> str:
        """Exporta Google Doc como PDF para adjuntar a email"""
        try:
            # Exportar como PDF
            request = drive_service.files().export_media(
                fileId=file_id,
                mimeType='application/pdf'
            )
            
            # Guardar temporalmente
            pdf_filename = f"{agent_id}_Analisis_{project_id[:8]}.pdf"
            pdf_path = self.temp_dir / pdf_filename
            
            import io
            from googleapiclient.http import MediaIoBaseDownload
            
            fh = io.FileIO(str(pdf_path), 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.close()
            
            logger.info(f"📄 PDF exportado: {pdf_filename}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Error exportando PDF: {str(e)}")
            return None
    
    def get_document_export_link(self, file_id: str, export_format: str = "pdf") -> str:
        """
        Obtiene el link de exportación de un Google Doc.
        
        Args:
            file_id: ID del archivo en Drive
            export_format: pdf, docx, txt
        """
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain"
        }
        
        export_mime = mime_types.get(export_format, "application/pdf")
        return f"https://docs.google.com/document/d/{file_id}/export?format={export_format}"