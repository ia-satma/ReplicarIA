"""
DreamHost Email Service for Revisar.ia Multi-Agent System
Provides SMTP and IMAP functionality for agent email communication
"""
import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

IMAP_HOST = os.environ.get('IMAP_HOST', 'imap.dreamhost.com')
SMTP_HOST = 'smtp.dreamhost.com'
SMTP_PORT = 587

SHARED_PASSWORD = os.environ.get('DREAMHOST_EMAIL_PASSWORD', '')

AGENT_PASSWORDS = {
    "A1_SPONSOR": SHARED_PASSWORD,
    "A2_PMO": SHARED_PASSWORD,
    "A3_FISCAL": SHARED_PASSWORD,
    "A5_FINANZAS": SHARED_PASSWORD,
    "LEGAL": SHARED_PASSWORD,
    "A8_AUDITOR": SHARED_PASSWORD,
    "PROVEEDOR": SHARED_PASSWORD,
    "SUB_TIPIFICACION": SHARED_PASSWORD,
    "SUB_MATERIALIDAD": SHARED_PASSWORD,
    "SUB_RIESGOS": SHARED_PASSWORD,
    "A7_DEFENSA": SHARED_PASSWORD,
    # Agentes de sistema
    "BIBLIOTECARIA": SHARED_PASSWORD,
    "TRAFICO": SHARED_PASSWORD,
    "SOPORTE": SHARED_PASSWORD,
    "SYSTEM": SHARED_PASSWORD,
}

AGENT_EMAILS = {
    "A1_SPONSOR": "estrategia@revisar-ia.com",
    "A2_PMO": "pmo@revisar-ia.com",
    "A3_FISCAL": "fiscal@revisar-ia.com",
    "A5_FINANZAS": "finanzas@revisar-ia.com",
    "LEGAL": "legal@revisar-ia.com",
    "A8_AUDITOR": "auditoria@revisar-ia.com",
    "PROVEEDOR": "proveedor@revisar-ia.com",
    "SUB_TIPIFICACION": "tipificacion@revisar-ia.com",
    "SUB_MATERIALIDAD": "materialidad@revisar-ia.com",
    "SUB_RIESGOS": "riesgos@revisar-ia.com",
    "A7_DEFENSA": "defensa@revisar-ia.com",
    # Agentes de sistema
    "BIBLIOTECARIA": "kb@revisar-ia.com",
    "TRAFICO": "trafico@revisar-ia.com",
    "SOPORTE": "soporte@revisar-ia.com",
    "SYSTEM": "noreply@revisar-ia.com",
}

AGENT_NAMES = {
    "A1_SPONSOR": "María Rodríguez",
    "A2_PMO": "Carlos Mendoza",
    "A3_FISCAL": "Laura Sánchez",
    "A5_FINANZAS": "Roberto Torres",
    "LEGAL": "Ana Martínez",
    "A8_AUDITOR": "Diego Ramírez",
    "PROVEEDOR": "Comunicaciones Proveedor",
    "SUB_TIPIFICACION": "Patricia López",
    "SUB_MATERIALIDAD": "Fernando Ruiz",
    "SUB_RIESGOS": "Gabriela Vega",
    "A7_DEFENSA": "Héctor Mora",
    # Agentes de sistema
    "BIBLIOTECARIA": "Dra. Elena Vázquez",
    "TRAFICO": "Tráfico.IA",
    "SOPORTE": "Soporte Técnico",
    "SYSTEM": "Revisar.IA Sistema",
}

BCC_MASTER = "proveedor@revisar-ia.com"


def _is_valid_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(pattern, email))


def _build_bcc_list(provider_email: Optional[str] = None, additional_bcc: Optional[List[str]] = None) -> List[str]:
    """
    Build BCC list with master email and provider email.
    
    Args:
        provider_email: Email from project provider (optional)
        additional_bcc: Additional BCC emails (optional)
    
    Returns:
        List of unique valid BCC emails
    """
    bcc_list = []
    
    if _is_valid_email(BCC_MASTER):
        bcc_list.append(BCC_MASTER)
    
    if provider_email and _is_valid_email(provider_email):
        if provider_email not in bcc_list:
            bcc_list.append(provider_email)
    
    if additional_bcc:
        for email in additional_bcc:
            if _is_valid_email(email) and email not in bcc_list:
                bcc_list.append(email)
    
    return bcc_list


def _generar_extracto_normativo(tipologia: str = "") -> str:
    """Genera extracto normativo relevante para incluir en emails"""
    extracto = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARCO NORMATIVO APLICABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Art. 5-A CFF (Razón de Negocios)
   Los actos jurídicos deben tener razón de negocios cuando el 
   beneficio económico sea mayor al beneficio fiscal.

📋 Art. 69-B CFF (Operaciones Inexistentes)
   Se presume inexistencia si el emisor carece de activos, personal
   o infraestructura para prestar los servicios.

📋 Art. 27 LISR (Deducibilidad)
   Las deducciones deben ser estrictamente indispensables y estar
   amparadas con CFDI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if tipologia:
        try:
            from config.reglas_tipologia import get_reglas_tipologia
            reglas = get_reglas_tipologia(tipologia)
            if reglas:
                alertas = reglas.get("contexto_inyeccion_agentes", {}).get("A3_FISCAL", {}).get("alertas_tipologia", [])
                if alertas:
                    extracto += "\n⚠️ ALERTAS PARA ESTA TIPOLOGÍA:\n"
                    for alerta in alertas:
                        extracto += f"   • {alerta}\n"
        except Exception:
            pass
    
    return extracto


class DreamHostEmailService:
    """Email service using DreamHost SMTP/IMAP for agent communication"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.imap_host = IMAP_HOST
        self.agent_passwords = AGENT_PASSWORDS
        self.initialized = any(AGENT_PASSWORDS.values())
        
        if not self.initialized:
            logger.warning("DreamHost email service not configured - no agent passwords set")
        else:
            logger.info(f"DreamHost email service initialized: SMTP={self.smtp_host}:{self.smtp_port}, IMAP={self.imap_host}")
    
    def _get_agent_password(self, agent_id: str) -> str:
        """Get password for a specific agent"""
        return self.agent_passwords.get(agent_id, '')
    
    def _get_smtp_connection(self, agent_id: str, agent_email: str) -> Optional[smtplib.SMTP]:
        """Create SMTP connection for an agent"""
        password = self._get_agent_password(agent_id)
        if not password:
            logger.error(f"[SMTP] No password configured for agent {agent_id}")
            return None
        try:
            logger.info(f"[SMTP] Connecting to {self.smtp_host}:{self.smtp_port} for agent {agent_id} ({agent_email})")
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
            smtp.set_debuglevel(0)
            logger.info(f"[SMTP] Starting TLS...")
            smtp.starttls()
            logger.info(f"[SMTP] Authenticating with email: {agent_email}")
            smtp.login(agent_email, password)
            logger.info(f"[SMTP] ✅ Successfully connected and authenticated for {agent_id}")
            return smtp
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[SMTP] ❌ Authentication failed for {agent_email}: {e}")
            return None
        except smtplib.SMTPConnectError as e:
            logger.error(f"[SMTP] ❌ Connection error for {agent_email}: {e}")
            return None
        except smtplib.SMTPException as e:
            logger.error(f"[SMTP] ❌ SMTP error for {agent_email}: {e}")
            return None
        except Exception as e:
            logger.error(f"[SMTP] ❌ Connection failed for {agent_email}: {type(e).__name__} - {e}")
            return None
    
    def _get_imap_connection(self, agent_id: str, agent_email: str) -> Optional[imaplib.IMAP4_SSL]:
        """Create IMAP connection for an agent"""
        password = self._get_agent_password(agent_id)
        if not password:
            logger.error(f"No password configured for agent {agent_id}")
            return None
        try:
            imap = imaplib.IMAP4_SSL(self.imap_host)
            imap.login(agent_email, password)
            return imap
        except Exception as e:
            logger.error(f"IMAP connection failed for {agent_email}: {e}")
            return None
    
    def send_email(
        self,
        from_agent_id: str,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        html_body: Optional[str] = None,
        attachment_path: Optional[str] = None,
        provider_email: Optional[str] = None
    ) -> Dict:
        """
        Send email from an agent using SendGrid API (bypasses SMTP blocks on Railway)
        
        Args:
            from_agent_id: Agent ID (A1_SPONSOR, A2_PMO, etc.)
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            cc_emails: List of CC recipients
            bcc_emails: List of BCC recipients (additional to auto-BCC)
            html_body: Optional HTML body
            attachment_path: Optional file attachment path
            provider_email: Provider email to auto-BCC (from project)
        
        Returns:
            Dict with success status and message_id
        """
        # Check for SendGrid API key first (preferred for Railway)
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
        
        if not sendgrid_api_key and not self.initialized:
            logger.warning("Email service not initialized - logging email only")
            return self._log_email(from_agent_id, to_email, subject, body)
        
        from_email = AGENT_EMAILS.get(from_agent_id)
        from_name = AGENT_NAMES.get(from_agent_id, "Sistema")
        
        if not from_email:
            return {"success": False, "error": f"Unknown agent: {from_agent_id}"}
        
        # Use SendGrid API if available (bypasses Railway SMTP port blocks)
        if sendgrid_api_key:
            return self._send_via_sendgrid(
                from_agent_id=from_agent_id,
                from_email=from_email,
                from_name=from_name,
                to_email=to_email,
                subject=subject,
                body=body,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                html_body=html_body,
                attachment_path=attachment_path,
                provider_email=provider_email,
                api_key=sendgrid_api_key
            )
        
        # Fallback to SMTP if SendGrid not available
        return self._send_via_smtp(
            from_agent_id=from_agent_id,
            from_email=from_email,
            from_name=from_name,
            to_email=to_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            html_body=html_body,
            attachment_path=attachment_path,
            provider_email=provider_email
        )
    
    def _send_via_sendgrid(
        self,
        from_agent_id: str,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]],
        bcc_emails: Optional[List[str]],
        html_body: Optional[str],
        attachment_path: Optional[str],
        provider_email: Optional[str],
        api_key: str
    ) -> Dict:
        """Send email via SendGrid API"""
        import httpx
        import base64
        
        try:
            # Use SendGrid from_email (verified sender) with agent name for display
            sendgrid_from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'pmo@revisar-ia.com')
            
            # Build personalizations
            personalizations = [{
                "to": [{"email": to_email}]
            }]
            
            if cc_emails:
                personalizations[0]["cc"] = [{"email": email} for email in cc_emails]
            
            final_bcc = _build_bcc_list(provider_email, bcc_emails)
            if final_bcc:
                personalizations[0]["bcc"] = [{"email": email} for email in final_bcc]
            
            # Build content
            content = [{"type": "text/plain", "value": body}]
            if html_body:
                content.append({"type": "text/html", "value": html_body})
            
            # Build payload
            payload = {
                "personalizations": personalizations,
                "from": {
                    "email": sendgrid_from_email,
                    "name": f"{from_name} (via Revisar.IA)"
                },
                "reply_to": {"email": from_email, "name": from_name},
                "subject": subject,
                "content": content,
                "headers": {
                    "X-Agent-ID": from_agent_id,
                    "X-System": "Revisar.IA",
                    "X-Original-From": from_email
                }
            }
            
            # Add attachment if present
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    file_content = f.read()
                    payload["attachments"] = [{
                        "content": base64.b64encode(file_content).decode('utf-8'),
                        "filename": os.path.basename(attachment_path),
                        "type": "application/pdf",
                        "disposition": "attachment"
                    }]
            
            # Send via SendGrid API
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
            
            if response.status_code in (200, 201, 202):
                message_id = response.headers.get('X-Message-Id', f"sg_{from_agent_id}_{datetime.now().timestamp()}")
                logger.info(f"✅ SendGrid Email sent: {from_name} -> {to_email} | BCC: {', '.join(final_bcc) if final_bcc else 'none'} | Subject: {subject}")
                
                return {
                    "success": True,
                    "provider": "sendgrid",
                    "message_id": message_id,
                    "from": from_email,
                    "to": to_email,
                    "bcc": final_bcc,
                    "subject": subject,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                error_detail = response.text
                logger.error(f"❌ SendGrid error {response.status_code}: {error_detail}")
                return {"success": False, "error": f"SendGrid error: {error_detail}"}
                
        except Exception as e:
            logger.error(f"❌ SendGrid exception: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_via_smtp(
        self,
        from_agent_id: str,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]],
        bcc_emails: Optional[List[str]],
        html_body: Optional[str],
        attachment_path: Optional[str],
        provider_email: Optional[str]
    ) -> Dict:
        """Fallback: Send email via DreamHost SMTP (may not work on Railway)"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
            msg['X-Agent-ID'] = from_agent_id
            msg['X-System'] = "Revisar.IA"
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            final_bcc = _build_bcc_list(provider_email, bcc_emails)
            if final_bcc:
                msg['Bcc'] = ', '.join(final_bcc)
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment_path)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            if final_bcc:
                recipients.extend(final_bcc)
            
            smtp = self._get_smtp_connection(from_agent_id, from_email)
            if not smtp:
                return {"success": False, "error": "SMTP connection failed"}
            
            smtp.sendmail(from_email, recipients, msg.as_string())
            smtp.quit()
            
            message_id = msg.get('Message-ID', f"{from_agent_id}_{datetime.now().timestamp()}")
            
            logger.info(f"📧 SMTP Email sent: {from_name} -> {to_email} | BCC: {', '.join(final_bcc) if final_bcc else 'none'} | Subject: {subject}")
            
            return {
                "success": True,
                "provider": "dreamhost_smtp",
                "message_id": message_id,
                "from": from_email,
                "to": to_email,
                "bcc": final_bcc,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ SMTP Failed to send email from {from_agent_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def send_agent_to_agent(
        self,
        from_agent_id: str,
        to_agent_id: str,
        subject: str,
        body: str,
        cc_agent_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None
    ) -> Dict:
        """
        Send email between agents (for deliberation)
        
        Args:
            from_agent_id: Sending agent ID
            to_agent_id: Receiving agent ID
            subject: Email subject
            body: Email body
            cc_agent_ids: Optional list of agent IDs to CC
            project_id: Optional project ID for tracking
        
        Returns:
            Dict with send result
        """
        to_email = AGENT_EMAILS.get(to_agent_id)
        if not to_email:
            return {"success": False, "error": f"Unknown recipient agent: {to_agent_id}"}
        
        cc_emails = []
        if cc_agent_ids:
            cc_emails = [AGENT_EMAILS[aid] for aid in cc_agent_ids if aid in AGENT_EMAILS]
        
        if project_id:
            subject = f"[Proyecto: {project_id[:8]}] {subject}"
        
        return self.send_email(
            from_agent_id=from_agent_id,
            to_email=to_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails
        )
    
    def send_to_provider(
        self,
        from_agent_id: str,
        provider_email: str,
        subject: str,
        body: str,
        project_id: Optional[str] = None,
        cc_pmo: bool = True
    ) -> Dict:
        """
        Send email to external provider (for requesting adjustments)
        
        Args:
            from_agent_id: Agent sending the request
            provider_email: Provider's email
            subject: Email subject
            body: Email body
            project_id: Project ID for tracking
            cc_pmo: Whether to CC the PMO agent
        
        Returns:
            Dict with send result
        """
        cc_emails = []
        if cc_pmo:
            cc_emails.append(AGENT_EMAILS["A2_PMO"])
        
        if project_id:
            subject = f"[Solicitud de Ajustes - Proyecto: {project_id[:8]}] {subject}"
        
        return self.send_email(
            from_agent_id=from_agent_id,
            to_email=provider_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails
        )
    
    def read_inbox(
        self,
        agent_id: str,
        limit: int = 10,
        unread_only: bool = True
    ) -> List[Dict]:
        """
        Read emails from an agent's inbox
        
        Args:
            agent_id: Agent ID
            limit: Max emails to retrieve
            unread_only: Only get unread emails
        
        Returns:
            List of email dicts
        """
        agent_email = AGENT_EMAILS.get(agent_id)
        if not agent_email:
            return []
        
        if not self.initialized:
            logger.warning("Email service not initialized - cannot read inbox")
            return []
        
        try:
            imap = self._get_imap_connection(agent_id, agent_email)
            if not imap:
                return []
            
            imap.select('INBOX')
            
            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            _, message_numbers = imap.search(None, search_criteria)
            
            emails = []
            message_ids = message_numbers[0].split()[-limit:] if message_numbers[0] else []
            
            for msg_id in message_ids:
                _, msg_data = imap.fetch(msg_id, '(RFC822)')
                if msg_data is None or len(msg_data) == 0 or msg_data[0] is None:
                    continue
                email_body = msg_data[0][1]
                if not isinstance(email_body, bytes):
                    continue
                msg = email.message_from_bytes(email_body)
                
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                body_text = payload.decode('utf-8', errors='ignore')
                            break
                else:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_text = payload.decode('utf-8', errors='ignore')
                
                emails.append({
                    "message_id": msg.get('Message-ID', ''),
                    "from": msg.get('From', ''),
                    "to": msg.get('To', ''),
                    "subject": msg.get('Subject', ''),
                    "date": msg.get('Date', ''),
                    "body": body_text,
                    "x_agent_id": msg.get('X-Agent-ID', ''),
                    "x_system": msg.get('X-System', '')
                })
            
            imap.close()
            imap.logout()
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to read inbox for {agent_id}: {e}")
            return []
    
    def send_email_with_attachments(
        self,
        from_agent_id: str,
        to_email: str,
        subject: str,
        body: str,
        attachments: List[str],
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        html_body: Optional[str] = None,
        provider_email: Optional[str] = None
    ) -> Dict:
        """
        Send email with multiple attachments from an agent
        
        Args:
            from_agent_id: Agent ID (A1_SPONSOR, A2_PMO, etc.)
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            attachments: List of file paths to attach (PDFs)
            cc_emails: List of CC recipients
            bcc_emails: List of additional BCC recipients
            html_body: Optional HTML body
            provider_email: Provider email to auto-BCC (from project)
        
        Returns:
            Dict with success status and message_id
        """
        if not self.initialized:
            logger.warning("Email service not initialized - logging email only")
            return self._log_email_with_attachments(from_agent_id, to_email, subject, body, attachments)
        
        from_email = AGENT_EMAILS.get(from_agent_id)
        from_name = AGENT_NAMES.get(from_agent_id, "Sistema")
        
        if not from_email:
            return {"success": False, "error": f"Unknown agent: {from_agent_id}"}
        
        try:
            msg = MIMEMultipart('mixed')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
            msg['X-Agent-ID'] = from_agent_id
            msg['X-System'] = "Revisar.IA"
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            final_bcc = _build_bcc_list(provider_email, bcc_emails)
            if final_bcc:
                msg['Bcc'] = ', '.join(final_bcc)
            
            text_part = MIMEMultipart('alternative')
            text_part.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if html_body:
                text_part.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            msg.attach(text_part)
            
            attached_files = []
            for attachment_path in attachments:
                if attachment_path and os.path.exists(attachment_path):
                    try:
                        with open(attachment_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(attachment_path)
                            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                            msg.attach(part)
                            attached_files.append(filename)
                            logger.info(f"Attached file: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to attach file {attachment_path}: {e}")
                else:
                    logger.warning(f"Attachment not found: {attachment_path}")
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            if final_bcc:
                recipients.extend(final_bcc)
            
            logger.info(f"[EMAIL] Preparing to send from {from_agent_id} ({from_email}) to {to_email}")
            logger.info(f"[EMAIL] Recipients: {recipients}")
            logger.info(f"[EMAIL] BCC: {', '.join(final_bcc) if final_bcc else 'none'}")
            logger.info(f"[EMAIL] Attachments to send: {attached_files}")
            
            smtp = self._get_smtp_connection(from_agent_id, from_email)
            if not smtp:
                logger.error(f"[EMAIL] ❌ Failed to establish SMTP connection for external email to {to_email}")
                return {"success": False, "error": "SMTP connection failed"}
            
            logger.info(f"[EMAIL] Sending email via SMTP...")
            smtp.sendmail(from_email, recipients, msg.as_string())
            smtp.quit()
            
            message_id = msg.get('Message-ID', f"{from_agent_id}_{datetime.now().timestamp()}")
            
            logger.info(f"[EMAIL] ✅ Email SENT with {len(attached_files)} attachments: {from_name} -> {to_email} | BCC: {', '.join(final_bcc) if final_bcc else 'none'}")
            
            return {
                "success": True,
                "message_id": message_id,
                "from": from_email,
                "to": to_email,
                "bcc": final_bcc,
                "subject": subject,
                "attachments": attached_files,
                "attachment_count": len(attached_files),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email with attachments from {from_agent_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _log_email_with_attachments(
        self,
        from_agent_id: str,
        to_email: str,
        subject: str,
        body: str,
        attachments: List[str]
    ) -> Dict:
        """Log email with attachments when service is not configured (demo mode)"""
        from_name = AGENT_NAMES.get(from_agent_id, "Sistema")
        from_email = AGENT_EMAILS.get(from_agent_id, "system@revisar-ia.com")
        
        attachment_names = [os.path.basename(a) for a in attachments if a and os.path.exists(a)]
        
        logger.info(f"""
========== EMAIL LOG WITH ATTACHMENTS (Demo Mode) ==========
From: {from_name} <{from_email}>
To: {to_email}
Subject: {subject}
Date: {datetime.now(timezone.utc).isoformat()}
Attachments: {', '.join(attachment_names) if attachment_names else 'None'}
-------------------------------------------------------------
{body[:500]}{'...' if len(body) > 500 else ''}
=============================================================
""")
        
        return {
            "success": True,
            "demo_mode": True,
            "message_id": f"demo_{datetime.now().timestamp()}",
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "attachments": attachment_names,
            "attachment_count": len(attachment_names),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _log_email(self, from_agent_id: str, to_email: str, subject: str, body: str) -> Dict:
        """Log email when service is not configured (demo mode)"""
        from_name = AGENT_NAMES.get(from_agent_id, "Sistema")
        from_email = AGENT_EMAILS.get(from_agent_id, "system@revisar-ia.com")
        
        logger.info(f"""
========== EMAIL LOG (Demo Mode) ==========
From: {from_name} <{from_email}>
To: {to_email}
Subject: {subject}
Date: {datetime.now(timezone.utc).isoformat()}
-------------------------------------------
{body[:500]}{'...' if len(body) > 500 else ''}
============================================
""")
        
        return {
            "success": True,
            "demo_mode": True,
            "message_id": f"demo_{datetime.now().timestamp()}",
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def send_user_approval_notification(self, user_email: str, user_name: str) -> Dict:
        """
        Send email notification when a user account has been approved
        
        Args:
            user_email: The approved user's email address
            user_name: The approved user's full name
        
        Returns:
            Dict with success status
        """
        subject = "Tu cuenta ha sido aprobada - Revisar.ia"
        
        plain_body = f"""Estimado/a {user_name},

¡Buenas noticias! Tu cuenta en Revisar.ia ha sido aprobada.

Ya puedes iniciar sesión en la plataforma con tu email y contraseña registrados.

Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.

Saludos cordiales,
Carlos Mendoza
PMO - Revisar.ia
"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
        .success-badge {{ background: #48bb78; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-weight: bold; }}
        .footer {{ background: #f7fafc; padding: 20px; text-align: center; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px; font-size: 12px; color: #718096; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Revisar.ia</h1>
        </div>
        <div class="content">
            <span class="success-badge">Cuenta Aprobada</span>
            <p>Estimado/a <strong>{user_name}</strong>,</p>
            <p>¡Buenas noticias! Tu cuenta en Revisar.ia ha sido <strong>aprobada</strong>.</p>
            <p>Ya puedes iniciar sesión en la plataforma con tu email y contraseña registrados.</p>
            <p>Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.</p>
            <p>Saludos cordiales,<br>
            <strong>Carlos Mendoza</strong><br>
            PMO - Revisar.ia</p>
        </div>
        <div class="footer">
            <p>Revisar.ia | Sistema de Gestión Multi-Agente</p>
            <p>Este es un mensaje automático, por favor no responder directamente.</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(
            from_agent_id="A2_PMO",
            to_email=user_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )

    def send_user_rejection_notification(self, user_email: str, user_name: str) -> Dict:
        """
        Send email notification when a user account has been rejected
        
        Args:
            user_email: The rejected user's email address
            user_name: The rejected user's full name
        
        Returns:
            Dict with success status
        """
        subject = "Actualización sobre tu solicitud - Revisar.ia"
        
        plain_body = f"""Estimado/a {user_name},

Gracias por tu interés en Revisar.ia.

Lamentamos informarte que tu solicitud de acceso no ha sido aprobada en este momento.

Si crees que esto es un error o deseas más información, por favor contacta al administrador del sistema.

Saludos cordiales,
Carlos Mendoza
PMO - Revisar.ia
"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
        .info-badge {{ background: #718096; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-weight: bold; }}
        .footer {{ background: #f7fafc; padding: 20px; text-align: center; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px; font-size: 12px; color: #718096; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Revisar.ia</h1>
        </div>
        <div class="content">
            <span class="info-badge">Actualización de Solicitud</span>
            <p>Estimado/a <strong>{user_name}</strong>,</p>
            <p>Gracias por tu interés en Revisar.ia.</p>
            <p>Lamentamos informarte que tu solicitud de acceso no ha sido aprobada en este momento.</p>
            <p>Si crees que esto es un error o deseas más información, por favor contacta al administrador del sistema.</p>
            <p>Saludos cordiales,<br>
            <strong>Carlos Mendoza</strong><br>
            PMO - Revisar.ia</p>
        </div>
        <div class="footer">
            <p>Revisar.ia | Sistema de Gestión Multi-Agente</p>
            <p>Este es un mensaje automático, por favor no responder directamente.</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(
            from_agent_id="A2_PMO",
            to_email=user_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )

    def test_connection(self, agent_id: str = "A2_PMO") -> Dict:
        """Test email connection for an agent"""
        agent_email = AGENT_EMAILS.get(agent_id)
        if not agent_email:
            return {"success": False, "error": f"Unknown agent: {agent_id}"}
        
        if not self.initialized:
            return {"success": False, "error": "Email service not configured"}
        
        password = self._get_agent_password(agent_id)
        if not password:
            return {"success": False, "error": f"No password configured for agent: {agent_id}"}
        
        try:
            smtp = self._get_smtp_connection(agent_id, agent_email)
            if smtp:
                smtp.quit()
                return {
                    "success": True,
                    "agent": agent_id,
                    "email": agent_email,
                    "smtp_host": self.smtp_host,
                    "smtp_port": self.smtp_port,
                    "imap_host": self.imap_host
                }
            return {"success": False, "error": "SMTP connection failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


email_service = DreamHostEmailService()
