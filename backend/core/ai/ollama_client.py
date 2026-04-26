"""
OllamaClient (backward-compat shim)
====================================
backend/core/ai/ollama_client.py

The project has migrated from a local Ollama server to the Groq cloud API.
This module is kept so existing imports such as

    from core.ai.ollama_client import OllamaClient

continue to work without changes.  The class is now a thin alias of
:class:`core.ai.groq_client.GroqClient`, so every call site automatically
uses Groq.

If you are writing new code, please import :class:`GroqClient` directly:

    from core.ai.groq_client import GroqClient
"""

from .groq_client import GroqClient


class OllamaClient(GroqClient):
    """Deprecated alias.  Use :class:`GroqClient` instead.

    Retained for backward compatibility — all behaviour and method
    signatures are inherited from :class:`GroqClient`.  Any legacy Ollama
    model name passed in (``qwen2.5:7b``, ``phi3:mini``, ``phi3:latest``,
    ...) is automatically translated to a Groq model.
    """

    # Kept for compatibility with old code that still reads these attrs.
    DEFAULT_MODEL = None  # resolved by GroqClient at runtime
    BASE_URL = None       # not applicable for cloud client


__all__ = ['OllamaClient']
