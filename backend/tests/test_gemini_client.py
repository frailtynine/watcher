"""Tests for Gemini client."""

import pytest
from unittest.mock import patch
from dataclasses import dataclass

from app.ai.gemini_client import GeminiClient, ProcessingResult


@dataclass
class MockUsageMetadata:
    """Mock usage metadata from Gemini response."""
    prompt_token_count: int = 100
    candidates_token_count: int = 50


@dataclass
class MockResponse:
    """Mock Gemini API response."""
    usage_metadata: MockUsageMetadata = None
    text: str = '{"result": true, "thinking": "This news matches the criteria"}'


@pytest.fixture
def gemini_client():
    """Create a Gemini client with test API key."""
    return GeminiClient(api_key="test-api-key")


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini response."""
    return MockResponse(usage_metadata=MockUsageMetadata())


@pytest.mark.asyncio
async def test_gemini_client_initialization():
    """Test Gemini client initializes correctly."""
    client = GeminiClient(api_key="test-key-123")
    assert client.api_key == "test-key-123"
    assert client.MODEL_NAME == "gemini-2.5-flash-lite"


@pytest.mark.asyncio
async def test_process_news_success(gemini_client, mock_gemini_response):
    """Test successful news processing."""
    with patch.object(
        gemini_client.client.models,
        'generate_content',
        return_value=mock_gemini_response
    ):
        result = await gemini_client.process_news(
            title="Test Article",
            content="This is test content",
            prompt="Find articles about technology"
        )

    assert isinstance(result, ProcessingResult)
    assert result.result is True
    assert result.thinking == "This news matches the criteria"
    assert result.tokens_used == 150  # 100 + 50


@pytest.mark.asyncio
async def test_process_news_negative_result(gemini_client):
    """Test news processing with negative result."""
    negative_response = MockResponse(
        usage_metadata=MockUsageMetadata(
            prompt_token_count=80,
            candidates_token_count=30
        ),
        text='{"result": false, "thinking": "Does not match criteria"}'
    )

    with patch.object(
        gemini_client.client.models,
        'generate_content',
        return_value=negative_response
    ):
        result = await gemini_client.process_news(
            title="Unrelated Article",
            content="Content about cooking",
            prompt="Find articles about technology"
        )

    assert result.result is False
    assert result.thinking == "Does not match criteria"
    assert result.tokens_used == 110


@pytest.mark.asyncio
async def test_build_system_instruction(gemini_client):
    """Test system instruction building."""
    prompt = "Find news about AI and machine learning"
    instruction = gemini_client._build_system_instruction(prompt)

    assert "news monitoring assistant" in instruction
    assert prompt in instruction
    assert "result" in instruction
    assert "thinking" in instruction


@pytest.mark.asyncio
async def test_build_user_message(gemini_client):
    """Test user message building."""
    title = "AI Breakthrough"
    content = "Scientists achieve new milestone"
    message = gemini_client._build_user_message(title, content)

    assert "Title:" in message
    assert title in message
    assert "Content:" in message
    assert content in message


@pytest.mark.asyncio
async def test_count_tokens_with_metadata(gemini_client):
    """Test token counting with valid metadata."""
    response = MockResponse(
        usage_metadata=MockUsageMetadata(
            prompt_token_count=200,
            candidates_token_count=100
        )
    )
    tokens = gemini_client._count_tokens(response)
    assert tokens == 300


@pytest.mark.asyncio
async def test_count_tokens_without_metadata(gemini_client):
    """Test token counting without metadata."""
    response = MockResponse(usage_metadata=None)
    tokens = gemini_client._count_tokens(response)
    assert tokens == 0


@pytest.mark.asyncio
async def test_process_news_with_api_error(gemini_client):
    """Test handling of API errors."""
    with patch.object(
        gemini_client.client.models,
        'generate_content',
        side_effect=Exception("API Error")
    ):
        with pytest.raises(Exception, match="API Error"):
            await gemini_client.process_news(
                title="Test",
                content="Content",
                prompt="Prompt"
            )


@pytest.mark.asyncio
async def test_process_news_with_missing_fields(gemini_client):
    """Test processing with missing response fields."""
    incomplete_response = MockResponse(
        usage_metadata=MockUsageMetadata(),
        text='{"result": true}'
    )

    with patch.object(
        gemini_client.client.models,
        'generate_content',
        return_value=incomplete_response
    ):
        result = await gemini_client.process_news(
            title="Test",
            content="Content",
            prompt="Prompt"
        )

    assert result.result is True
    assert result.thinking == ""  # Default for missing field
