"""
Support Agent for Revisar.IA
Uses Anthropic Claude via Replit AI Integrations for intelligent support responses.
Includes security layer to protect against prompt injection and config extraction.
"""

import os
import logging
import urllib.parse
from typing import List, Dict, Optional, TypedDict
from datetime import datetime

from .knowledge_base import SOPORTE_KNOWLEDGE_BASE
from ..security.security_layer import (
    check_message_security,
    sanitize_message,
    sanitize_response,
    log_security_event,
    SECURITY_PROMPT_BLOCK
)

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

WHATSAPP_NUMBER = "528123997852"

class SupportResponse(TypedDict):
    text: str
    show_whatsapp: bool
    whatsapp_number: str
    whatsapp_message: str
    blocked: Optional[bool]

SYSTEM_PROMPT = f"""{SECURITY_PROMPT_BLOCK}

Eres el Asistente Virtual de Soporte de Revisar.IA, una plataforma de auditoría fiscal inteligente para empresas mexicanas.

Tu personalidad:
- Profesional pero amigable y accesible
- Paciente y comprensivo con usuarios de todos los niveles técnicos
- Proactivo en ofrecer soluciones y alternativas
- Siempre respondes en español de México (usando modismos apropiados como "¿en qué te puedo ayudar?" en lugar de "¿en qué puedo ayudarle?")
- Usas emojis ocasionalmente para hacer la conversación más amena (📊, ✅, 💡, etc.)
- Cuando no sabes algo, lo admites honestamente y ofreces escalar a soporte humano

Tu rol:
- Ayudar a los usuarios a entender y usar la plataforma Revisar.IA
- Resolver dudas sobre funcionalidades, procesos y errores comunes
- Explicar conceptos fiscales relacionados con la plataforma (69-B, materialidad, etc.)
- Guiar en el proceso de onboarding, registro de empresas y proveedores
- Ofrecer escalar a soporte humano cuando sea necesario

Reglas importantes:
1. Si el usuario pregunta sobre temas fuera del ámbito de Revisar.IA, amablemente indica que solo puedes ayudar con temas de la plataforma
2. Nunca inventes funcionalidades que no existen
3. Si detectas frustración del usuario, ofrece la opción de hablar con un agente humano
4. Mantén las respuestas concisas pero completas
5. Usa formato con negritas (**texto**) para resaltar información importante
6. Si es una pregunta técnica compleja, sugiere contactar a soporte@revisar.ia

REGLAS DE ESCALACIÓN A WHATSAPP:
- Cuando el usuario pide hablar con una persona/humano, dice que no le ayudaste, tiene un problema muy complejo, menciona urgencia extrema, está frustrado o pide contacto directo, DEBES incluir el marcador [WHATSAPP_BUTTON] en tu respuesta.
- Palabras clave que activan escalación: humano, persona, alguien, agente, contactar, teléfono, llamar, whatsapp, no sirve, frustrado, urgente, hablar con alguien, no entiendes, no me ayudas
- Cuando incluyas [WHATSAPP_BUTTON], hazlo en un mensaje empático como:
  "Entiendo que necesitas atención personalizada. 👤

  Te conecto con nuestro equipo de soporte humano por WhatsApp:

  [WHATSAPP_BUTTON]

  Un asesor te atenderá lo antes posible."

Base de conocimiento de referencia:
{SOPORTE_KNOWLEDGE_BASE}
"""

FALLBACK_RESPONSES = {
    "saludo": "¡Hola! 👋 Soy el asistente virtual de Revisar.IA. Estoy aquí para ayudarte con cualquier duda sobre nuestra plataforma de auditoría fiscal. ¿En qué te puedo ayudar hoy?",
    "despedida": "¡Fue un gusto ayudarte! 🙌 Si tienes más preguntas, no dudes en escribirme. ¡Que tengas excelente día!",
    "gracias": "¡De nada! 😊 Estoy aquí para lo que necesites. ¿Hay algo más en lo que te pueda ayudar?",
    "error": "Disculpa, estoy teniendo dificultades técnicas en este momento. 😅 Por favor intenta de nuevo en unos minutos o contacta a nuestro equipo de soporte en **soporte@revisar.ia**",
    "no_entiendo": "Mmm, no estoy seguro de entender tu pregunta. 🤔 ¿Podrías reformularla? También puedo ayudarte con:\n\n• Cómo usar la plataforma\n• Registro de empresas y proveedores\n• Entender los análisis fiscales\n• Resolver problemas técnicos\n\n¿Cuál te interesa?",
    "default": "Gracias por tu mensaje. Actualmente estoy procesando tu consulta. Si necesitas ayuda inmediata, puedes contactar a nuestro equipo en **soporte@revisar.ia** o llamar en horario de oficina.",
    "whatsapp_escalation": """Entiendo que necesitas atención personalizada. 👤

Te conecto con nuestro equipo de soporte humano por WhatsApp:

[WHATSAPP_BUTTON]

Un asesor te atenderá lo antes posible.""",
}

HUMAN_KEYWORDS = [
    "humano", "persona", "alguien", "agente", "contactar", "teléfono", "telefono",
    "llamar", "whatsapp", "no sirve", "frustrado", "urgente", "hablar con alguien",
    "no entiendes", "no me ayudas", "no funciona", "no me sirve", "asesor",
    "representante", "ejecutivo", "soporte humano", "atención personal", "ayuda real"
]


def detect_wants_human(message: str) -> bool:
    """Detect if user wants to talk to a human agent."""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in HUMAN_KEYWORDS)


def build_whatsapp_message(last_message: str, context: Optional[str] = None) -> str:
    """Build URL-encoded message for WhatsApp."""
    base_message = f"Hola, necesito ayuda con Revisar.IA."
    if last_message:
        base_message += f"\n\nMi consulta: {last_message[:200]}"
    if context:
        base_message += f"\n\nContexto: {context[:100]}"
    return urllib.parse.quote(base_message)


def get_fallback_response(user_message: str) -> SupportResponse:
    """Get a fallback response when AI is not available."""
    message_lower = user_message.lower()
    
    wants_human = detect_wants_human(user_message)
    
    if wants_human:
        return {
            "text": FALLBACK_RESPONSES["whatsapp_escalation"],
            "show_whatsapp": True,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": build_whatsapp_message(user_message),
            "blocked": None
        }
    
    greetings = ["hola", "buenos días", "buenas tardes", "buenas noches", "hey", "hi", "qué onda"]
    if any(g in message_lower for g in greetings):
        return {
            "text": FALLBACK_RESPONSES["saludo"],
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    farewells = ["adiós", "bye", "hasta luego", "chao", "nos vemos"]
    if any(f in message_lower for f in farewells):
        return {
            "text": FALLBACK_RESPONSES["despedida"],
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    thanks = ["gracias", "muchas gracias", "te agradezco", "thanks"]
    if any(t in message_lower for t in thanks):
        return {
            "text": FALLBACK_RESPONSES["gracias"],
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    if "qué es revisar" in message_lower or "para qué sirve" in message_lower:
        return {
            "text": """**Revisar.IA** es una plataforma de auditoría fiscal inteligente 🔍

Te ayuda a:
• ✅ Validar operaciones con proveedores antes de una auditoría del SAT
• 📊 Detectar riesgos fiscales relacionados con el Artículo 69-B
• 📁 Generar expedientes de defensa sólidos
• 🤖 Automatizar el análisis de contratos y facturas

¿Te gustaría saber más sobre alguna funcionalidad específica?""",
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    if "69-b" in message_lower or "69b" in message_lower or "efos" in message_lower:
        return {
            "text": """El **Artículo 69-B del CFF** permite al SAT detectar empresas que facturan operaciones simuladas (conocidas como EFOS).

Revisar.IA te ayuda a:
• 🔍 Verificar si tus proveedores están en listas 69-B
• 📋 Documentar la sustancia de tus operaciones
• ✅ Preparar evidencias que demuestren materialidad

¿Quieres saber cómo verificar un proveedor específico?""",
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    if "contacto" in message_lower or "soporte" in message_lower or "ayuda" in message_lower:
        return {
            "text": """📞 **Información de Contacto**

• **Soporte técnico:** soporte@revisar.ia
• **Ventas y demos:** ventas@revisar.ia
• **Horario:** Lunes a Viernes, 9:00 - 18:00 (CDMX)

¿Prefieres que escale tu consulta a un agente humano? También puedes contactarnos directamente por WhatsApp:

[WHATSAPP_BUTTON]""",
            "show_whatsapp": True,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": build_whatsapp_message(user_message),
            "blocked": None
        }
    
    if "como" in message_lower or "cómo" in message_lower:
        return {
            "text": """Claro, te puedo ayudar. ¿Sobre qué proceso necesitas información?

1️⃣ **Registrar tu empresa** - Configuración inicial
2️⃣ **Agregar proveedores** - Cargar datos y documentos
3️⃣ **Crear proyecto** - Iniciar análisis fiscal
4️⃣ **Ver resultados** - Interpretar scores y reportes

Solo dime el número o escribe tu pregunta específica. 😊""",
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": None
        }
    
    return {
        "text": FALLBACK_RESPONSES["default"],
        "show_whatsapp": False,
        "whatsapp_number": WHATSAPP_NUMBER,
        "whatsapp_message": "",
        "blocked": None
    }


async def get_support_response(
    user_message: str,
    conversation_history: Optional[List[Dict]] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> SupportResponse:
    """
    Get a response from the support agent using Anthropic Claude.
    Falls back to simulated responses if API is not available.
    Includes security layer to block prompt injection attempts.
    
    Args:
        user_message: The user's message
        conversation_history: List of previous messages in the conversation
        user_name: Optional user name for personalization
        user_email: Optional user email for context
        session_id: Optional session ID for logging
        user_id: Optional user ID for logging
        
    Returns:
        SupportResponse dict with text, show_whatsapp, whatsapp_number, whatsapp_message, blocked
    """
    # ========== SECURITY LAYER ==========
    security_check = check_message_security(user_message)
    
    if not security_check.is_safe:
        # Log security event
        if security_check.should_log:
            log_security_event(
                session_id=session_id or "unknown",
                user_id=user_id,
                message=user_message,
                threat_type=security_check.threat_type or "unknown",
                confidence=security_check.confidence
            )
        
        # Return safe response WITHOUT calling the LLM
        return {
            "text": security_check.safe_response or "Soy el asistente de Revisar.IA. ¿En qué puedo ayudarte?",
            "show_whatsapp": False,
            "whatsapp_number": WHATSAPP_NUMBER,
            "whatsapp_message": "",
            "blocked": True
        }
    
    # Sanitize message before sending to LLM
    sanitized_message = sanitize_message(user_message)
    
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API Key not configured, using fallback responses")
        response = get_fallback_response(sanitized_message)
        response["blocked"] = False
        return response

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        messages.append({
            "role": "user",
            "content": sanitized_message
        })

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            messages=messages
        )

        if response.choices and len(response.choices) > 0:
            response_text = response.choices[0].message.content
            
            # Sanitize response to ensure no sensitive info leaked
            response_text = sanitize_response(response_text)
            
            show_whatsapp = "[WHATSAPP_BUTTON]" in response_text or detect_wants_human(sanitized_message)
            
            context = None
            if user_name:
                context = f"Usuario: {user_name}"
            if user_email:
                context = f"{context}, Email: {user_email}" if context else f"Email: {user_email}"
            
            return {
                "text": response_text,
                "show_whatsapp": show_whatsapp,
                "whatsapp_number": WHATSAPP_NUMBER,
                "whatsapp_message": build_whatsapp_message(sanitized_message, context) if show_whatsapp else "",
                "blocked": False
            }
        else:
            logger.warning("Empty response from OpenAI")
            fallback = get_fallback_response(sanitized_message)
            fallback["blocked"] = False
            return fallback
            
    except ImportError:
        logger.error("openai package not installed")
        fallback = get_fallback_response(sanitized_message)
        fallback["blocked"] = False
        return fallback
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        fallback = get_fallback_response(sanitized_message)
        fallback["blocked"] = False
        return fallback
