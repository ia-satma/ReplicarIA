import os
import logging
import base64
from typing import List, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

GOOGLE_API_AVAILABLE = False

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    Request = None
    Credentials = None
    build = None
    logger.info("Google API not installed - Gmail service disabled")

class GmailService:
    """Servicio para enviar y recibir correos usando Gmail API con OAuth"""
    
    def __init__(self):
        self.service: Any = None
        if GOOGLE_API_AVAILABLE:
            self.service = self._get_gmail_service()
    
    def _get_gmail_service(self) -> Any:
        """Obtener servicio de Gmail autenticado con OAuth"""
        if not GOOGLE_API_AVAILABLE or Credentials is None or build is None:
            return None
            
        try:
            token_path = os.path.join(os.path.dirname(__file__), '..', 'token.json')
            
            if not os.path.exists(token_path):
                return None
            
            creds = Credentials.from_authorized_user_file(token_path, 
                ['https://www.googleapis.com/auth/gmail.readonly',
                 'https://www.googleapis.com/auth/gmail.send'])
            
            if creds and creds.expired and creds.refresh_token and Request:
                creds.refresh(Request())
            
            service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service authenticated successfully")
            return service
            
        except Exception as e:
            logger.debug(f"Gmail service not available: {str(e)}")
            return None
    
    def send_email(self, to: str, subject: str, body: str, from_email: str = "") -> Dict:
        """Envía un correo electrónico usando Gmail API"""
        if not self.service:
            return {"success": False, "error": "Gmail service not available"}
        
        try:
            message = MIMEMultipart('alternative')
            message['To'] = to
            message['Subject'] = subject
            
            text_part = MIMEText(body, 'plain', 'utf-8')
            html_part = MIMEText(body, 'html', 'utf-8')
            message.attach(text_part)
            message.attach(html_part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent to {to}: {result.get('id')}")
            return {"success": True, "message_id": result.get('id')}
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_emails(self, max_results: int = 10, label: str = 'INBOX') -> List[Dict]:
        """Obtiene emails del usuario"""
        if not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in email_data.get('payload', {}).get('headers', [])}
                emails.append({
                    'id': msg['id'],
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': email_data.get('snippet', '')
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting emails: {str(e)}")
            return []

gmail_service = GmailService()
