"""OpenRouter client for news processing and model discovery."""

import logging
from typing import Any

import httpx
from openrouter import OpenRouter

from app.ai.base import BaseAIClient
from app.core.config import settings


logger = logging.getLogger(__name__)


class OpenRouterClient(BaseAIClient):
    """Client for OpenRouter's chat and model APIs."""

    MODEL_NAME = "anthropic/claude-haiku-5.5"
    JEV_MODEL_NAME = "typesafe/jev-1.13"
    JEV_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"

    def __init__(
        self,
        api_key: str = settings.OPEN_ROUTER_API_KEY,
        model_name: str = MODEL_NAME,
    ):
        super().__init__(model_name)
        self.api_key = api_key
        self.client = OpenRouter(api_key=api_key)

    async def list_models(
        self,
        *,
        limit: int = 500,
        output_modalities: str | None = None,
        supported_parameters: str | None = None,
        sort: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return available OpenRouter models and their metadata."""
        response = await self.client.models.list_async(
            limit=limit,
            output_modalities=output_modalities,
            supported_parameters=supported_parameters,
            sort=sort,
        )
        if not response or not response.data:
            return []
        return [model.model_dump() for model in response.data]

    async def generate_text_response(self, prompt: str) -> str:
        """Generate text and log the actual OpenRouter charge in USD."""
        response = await self.client.chat.send_async(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise ValueError("OpenRouter returned no chat completion choices.")

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenRouter returned an empty chat completion.")

        usage = response.usage
        logger.info(
            "OpenRouter generation model=%s cost_usd=%s",
            response.model or self.model_name,
            getattr(usage, "cost", None),
        )
        return content

    async def is_news_relevant(
        self,
        title: str,
        content: str,
        prompt: str,
        threshold: float = 0.7,
    ) -> bool:
        """Classify a news item against criteria with the Jev model."""
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1.")

        payload = {
            "model": self.JEV_MODEL_NAME,
            "state": {
                "criteria": prompt,
                "news_item": {"title": title, "content": content},
            },
            "questions": {
                "relevant": {
                    "type": "noul",
                    "instructions": (
                        "The news item in `news_item` matches the "
                        "relevancy criteria in `criteria`."
                    ),
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                self.JEV_DECISIONS_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        try:
            probability = response.json()["answers"]["relevant"]["noul"]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Jev returned an invalid decision response."
            ) from exc

        if not isinstance(probability, (int, float)) or not (
            0 <= probability <= 1
        ):
            raise ValueError("Jev returned an invalid relevance probability.")
        return probability >= threshold

    async def _generate(
        self,
        system_instruction: str,
        user_message: str,
    ) -> tuple[str, int]:
        response = await self.client.chat.send_async(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
        if not response.choices:
            raise ValueError("OpenRouter returned no chat completion choices.")

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenRouter returned an empty chat completion.")

        usage = response.usage
        tokens_used = 0
        if usage:
            tokens_used = (usage.prompt_tokens or 0) + (
                usage.completion_tokens or 0
            )
        return content, tokens_used
