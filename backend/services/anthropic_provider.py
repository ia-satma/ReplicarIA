"""
Anthropic Provider - Claude API for document analysis and AI services
"""
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

_anthropic_client = None
_initialized = False
ANTHROPIC_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("anthropic package not available")

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _get_client():
    """Lazy initialization of Anthropic client"""
    global _anthropic_client, _initialized

    if _initialized:
        return _anthropic_client

    _initialized = True
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')

    if ANTHROPIC_AVAILABLE and api_key:
        try:
            _anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            _anthropic_client = None
    else:
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not configured")
        _anthropic_client = None

    return _anthropic_client


def chat_completion_sync(
    messages: List[Dict[str, str]],
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """Synchronous chat completion using Claude"""
    client = _get_client()

    if not client:
        logger.warning("Anthropic client not available, returning error")
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

        response = client.messages.create(**kwargs)

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
    return _get_client() is not None
