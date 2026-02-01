"""
OTP Authentication Routes for Revisar.IA
Handles OTP request, verification, session management
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from services.otp_auth_service import otp_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/otp", tags=["OTP Authentication"])


class OTPRequestInput(BaseModel):
    email: EmailStr


class OTPVerifyInput(BaseModel):
    email: EmailStr
    code: str


class OTPResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.get("/status")
async def get_otp_status():
    """
    Endpoint de diagnóstico para verificar el estado del sistema OTP.
    Útil para debugging y verificar configuración.
    """
    from services.otp_auth_service import DATABASE_URL, EMAIL_CONFIGURED, DEMO_MODE, ADMIN_EMAIL, get_db_connection

    db_configured = bool(DATABASE_URL)

    # Test database connection
    db_connected = False
    tables_exist = False
    if db_configured:
        try:
            conn = await get_db_connection()
            if conn:
                db_connected = True
                # Check if tables exist
                result = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usuarios_autorizados')"
                )
                tables_exist = result
                await conn.close()
        except Exception as e:
            logger.error(f"DB connection test failed: {e}")

    warnings = []
    if not db_configured:
        warnings.append("DATABASE_URL not configured - using demo mode (only admin email works)")
    elif not db_connected:
        warnings.append("DATABASE_URL configured but connection failed")
    elif not tables_exist:
        warnings.append("Database connected but 'usuarios_autorizados' table missing - run 001_otp_legacy_tables.sql")
    if not EMAIL_CONFIGURED:
        warnings.append("DREAMHOST_EMAIL_PASSWORD not configured - OTP codes will only be logged/shown in response")

    return {
        "status": "operational",
        "config": {
            "database_configured": db_configured,
            "database_connected": db_connected,
            "tables_exist": tables_exist,
            "email_configured": EMAIL_CONFIGURED,
            "demo_mode": DEMO_MODE,
            "admin_email": ADMIN_EMAIL
        },
        "warnings": warnings,
        "help": {
            "no_email": "Sin email configurado, el código OTP aparecerá en '_dev_code' de la respuesta",
            "tables_missing": "Ejecuta: psql $DATABASE_URL -f database/001_otp_legacy_tables.sql"
        }
    }


@router.post("/request-code", response_model=OTPResponse)
async def request_otp_code(input: OTPRequestInput):
    from services.otp_auth_service import check_lockout, check_rate_limit, EMAIL_CONFIGURED

    email = input.email.lower()

    # Security: Check lockout first
    if check_lockout(email):
        raise HTTPException(
            status_code=429,
            detail="Cuenta temporalmente bloqueada por múltiples intentos fallidos. Intenta en 15 minutos."
        )

    user = await otp_auth_service.check_authorized_email(email)
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Este correo no está autorizado para acceder al sistema. Contacta al administrador."
        )

    codigo = await otp_auth_service.create_otp_code(email, user['id'])
    if not codigo:
        # Could be rate limited or other error
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Por favor espera 1 minuto antes de solicitar otro código."
        )

    email_result = await otp_auth_service.send_otp_email(
        email=email,
        codigo=codigo,
        nombre=user.get('nombre', '')
    )

    logger.info(f"OTP requested for {email}, email sent: {email_result.get('success')}, demo_mode: {email_result.get('demo_mode', False)}")

    response_data = {
        "email": email,
        "nombre": user.get('nombre'),
        "rol": user.get('rol', 'user'),
        "empresa": user.get('empresa'),
        "expires_in_minutes": 5,
        "is_admin": user.get('rol') in ['admin', 'super_admin']
    }

    # En modo desarrollo (sin email), incluir el código en la respuesta
    if not EMAIL_CONFIGURED or email_result.get('demo_mode'):
        response_data["_dev_code"] = codigo
        response_data["_dev_warning"] = "⚠️ Email no configurado. Usa este código para autenticarte."
        logger.warning("=" * 60)
        logger.warning(f"🔐 DEV MODE - OTP Code for {email}: {codigo}")
        logger.warning("=" * 60)

    message = "Código enviado a tu correo electrónico"
    if not EMAIL_CONFIGURED:
        message = f"Código generado: revisa '_dev_code' en la respuesta (email no configurado)"

    return OTPResponse(
        success=True,
        message=message,
        data=response_data
    )


@router.post("/verify-code", response_model=OTPResponse)
async def verify_otp_code(input: OTPVerifyInput):
    from services.otp_auth_service import check_lockout, MAX_VERIFICATION_ATTEMPTS, _verification_attempts

    email = input.email.lower()
    code = input.code.strip()

    # Security: Check lockout first
    if check_lockout(email):
        raise HTTPException(
            status_code=429,
            detail="Cuenta temporalmente bloqueada por múltiples intentos fallidos. Intenta en 15 minutos."
        )

    if len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El código debe ser de 6 dígitos"
        )

    session = await otp_auth_service.verify_otp_code(email, code)
    if not session:
        # Check how many attempts remain
        attempts = _verification_attempts.get(email.lower(), 0)
        remaining = MAX_VERIFICATION_ATTEMPTS - attempts
        if remaining <= 0:
            raise HTTPException(
                status_code=429,
                detail="Cuenta bloqueada por múltiples intentos fallidos. Intenta en 15 minutos."
            )
        raise HTTPException(
            status_code=401,
            detail=f"Código inválido o expirado. Te quedan {remaining} intento(s)."
        )
    
    logger.info(f"OTP verified for {email}")
    
    return OTPResponse(
        success=True,
        message="Autenticación exitosa",
        data=session
    )


@router.get("/session", response_model=OTPResponse)
async def get_current_session(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación requerido"
        )
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    session = await otp_auth_service.validate_session(token)
    if session:
        return OTPResponse(
            success=True,
            message="Sesión válida",
            data=session
        )
    
    from jose import jwt, exceptions as jose_exceptions
    import os
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"

    # Security: Validate SECRET_KEY exists
    if not SECRET_KEY or len(SECRET_KEY) < 16:
        logger.error("SECRET_KEY not configured or too short - JWT validation disabled")
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o expirada"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id:
            from services.user_db import user_service
            user = await user_service.get_user_by_id(user_id)
            if user:
                return OTPResponse(
                    success=True,
                    message="Sesión válida (JWT)",
                    data={
                        "user": {
                            "id": str(user.id),
                            "email": str(user.email),
                            "nombre": getattr(user, 'full_name', '') or '',
                            "empresa": getattr(user, 'company', '') or '',
                            "rol": str(user.role) if user.role else 'user',
                            "role": str(user.role) if user.role else 'user'
                        },
                        "token": token
                    }
                )
    except (jose_exceptions.ExpiredSignatureError, jose_exceptions.JWTError):
        pass
    
    raise HTTPException(
        status_code=401,
        detail="Sesión inválida o expirada"
    )


@router.post("/logout", response_model=OTPResponse)
async def logout(authorization: Optional[str] = Header(None)):
    if not authorization:
        return OTPResponse(success=True, message="Sesión cerrada")

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    await otp_auth_service.end_session(token)

    return OTPResponse(
        success=True,
        message="Sesión cerrada exitosamente"
    )


@router.get("/test-email")
async def test_email_connection():
    """
    Endpoint para verificar configuración del servicio de email unificado (SendGrid/DreamHost).
    Solo para diagnóstico.
    """
    import os
    from services.email_service import is_configured, get_email_provider

    sendgrid_key = os.environ.get('SENDGRID_API_KEY', '')
    dreamhost_pwd = os.environ.get('DREAMHOST_EMAIL_PASSWORD', '')

    result = {
        "email_configured": is_configured(),
        "provider": get_email_provider(),
        "sendgrid_configured": bool(sendgrid_key),
        "sendgrid_key_length": len(sendgrid_key) if sendgrid_key else 0,
        "dreamhost_configured": bool(dreamhost_pwd),
        "sendgrid_from_email": os.environ.get('SENDGRID_FROM_EMAIL', 'NOT SET'),
        "status": "✅ EMAIL SERVICE OK" if is_configured() else "❌ EMAIL NOT CONFIGURED"
    }

    return result


@router.get("/trigger-otp/{email}")
async def trigger_otp_test(email: str):
    """
    Endpoint GET para probar el flujo completo de OTP.
    SOLO PARA TESTING - envía un OTP real al email especificado.
    """
    from services.otp_auth_service import otp_auth_service, EMAIL_CONFIGURED

    result = {
        "email": email,
        "email_configured": EMAIL_CONFIGURED,
        "steps": []
    }

    if not EMAIL_CONFIGURED:
        result["success"] = False
        result["error"] = "Email service not configured"
        return result

    try:
        # 1. Verificar email autorizado
        user = await otp_auth_service.check_authorized_email(email)
        result["steps"].append({"step": "check_email", "success": bool(user), "user": user.get("nombre") if user else None})

        if not user:
            result["success"] = False
            result["error"] = f"Email {email} no está autorizado"
            return result

        # 2. Crear código OTP
        codigo = await otp_auth_service.create_otp_code(email, user.get("id", 1))
        result["steps"].append({"step": "create_otp", "success": bool(codigo), "codigo_created": bool(codigo)})

        # Guardar el código para mostrarlo si falla el envío
        result["otp_code"] = codigo

        if not codigo:
            result["success"] = False
            result["error"] = "No se pudo crear el código OTP (rate limit o error DB)"
            return result

        # 3. Enviar email
        email_result = await otp_auth_service.send_otp_email(email, codigo, user.get("nombre", ""))
        result["steps"].append({"step": "send_email", "result": email_result})

        result["success"] = email_result.get("success", False)
        result["message"] = "OTP enviado exitosamente" if result["success"] else "Error al enviar OTP"

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["error_type"] = type(e).__name__

    return result


@router.post("/send-test-email")
async def send_test_email(input: OTPRequestInput):
    """
    Envía un email de prueba al correo especificado.
    Solo para diagnóstico - requiere que el email esté autorizado.
    """
    from services.dreamhost_email_service import email_service
    from services.otp_auth_service import EMAIL_CONFIGURED

    email = input.email.lower()

    if not EMAIL_CONFIGURED:
        return {
            "success": False,
            "error": "Email no configurado",
            "message": "DREAMHOST_EMAIL_PASSWORD no está en las variables de entorno"
        }

    # Verificar que el email esté autorizado
    user = await otp_auth_service.check_authorized_email(email)
    if not user:
        return {
            "success": False,
            "error": "Email no autorizado",
            "message": "Este email no está en usuarios_autorizados"
        }

    # Enviar email de prueba
    result = email_service.send_email(
        from_agent_id="A2_PMO",
        to_email=email,
        subject="🔧 Prueba de conexión - Revisar.IA",
        body=f"""
Hola {user.get('nombre', 'Usuario')},

Este es un email de prueba del sistema Revisar.IA.

Si recibes este mensaje, la configuración de email está funcionando correctamente.

Detalles:
- Email destino: {email}
- Sistema: Revisar.IA
- Agente remitente: A2_PMO (pmo@revisar-ia.com)

Saludos,
Sistema Revisar.IA
        """,
        html_body=f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a365d;">🔧 Prueba de Conexión</h2>
            <p>Hola <strong>{user.get('nombre', 'Usuario')}</strong>,</p>
            <p>Este es un email de prueba del sistema <strong>Revisar.IA</strong>.</p>
            <p style="background: #e8f5e9; padding: 15px; border-radius: 8px; color: #2e7d32;">
                ✅ Si recibes este mensaje, la configuración de email está funcionando correctamente.
            </p>
            <hr>
            <small style="color: #666;">
                Email destino: {email}<br>
                Agente remitente: A2_PMO (pmo@revisar-ia.com)
            </small>
        </body>
        </html>
        """
    )

    return {
        "success": result.get("success", False),
        "demo_mode": result.get("demo_mode", False),
        "message_id": result.get("message_id"),
        "error": result.get("error"),
        "from": result.get("from"),
        "to": result.get("to"),
        "note": "Si demo_mode=true, el email solo se logueó pero NO se envió realmente"
    }
