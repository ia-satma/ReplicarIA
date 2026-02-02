"""
OTP Authentication Service for Revisar.IA
Handles 6-digit OTP generation, validation, and session management
Uses asyncpg for PostgreSQL queries
"""

import os
import base64
import secrets
import string
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
import asyncpg

from services.email_service import email_service as unified_email, is_configured as email_is_configured

logger = logging.getLogger(__name__)

def get_logo_base64() -> str:
    """Load and encode the logo as base64 for email embedding"""
    logo_paths = [
        Path(__file__).parent.parent / "static" / "logo-revisar-white.png",
        Path(__file__).parent.parent.parent / "frontend" / "public" / "logo-revisar-white.png",
    ]
    
    for logo_path in logo_paths:
        if logo_path.exists():
            try:
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/png;base64,{logo_data}"
            except Exception as e:
                logger.warning(f"Could not read logo from {logo_path}: {e}")
    
    return ""

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Demo/Fallback mode settings (when PostgreSQL is not available)
DEMO_MODE = os.environ.get('OTP_DEMO_MODE', 'false').lower() == 'true'
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'ia@satma.mx')
ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Administrador SATMA')
ADMIN_COMPANY = os.environ.get('ADMIN_COMPANY', 'SATMA')
DEMO_OTP_CODE = '123456'  # Fixed OTP for demo mode

# Email configuration check - uses unified service (SendGrid or DreamHost)
EMAIL_CONFIGURED = email_is_configured()

OTP_EXPIRATION_MINUTES = 5
SESSION_EXPIRATION_HOURS = 24

# Security settings
MAX_OTP_REQUESTS_PER_MINUTE = 3
MAX_VERIFICATION_ATTEMPTS = 3
LOCKOUT_DURATION_MINUTES = 15

# In-memory stores for demo mode
_demo_sessions: Dict[str, Dict[str, Any]] = {}  # token -> session data
_demo_otp_codes: Dict[str, str] = {}  # email -> otp code

# In-memory rate limiting stores (for Railway deployment)
_rate_limit_store: Dict[str, list] = {}  # email -> [timestamps]
_verification_attempts: Dict[str, int] = {}  # email -> attempt_count
_lockout_store: Dict[str, datetime] = {}  # email -> lockout_until


def check_rate_limit(email: str) -> bool:
    """Check if email has exceeded rate limit for OTP requests"""
    now = datetime.now(timezone.utc)
    email_key = email.lower()

    # Clean old entries
    if email_key in _rate_limit_store:
        _rate_limit_store[email_key] = [
            ts for ts in _rate_limit_store[email_key]
            if (now - ts).total_seconds() < 60
        ]
    else:
        _rate_limit_store[email_key] = []

    # Check if under limit
    if len(_rate_limit_store[email_key]) >= MAX_OTP_REQUESTS_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for {email}")
        return False

    # Add current request
    _rate_limit_store[email_key].append(now)
    return True


def check_lockout(email: str) -> bool:
    """Check if email is currently locked out"""
    email_key = email.lower()
    now = datetime.now(timezone.utc)

    if email_key in _lockout_store:
        if now < _lockout_store[email_key]:
            remaining = (_lockout_store[email_key] - now).total_seconds() / 60
            logger.warning(f"Account {email} is locked for {remaining:.1f} more minutes")
            return True
        else:
            # Lockout expired, clean up
            del _lockout_store[email_key]
            if email_key in _verification_attempts:
                del _verification_attempts[email_key]

    return False


def record_failed_attempt(email: str) -> int:
    """Record a failed verification attempt, return total attempts"""
    email_key = email.lower()

    if email_key not in _verification_attempts:
        _verification_attempts[email_key] = 0

    _verification_attempts[email_key] += 1
    attempts = _verification_attempts[email_key]

    if attempts >= MAX_VERIFICATION_ATTEMPTS:
        # Lock the account
        _lockout_store[email_key] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        logger.warning(f"Account {email} locked after {attempts} failed attempts")

    return attempts


def clear_attempts(email: str):
    """Clear verification attempts after successful verification"""
    email_key = email.lower()
    if email_key in _verification_attempts:
        del _verification_attempts[email_key]
    if email_key in _lockout_store:
        del _lockout_store[email_key]


async def get_db_connection():
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured")
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def generate_otp_code() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


class OTPAuthService:

    async def check_authorized_email(self, email: str) -> Optional[Dict[str, Any]]:
        # Try database first
        conn = await get_db_connection()
        if conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, nombre, empresa, rol, activo, empresa_id
                    FROM usuarios_autorizados
                    WHERE LOWER(email) = LOWER($1) AND activo = true
                    """,
                    email
                )
                if row:
                    result = dict(row)
                    # Ensure empresa_id is a string if present
                    if result.get('empresa_id'):
                        result['empresa_id'] = str(result['empresa_id'])
                    return result
                return None
            except Exception as e:
                logger.error(f"Error checking authorized email: {e}")
            finally:
                await conn.close()

        # Fallback to demo mode if DB not available and email matches admin
        if email.lower() == ADMIN_EMAIL.lower():
            logger.info(f"Demo mode: Authorized admin email {email}")
            return {
                'id': 1,
                'email': ADMIN_EMAIL,
                'nombre': ADMIN_NAME,
                'empresa': ADMIN_COMPANY,
                'rol': 'admin',
                'activo': True
            }

        logger.warning(f"No database and email {email} is not admin - auth denied")
        return None
    
    async def create_otp_code(self, email: str, usuario_id: int) -> Optional[str]:
        # Security: Check rate limit
        if not check_rate_limit(email):
            logger.warning(f"OTP request rate limited for {email}")
            return None

        # Security: Check lockout
        if check_lockout(email):
            logger.warning(f"OTP request rejected - account locked: {email}")
            return None

        # Try database first
        conn = await get_db_connection()
        if conn:
            try:
                await conn.execute(
                    """
                    UPDATE codigos_otp
                    SET usado = true
                    WHERE email = $1 AND usado = false
                    """,
                    email
                )

                codigo = generate_otp_code()
                otp_id = f"otp-{uuid.uuid4().hex[:8]}"

                await conn.execute(
                    """
                    INSERT INTO codigos_otp (id, usuario_id, email, codigo, usado, fecha_creacion, fecha_expiracion)
                    VALUES ($1, $2, $3, $4, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '5 minutes')
                    """,
                    otp_id, str(usuario_id), email, codigo
                )

                logger.info(f"OTP created for {email}")
                return codigo
            except Exception as e:
                logger.error(f"Error creating OTP: {e}")
            finally:
                await conn.close()

        # Fallback to demo mode if DB not available and email is admin
        if email.lower() == ADMIN_EMAIL.lower():
            codigo = generate_otp_code()
            _demo_otp_codes[email.lower()] = codigo
            logger.info(f"Demo mode: OTP created for admin {email}")
            return codigo

        logger.warning(f"No database available and email {email} is not admin")
        return None

    async def verify_otp_code(self, email: str, codigo: str) -> Optional[Dict[str, Any]]:
        # Security: Check lockout first
        if check_lockout(email):
            logger.warning(f"OTP verification rejected - account locked: {email}")
            return None

        # Try database first
        conn = await get_db_connection()
        if conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT c.id, c.usuario_id, c.email, u.nombre, u.empresa, u.rol, u.empresa_id
                    FROM codigos_otp c
                    JOIN usuarios_autorizados u ON c.usuario_id::text = u.id::text
                    WHERE LOWER(c.email) = LOWER($1)
                      AND c.codigo = $2
                      AND c.usado = false
                      AND c.fecha_expiracion > NOW()
                    ORDER BY c.fecha_creacion DESC
                    LIMIT 1
                    """,
                    email, codigo
                )

                if not row:
                    # Security: Record failed attempt
                    attempts = record_failed_attempt(email)
                    logger.warning(f"Invalid or expired OTP for {email} (attempt {attempts}/{MAX_VERIFICATION_ATTEMPTS})")
                    return None

                # Security: Clear attempts on success
                clear_attempts(email)

                await conn.execute(
                    "UPDATE codigos_otp SET usado = true WHERE id = $1",
                    row['id']
                )

                token = generate_session_token()
                session_id = f"ses-{uuid.uuid4().hex[:8]}"

                session_row = await conn.fetchrow(
                    """
                    INSERT INTO sesiones_otp (id, usuario_id, token, activa, fecha_creacion, fecha_expiracion)
                    VALUES ($1, $2, $3, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '24 hours')
                    RETURNING fecha_expiracion
                    """,
                    session_id, row['usuario_id'], token
                )

                logger.info(f"Session created for {email}")
                expires_at = session_row['fecha_expiracion'].isoformat() if session_row else None
                return {
                    "token": token,
                    "user": {
                        "id": row['usuario_id'],
                        "email": row['email'],
                        "nombre": row['nombre'],
                        "empresa": row['empresa'],
                        "empresa_id": str(row['empresa_id']) if row.get('empresa_id') else None,
                        "rol": row['rol'],
                        "role": row['rol']
                    },
                    "expires_at": expires_at
                }
            except Exception as e:
                logger.error(f"Error verifying OTP: {e}")
            finally:
                await conn.close()

        # Fallback to demo mode for admin email
        if email.lower() == ADMIN_EMAIL.lower():
            stored_code = _demo_otp_codes.get(email.lower())
            if stored_code and stored_code == codigo:
                # Clear the used OTP
                del _demo_otp_codes[email.lower()]
                clear_attempts(email)

                token = generate_session_token()
                expires_at = (datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRATION_HOURS)).isoformat()

                # Store session in memory
                _demo_sessions[token] = {
                    "user": {
                        "id": "1",
                        "email": ADMIN_EMAIL,
                        "nombre": ADMIN_NAME,
                        "empresa": ADMIN_COMPANY,
                        "rol": "admin",
                        "role": "admin"
                    },
                    "expires_at": expires_at
                }

                logger.info(f"Demo mode: Session created for admin {email}")
                return {
                    "token": token,
                    "user": _demo_sessions[token]["user"],
                    "expires_at": expires_at
                }
            else:
                attempts = record_failed_attempt(email)
                logger.warning(f"Demo mode: Invalid OTP for {email} (attempt {attempts})")
                return None

        return None

    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        # Check demo sessions first (in-memory)
        if token in _demo_sessions:
            session = _demo_sessions[token]
            expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) < expires_at:
                return {
                    "session_id": f"demo-{token[:8]}",
                    "user": session["user"],
                    "expires_at": session["expires_at"]
                }
            else:
                # Session expired, clean up
                del _demo_sessions[token]
                return None

        # Try database
        conn = await get_db_connection()
        if not conn:
            return None

        try:
            row = await conn.fetchrow(
                """
                SELECT s.id, s.usuario_id, s.fecha_expiracion,
                       u.email, u.nombre, u.empresa, u.rol
                FROM sesiones_otp s
                JOIN usuarios_autorizados u ON s.usuario_id::text = u.id::text
                WHERE s.token = $1
                  AND s.activa = true
                  AND s.fecha_expiracion > NOW()
                """,
                token
            )

            if not row:
                return None

            return {
                "session_id": row['id'],
                "user": {
                    "id": row['usuario_id'],
                    "email": row['email'],
                    "nombre": row['nombre'],
                    "empresa": row['empresa'],
                    "rol": row['rol'],
                    "role": row['rol']
                },
                "expires_at": row['fecha_expiracion'].isoformat() if row['fecha_expiracion'] else None
            }
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
        finally:
            await conn.close()
    
    async def end_session(self, token: str) -> bool:
        # Check demo sessions first
        if token in _demo_sessions:
            del _demo_sessions[token]
            logger.info("Demo session ended")
            return True

        # Try database
        conn = await get_db_connection()
        if not conn:
            return False

        try:
            result = await conn.execute(
                "UPDATE sesiones_otp SET activa = false WHERE token = $1",
                token
            )
            return "UPDATE" in result
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
        finally:
            await conn.close()
    
    async def send_otp_email(self, email: str, codigo: str, nombre: str = "") -> Dict[str, Any]:
        """
        Envía el código OTP por email.

        En modo demo o sin email configurado:
        - Loguea el código de manera visible
        - Devuelve el código en la respuesta para desarrollo
        """
        subject = f"Codigo de acceso {codigo} - Revisar.IA"

        greeting_name = nombre if nombre else "Usuario"

        # Si el email no está configurado o estamos en modo demo, solo loguea
        if not EMAIL_CONFIGURED or DEMO_MODE:
            logger.warning("=" * 60)
            logger.warning(f"⚠️  EMAIL NO CONFIGURADO - MODO DESARROLLO")
            logger.warning(f"📧 Email destino: {email}")
            logger.warning(f"🔐 CÓDIGO OTP: {codigo}")
            logger.warning(f"⏰ Expira en: {OTP_EXPIRATION_MINUTES} minutos")
            logger.warning("=" * 60)
            return {
                "success": True,
                "demo_mode": True,
                "message": "Email service not configured - code logged",
                "codigo_debug": codigo,  # Solo en desarrollo!
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        logo_base64 = get_logo_base64()
        
        if logo_base64:
            logo_html = f'<img src="{logo_base64}" alt="Revisar.IA" style="max-width: 220px; height: auto; margin-bottom: 8px;" />'
        else:
            logo_html = '<h1 style="margin: 0; font-size: 32px; font-weight: 300; letter-spacing: 4px; color: #ffffff;">REVISAR<span style="color: #7FEDD8; font-weight: 600;">.IA</span></h1>'
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 480px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.1);">
                    
                    <tr>
                        <td style="background: linear-gradient(135deg, #0a0f14 0%, #1a2332 100%); padding: 32px 40px; text-align: center;">
                            {logo_html}
                            <p style="margin: 12px 0 0 0; font-size: 11px; letter-spacing: 3px; color: #7FEDD8; text-transform: uppercase;">
                                Auditoria Fiscal Inteligente
                            </p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #333333;">
                                Hola <strong>{greeting_name}</strong>,
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 15px; color: #666666; line-height: 1.5;">
                                Recibimos una solicitud para acceder a tu cuenta. Usa el siguiente codigo de verificacion:
                            </p>
                            
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 32px 0;">
                                <tr>
                                    <td align="center">
                                        <div style="background: linear-gradient(135deg, #0a0f14 0%, #1a2332 100%); border-radius: 12px; padding: 24px 32px; display: inline-block;">
                                            <span style="font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 36px; font-weight: 700; letter-spacing: 6px; color: #7FEDD8;">
                                                {codigo}
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0; font-size: 14px; color: #888888; text-align: center;">
                                Este codigo expira en <strong style="color: #333333;">{OTP_EXPIRATION_MINUTES} minutos</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 24px 40px; border-top: 1px solid #eeeeee;">
                            <p style="margin: 0; font-size: 13px; color: #888888; line-height: 1.6;">
                                Si no solicitaste este codigo, puedes ignorar este mensaje. Tu cuenta esta segura.
                            </p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="background: linear-gradient(135deg, #0a0f14 0%, #1a2332 100%); padding: 20px 40px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #666666;">
                                2026 Revisar.IA - Plataforma de Cumplimiento Fiscal
                            </p>
                            <p style="margin: 8px 0 0 0; font-size: 11px; color: #555555;">
                                Monterrey, N.L. Mexico
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        body_text = f"""
Revisar.IA - Auditoria Fiscal Inteligente

Hola {greeting_name},

Tu codigo de verificacion es: {codigo}

Este codigo expira en {OTP_EXPIRATION_MINUTES} minutos.

Si no solicitaste este codigo, ignora este mensaje.

2026 Revisar.IA - Plataforma de Cumplimiento Fiscal
        """
        
        # Usar el servicio de email unificado (SendGrid o DreamHost según config)
        result = await unified_email.send_email(
            to=email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )
        return result


otp_auth_service = OTPAuthService()
