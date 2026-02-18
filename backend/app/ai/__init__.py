"""AI module for news processing."""

from app.ai.gemini_client import GeminiClient
from app.ai.consumer import AIConsumer

__all__ = ["GeminiClient", "AIConsumer"]
