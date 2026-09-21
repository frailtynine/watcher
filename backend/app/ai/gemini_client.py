"""Gemini API client for news processing."""
import logging

import google.genai as genai
from google.genai import types

from app.ai.base import BaseAIClient


logger = logging.getLogger(__name__)


class GeminiClient(BaseAIClient):
    """Client for interacting with Gemini API."""

    MODEL_NAME = "gemini-3.1-flash-lite"

    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize Gemini client with API key.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    async def generate_text_response(self, prompt: str) -> str:
        """Generate a text response from Gemini API.

        Args:
            prompt: The prompt to send to the Gemini API.
        """
        response = self.client.interactions.create(
            model=self.model_name,
            input=prompt,
        )
        return response.output_text

    async def _generate(
        self, system_instruction: str, user_message: str
    ) -> tuple[str, int]:
        """Call Gemini API and return (response_text, tokens_used)."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "boolean"},
                        "thinking": {"type": "string"}
                    },
                    "required": ["result", "thinking"]
                }
            )
        )
        return response.text, self._count_tokens(response)

    def _count_tokens(self, response) -> int:
        """Count tokens used in the response."""
        usage_metadata = response.usage_metadata
        if not usage_metadata:
            return 0
        return (
            usage_metadata.prompt_token_count +
            usage_metadata.candidates_token_count
        )
