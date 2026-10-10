from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.openrouter_client import OpenRouterClient


pytestmark = pytest.mark.anyio


@pytest.fixture
def openrouter_client():
    return OpenRouterClient(api_key="test-api-key")


async def test_list_models(openrouter_client):
    model = SimpleNamespace(model_dump=lambda: {"id": "openai/gpt-4o"})
    openrouter_client.client.models.list_async = AsyncMock(
        return_value=SimpleNamespace(data=[model])
    )

    models = await openrouter_client.list_models(limit=10, sort="newest")

    assert models == [{"id": "openai/gpt-4o"}]
    openrouter_client.client.models.list_async.assert_awaited_once_with(
        limit=10,
        output_modalities=None,
        supported_parameters=None,
        sort="newest",
    )


async def test_generate(openrouter_client):
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"result": true, "thinking": "Relevant"}'
                )
            )
        ],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
    )
    openrouter_client.client.chat.send_async = AsyncMock(
        return_value=response
    )

    response_text, tokens_used = await openrouter_client._generate(
        "System instruction",
        "User message",
    )

    assert response_text == '{"result": true, "thinking": "Relevant"}'
    assert tokens_used == 20


async def test_generate_text_response(openrouter_client):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Summary"))],
        model="openai/gpt-4o-mini",
        usage=SimpleNamespace(cost=0.00012),
    )
    openrouter_client.client.chat.send_async = AsyncMock(
        return_value=response
    )

    summary = await openrouter_client.generate_text_response("Article text")

    assert summary == "Summary"


async def test_is_news_relevant(openrouter_client):
    response = SimpleNamespace(
        json=lambda: {"answers": {"relevant": {"noul": 0.91}}},
        raise_for_status=lambda: None,
    )
    http_client = AsyncMock()
    http_client.post.return_value = response
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = http_client

    with patch(
        "app.ai.openrouter_client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        relevant = await openrouter_client.is_news_relevant(
            title="New Tube strike announced",
            content="London Underground staff will strike next week.",
            prompt="News about London transport disruptions.",
            threshold=0.9,
        )

    assert relevant is True
    http_client.post.assert_awaited_once()
