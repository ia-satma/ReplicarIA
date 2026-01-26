import os
import httpx
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


async def get_sendgrid_credentials() -> Dict[str, str]:
    """
    Get SendGrid credentials from environment variables or Replit connector.
    Priority: Direct env vars > Replit connector
    """
    # First try direct environment variables (works on Railway, Render, etc.)
    api_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@revisar-ia.com')

    if api_key:
        logger.debug("Using SendGrid credentials from environment variables")
        return {"api_key": api_key, "from_email": from_email}

    # Fall back to Replit connector
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    if not hostname:
        raise ValueError("SendGrid not configured - set SENDGRID_API_KEY or use Replit connector")

    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')

    if repl_identity:
        x_replit_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_replit_token = f"depl {web_repl_renewal}"
    else:
        raise ValueError("X_REPLIT_TOKEN not found for repl/depl")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=sendgrid",
            headers={
                "Accept": "application/json",
                "X_REPLIT_TOKEN": x_replit_token
            }
        )
        data = response.json()

    connection_settings = data.get('items', [{}])[0] if data.get('items') else {}
    settings = connection_settings.get('settings', {})

    api_key = settings.get('api_key')
    from_email = settings.get('from_email')

    if not api_key or not from_email:
        raise ValueError("SendGrid not connected - missing api_key or from_email")

    return {"api_key": api_key, "from_email": from_email}


def is_configured() -> bool:
    """Check if email service is configured via env vars or Replit connector"""
    return bool(
        os.environ.get('SENDGRID_API_KEY') or
        os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    )


class EmailService:
    
    def __init__(self):
        self._configured = is_configured()

        if self._configured:
            if os.environ.get('SENDGRID_API_KEY'):
                logger.info("✅ Email service configured with SendGrid via environment variables")
            else:
                logger.info("✅ Email service configured with SendGrid via Replit connector")
        else:
            logger.warning("⚠️ Email service not configured - running in demo mode. Set SENDGRID_API_KEY to enable.")
    
    def is_available(self) -> bool:
        return self._configured
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not self._configured:
            logger.info(f"📧 [DEMO] Email simulado a {to}: {subject}")
            return {
                "success": True,
                "simulado": True,
                "message_id": f"demo-{id(subject)}",
                "to": to,
                "subject": subject
            }
        
        try:
            credentials = await get_sendgrid_credentials()
            api_key = credentials["api_key"]
            from_email = credentials["from_email"]
            
            personalizations = [{
                "to": [{"email": to}]
            }]
            
            if cc:
                personalizations[0]["cc"] = [{"email": email} for email in cc]
            if bcc:
                personalizations[0]["bcc"] = [{"email": email} for email in bcc]
            
            content = []
            if body_text:
                content.append({"type": "text/plain", "value": body_text})
            content.append({"type": "text/html", "value": body_html})
            
            payload = {
                "personalizations": personalizations,
                "from": {"email": from_email, "name": "Revisar.IA"},
                "subject": subject,
                "content": content
            }
            
            if attachments:
                sg_attachments = []
                for attachment in attachments:
                    import base64
                    filename = attachment.get('filename', 'attachment')
                    file_content = attachment.get('content')
                    
                    if isinstance(file_content, str):
                        if Path(file_content).exists():
                            with open(file_content, 'rb') as f:
                                file_content = f.read()
                        else:
                            file_content = file_content.encode('utf-8')
                    
                    sg_attachments.append({
                        "content": base64.b64encode(file_content).decode('utf-8'),
                        "filename": filename,
                        "type": "application/octet-stream",
                        "disposition": "attachment"
                    })
                payload["attachments"] = sg_attachments
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"✅ Email enviado via SendGrid a {to}: {subject}")
                    return {
                        "success": True,
                        "simulado": False,
                        "to": to,
                        "subject": subject
                    }
                else:
                    error_msg = response.text
                    logger.error(f"❌ SendGrid error {response.status_code}: {error_msg}")
                    return {
                        "success": False,
                        "error": f"SendGrid error: {error_msg}",
                        "to": to,
                        "subject": subject
                    }
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to,
                "subject": subject
            }
    
    async def send_defense_file_notification(
        self,
        to: str,
        empresa_nombre: str,
        proyecto_nombre: str,
        pdf_link: str,
        score_total: int
    ) -> Dict[str, Any]:
        subject = f"Expediente de Defensa Generado - {proyecto_nombre}"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #16213e; padding: 30px; border-radius: 0 0 12px 12px; }}
                .score {{ font-size: 48px; font-weight: bold; color: #10b981; text-align: center; margin: 20px 0; }}
                .btn {{ display: inline-block; background: #6366f1; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; margin: 20px 0; }}
                .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Revisar.IA - Expediente de Defensa</h1>
                </div>
                <div class="content">
                    <p>Estimado equipo de <strong>{empresa_nombre}</strong>,</p>
                    <p>El expediente de defensa para el proyecto <strong>"{proyecto_nombre}"</strong> ha sido generado exitosamente.</p>
                    
                    <div class="score">
                        {score_total}/100
                    </div>
                    <p style="text-align: center; color: #888;">Puntuacion de Materialidad</p>
                    
                    <p style="text-align: center;">
                        <a href="{pdf_link}" class="btn">Descargar Expediente</a>
                    </p>
                    
                    <p>Este expediente incluye:</p>
                    <ul>
                        <li>Analisis de razon de negocios (Art. 5-A CFF)</li>
                        <li>Verificacion fiscal LISR Art. 27</li>
                        <li>Due diligence del proveedor</li>
                        <li>Deliberacion multi-agente</li>
                        <li>Evidencias y trazabilidad completa</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Este correo fue generado automaticamente por Revisar.IA</p>
                    <p>2024 Revisar.IA - Sistema de Auditoria Fiscal Inteligente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to=to, subject=subject, body_html=body_html)


email_service = EmailService()


async def send_email(
    to: str,
    subject: str,
    body_html: str,
    **kwargs
) -> Dict[str, Any]:
    return await email_service.send_email(to, subject, body_html, **kwargs)
