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


@router.post("/request-code", response_model=OTPResponse)
async def request_otp_code(input: OTPRequestInput):
    email = input.email.lower()
    
    user = await otp_auth_service.check_authorized_email(email)
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Este correo no está autorizado para acceder al sistema"
        )
    
    codigo = await otp_auth_service.create_otp_code(email, user['id'])
    if not codigo:
        raise HTTPException(
            status_code=500,
            detail="Error al generar el código de verificación"
        )
    
    email_result = await otp_auth_service.send_otp_email(
        email=email,
        codigo=codigo,
        nombre=user.get('nombre', '')
    )
    
    logger.info(f"OTP requested for {email}, email sent: {email_result.get('success')}")
    
    return OTPResponse(
        success=True,
        message="Código enviado a tu correo electrónico",
        data={
            "email": email,
            "nombre": user.get('nombre'),
            "expires_in_minutes": 5
        }
    )


@router.post("/verify-code", response_model=OTPResponse)
async def verify_otp_code(input: OTPVerifyInput):
    email = input.email.lower()
    code = input.code.strip()
    
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El código debe ser de 6 dígitos"
        )
    
    session = await otp_auth_service.verify_otp_code(email, code)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Código inválido o expirado"
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
