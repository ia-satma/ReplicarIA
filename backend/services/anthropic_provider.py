"""
Anthropic Provider - Claude API for document analysis and AI services
"""
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

anthropic_client = None
ANTHROPIC_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic package not available")

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
    try:
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
else:
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not configured")

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def chat_completion_sync(
    messages: List[Dict[str, str]],
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """Synchronous chat completion using Claude"""
    if not anthropic_client:
        logger.warning("Anthropic client not available")
        return '{"error": "Anthropic not configured"}'

    try:
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": formatted_messages
        }

        if system_message:
            kwargs["system"] = system_message

        response = anthropic_client.messages.create(**kwargs)

        if response.content and len(response.content) > 0:
            return response.content[0].text
        return ""

    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return f'{{"error": "{str(e)[:100]}"}}'


async def chat_completion(
    messages: List[Dict[str, str]],
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """Async wrapper for chat completion"""
    return chat_completion_sync(messages, system_message, model, max_tokens, temperature)


def is_configured() -> bool:
    """Check if Anthropic is properly configured"""
    return anthropic_client is not None
