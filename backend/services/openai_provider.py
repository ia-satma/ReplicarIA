"""
OpenAI Provider - Centralized OpenAI client for all AI services
Replaces Anthropic/Claude with OpenAI GPT-4o
"""
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# OpenAI client setup - LAZY INITIALIZATION
_openai_client = None
_initialized = False
OPENAI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("openai package not available")


def _get_client():
    """Lazy initialization of OpenAI client"""
    global _openai_client, _initialized

    if _initialized:
        return _openai_client

    _initialized = True
    api_key = os.environ.get('OPENAI_API_KEY', '')

    if OPENAI_AVAILABLE and api_key:
        try:
            _openai_client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            _openai_client = None
    else:
        if not api_key:
            logger.warning("OPENAI_API_KEY not configured - AI features will be limited")
        _openai_client = None

    return _openai_client


def get_client():
    """Public interface to get the OpenAI client"""
    return _get_client()


# Legacy compatibility - module-level client for backward compatibility
# Services should use is_configured() and chat_completion_sync() instead
class _LazyClient:
    """Lazy client wrapper for backward compatibility"""

    def __getattr__(self, name):
        client = _get_client()
        if client is None:
            raise RuntimeError("OpenAI client not configured. Set OPENAI_API_KEY environment variable.")
        return getattr(client, name)

    def __bool__(self):
        """Allow `if openai_client:` checks to work properly"""
        return _get_client() is not None


# This allows old code like `openai_client.chat.completions.create(...)` to work
openai_client = _LazyClient()

# Default model configuration
DEFAULT_MODEL = "gpt-4o"
FAST_MODEL = "gpt-4o-mini"


async def chat_completion(
    messages: List[Dict[str, str]],
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """
    Send a chat completion request to OpenAI.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system_message: Optional system message to prepend
        model: OpenAI model to use (default: gpt-4o)
        max_tokens: Maximum tokens in response
        temperature: Creativity level (0-2)

    Returns:
        str: The assistant's response text
    """
    client = _get_client()
    if not client:
        logger.warning("OpenAI client not available - returning error")
        return '{"error": "OpenAI not configured"}'

    try:
        # Build messages list
        all_messages = []
        if system_message:
            all_messages.append({"role": "system", "content": system_message})
        all_messages.extend(messages)

        response = client.chat.completions.create(
            model=model,
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f'{{"error": "{str(e)[:100]}"}}'


def chat_completion_sync(
    messages: List[Dict[str, str]],
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """
    Synchronous version of chat_completion for non-async contexts.
    """
    client = _get_client()
    if not client:
        logger.warning("OpenAI client not available - returning error")
        return '{"error": "OpenAI not configured"}'

    try:
        all_messages = []
        if system_message:
            all_messages.append({"role": "system", "content": system_message})
        all_messages.extend(messages)

        response = client.chat.completions.create(
            model=model,
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f'{{"error": "{str(e)[:100]}"}}'


def is_configured() -> bool:
    """Check if OpenAI is properly configured"""
    return _get_client() is not None


# Compatibility layer for code that used Anthropic patterns
class OpenAIChat:
    """
    Compatibility class that mimics the LlmChat interface but uses OpenAI.
    """
    def __init__(self, api_key: str = "", session_id: str = "", system_message: str = ""):
        self.system_message = system_message
        self.model = DEFAULT_MODEL

    def with_model(self, provider: str, model: str):
        """Set the model - maps Claude models to GPT equivalents"""
        # Map Claude models to OpenAI equivalents
        model_mapping = {
            "claude-3-opus": "gpt-4o",
            "claude-3-sonnet": "gpt-4o",
            "claude-sonnet-4-5": "gpt-4o",
            "claude-3-haiku": "gpt-4o-mini",
            "claude-3.5-sonnet": "gpt-4o",
        }

        model_lower = (model or "").lower()
        for claude_model, gpt_model in model_mapping.items():
            if claude_model in model_lower:
                self.model = gpt_model
                break
        else:
            # If no mapping found, use default
            self.model = DEFAULT_MODEL

        return self

    async def send_message(self, message) -> str:
        """Send a message and get a response"""
        # Handle both string and UserMessage objects
        text = message.text if hasattr(message, 'text') else str(message)

        return await chat_completion(
            messages=[{"role": "user", "content": text}],
            system_message=self.system_message,
            model=self.model
        )


# Export for compatibility
LlmChat = OpenAIChat


class UserMessage:
    """Simple message wrapper for compatibility"""
    def __init__(self, text: str):
        self.text = text
