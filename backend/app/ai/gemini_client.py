"""Gemini API client for news processing."""
import logging

import google.genai as genai
from google.genai import types

from app.ai.base import BaseAIClient
from app.schemas.newspaper import NewsItemNewspaperAIResponse
from app.models.newspaper import Newspaper


def _fix_schema_for_gemini(schema: dict) -> dict:
    """Convert tuple prefixItems notation to items — Gemini SDK doesn't support prefixItems."""
    if isinstance(schema, dict):
        if "prefixItems" in schema:
            item_types = schema["prefixItems"]
            schema = {k: v for k, v in schema.items() if k != "prefixItems"}
            schema["items"] = item_types[0] if item_types else {}
        return {k: _fix_schema_for_gemini(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_fix_schema_for_gemini(item) for item in schema]
    return schema

logger = logging.getLogger(__name__)

_AI_TITLE_MAX = 200
_AI_SUMMARY_MAX = 500
_ROW_MAX_ITEMS = 5


class GeminiClient(BaseAIClient):
    """Client for interacting with Gemini API."""

    MODEL_NAME = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        """Initialize Gemini client with API key.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    async def process_newspaper(
        self,
        prompt: str,
    ) -> Newspaper | None:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_fix_schema_for_gemini(
                    NewsItemNewspaperAIResponse.model_json_schema()
                )
            ),
        )
        return response.text

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
