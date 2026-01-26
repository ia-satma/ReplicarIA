import os
import logging
from typing import Optional
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

class MultiAgentGmailService:
    """Servicio de Gmail que maneja múltiples cuentas de agentes"""
    
    def __init__(self):
        self.services = {}
        # Path relativo para tokens
        self.token_base_path = Path(__file__).parent.parent
        self._initialize_all_agents()
    
    def _initialize_all_agents(self):
        """Inicializar servicios de Gmail para todos los agentes"""
        from services.agent_service import AGENT_CONFIGURATIONS
        
        for agent_id, config in AGENT_CONFIGURATIONS.items():
            token_file = config.get('token_file')
            if token_file:
                token_path = self.token_base_path / token_file
                if token_path.exists():
                    service = self._get_gmail_service(str(token_path))
                    if service:
                        self.services[agent_id] = {
                            'gmail': service,
                            'email': config['email'],
                            'name': config['name']
                        }
                        logger.info(f"✅ Gmail service initialized for {config['name']} ({config['email']})")
    
    def _get_gmail_service(self, token_path):
        """Obtener servicio de Gmail con token específico"""
        try:
            if not os.path.exists(token_path):
                logger.error(f"Token file not found: {token_path}")
                return None
            
            creds = Credentials.from_authorized_user_file(token_path, 
                ['https://www.googleapis.com/auth/gmail.readonly',
                 'https://www.googleapis.com/auth/gmail.send'])
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('gmail', 'v1', credentials=creds)
            return service
            
        except Exception as e:
            logger.error(f"Error authenticating Gmail service for {token_path}: {str(e)}")
            return None
    
    def send_email_as_agent(
        self,
        agent_id: str,
        to: str,
        subject: str,
        body: str,
        cc: list = None,
        attachment_path: str = None
    ) -> dict:
        """Envía email desde la cuenta específica del agente con archivo adjunto"""
        
        if agent_id not in self.services:
            logger.error(f"Agent {agent_id} not initialized")
            return {"success": False, "error": "Agent service not available"}
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.application import MIMEApplication
            import base64
            
            service = self.services[agent_id]['gmail']
            from_email = self.services[agent_id]['email']
            
            message = MIMEMultipart('mixed')
            message['To'] = to
            message['Subject'] = subject
            message['From'] = from_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            # Agregar cuerpo del email
            text_part = MIMEText(body, 'plain', 'utf-8')
            message.attach(text_part)
            
            # Adjuntar archivo PDF si existe
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype='pdf')
                    attachment.add_header('Content-Disposition', 'attachment', 
                                        filename=os.path.basename(attachment_path))
                    message.attach(attachment)
                logger.info(f"📎 Adjuntando archivo: {os.path.basename(attachment_path)}")
            
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Enviar mensaje
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Email sent from {from_email} to {to}. Message ID: {sent_message['id']}")
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "from": from_email,
                "to": to,
                "cc": cc,
                "attachment": os.path.basename(attachment_path) if attachment_path else None
            }
            
        except Exception as e:
            logger.error(f"Error sending email as {agent_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_agent_email(self, agent_id: str) -> str:
        """Obtiene el email de un agente"""
        if agent_id in self.services:
            return self.services[agent_id]['email']
        return ""
