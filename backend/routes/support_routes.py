"""
Support Routes for Revisar.IA Chatbot
Handles support messages, conversation history, and escalation to human support.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import logging
import urllib.parse

from services.support.support_agent import get_support_response, WHATSAPP_NUMBER, build_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["Support"])

conversations: Dict[str, List[Dict]] = {}


class WhatsAppInfo(BaseModel):
    number: str
    message: str
    url: str


class MessageInput(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    userName: Optional[str] = None
    userEmail: Optional[str] = None


class MessageResponse(BaseModel):
    success: bool
    session_id: str
    response: str
    timestamp: str
    showWhatsApp: bool = False
    whatsapp: Optional[WhatsAppInfo] = None


class EscalateInput(BaseModel):
    session_id: str
    reason: Optional[str] = None
    email: Optional[str] = None


class EscalateResponse(BaseModel):
    success: bool
    message: str
    ticket_id: Optional[str] = None


class ConversationHistory(BaseModel):
    success: bool
    session_id: str
    messages: List[Dict]


class WhatsAppLinkResponse(BaseModel):
    success: bool
    number: str
    url: str
    message: str


@router.post("/message", response_model=MessageResponse)
async def send_message(input: MessageInput):
    """
    Send a message to the support chatbot and get a response.
    """
    try:
        session_id = input.session_id or str(uuid.uuid4())
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        user_msg = {
            "role": "user",
            "content": input.message,
            "timestamp": datetime.utcnow().isoformat()
        }
        conversations[session_id].append(user_msg)
        
        response_data = await get_support_response(
            user_message=input.message,
            conversation_history=conversations[session_id][:-1],
            user_name=input.userName,
            user_email=input.userEmail
        )
        
        assistant_msg = {
            "role": "assistant",
            "content": response_data["text"],
            "timestamp": datetime.utcnow().isoformat(),
            "show_whatsapp": response_data["show_whatsapp"]
        }
        conversations[session_id].append(assistant_msg)
        
        if len(conversations[session_id]) > 100:
            conversations[session_id] = conversations[session_id][-100:]
        
        whatsapp_info = None
        if response_data["show_whatsapp"]:
            whatsapp_url = f"https://wa.me/{response_data['whatsapp_number']}?text={response_data['whatsapp_message']}"
            whatsapp_info = WhatsAppInfo(
                number=response_data["whatsapp_number"],
                message=response_data["whatsapp_message"],
                url=whatsapp_url
            )
        
        return MessageResponse(
            success=True,
            session_id=session_id,
            response=response_data["text"],
            timestamp=datetime.utcnow().isoformat(),
            showWhatsApp=response_data["show_whatsapp"],
            whatsapp=whatsapp_info
        )
        
    except Exception as e:
        logger.error(f"Error processing support message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar tu mensaje. Por favor intenta de nuevo."
        )


@router.get("/whatsapp", response_model=WhatsAppLinkResponse)
async def get_whatsapp_link(message: Optional[str] = None, context: Optional[str] = None):
    """
    Get WhatsApp link for direct contact with support.
    """
    encoded_message = build_whatsapp_message(message or "Necesito ayuda", context)
    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded_message}"
    
    return WhatsAppLinkResponse(
        success=True,
        number=WHATSAPP_NUMBER,
        url=whatsapp_url,
        message=encoded_message
    )


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_history(session_id: str):
    """
    Get the conversation history for a session.
    """
    if session_id not in conversations:
        return ConversationHistory(
            success=True,
            session_id=session_id,
            messages=[]
        )
    
    return ConversationHistory(
        success=True,
        session_id=session_id,
        messages=conversations[session_id]
    )


@router.post("/escalate", response_model=EscalateResponse)
async def escalate_to_human(input: EscalateInput):
    """
    Escalate the conversation to human support.
    """
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        escalation_msg = {
            "role": "system",
            "content": f"Conversación escalada a soporte humano. Ticket: {ticket_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if input.session_id in conversations:
            conversations[input.session_id].append(escalation_msg)
        
        logger.info(f"Conversation escalated: {ticket_id}, session: {input.session_id}, reason: {input.reason}")
        
        return EscalateResponse(
            success=True,
            message=f"Tu conversación ha sido escalada a nuestro equipo de soporte. Tu número de ticket es **{ticket_id}**. Te contactaremos pronto a través de soporte@revisar.ia.",
            ticket_id=ticket_id
        )
        
    except Exception as e:
        logger.error(f"Error escalating conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al escalar la conversación. Por favor contacta directamente a soporte@revisar.ia"
        )


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Clear the conversation history for a session.
    """
    if session_id in conversations:
        del conversations[session_id]
    
    return {"success": True, "message": "Historial eliminado"}
