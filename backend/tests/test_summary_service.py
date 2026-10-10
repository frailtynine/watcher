from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.summary_service import SummaryService
from app.models.news_item import NewsItem
from app.models.source import SourceType


@pytest.mark.parametrize(
    "url,source_type,expected",
    [
        (None, SourceType.RSS, False),
        ("", SourceType.RSS, False),
        ("https://example.com/news", None, False),
        ("https://example.com/news", SourceType.TELEGRAM, False),
        ("https://example.com/news", SourceType.RSS, True),
    ],
)
def test_should_fetch_article_for_news_item(url, source_type, expected):
    service = SummaryService()
    news_item = MagicMock(spec=NewsItem)
    news_item.url = url

    if source_type is None:
        news_item.source = None
    else:
        source = MagicMock()
        source.type = source_type
        news_item.source = source

    assert service.should_fetch_article_for_news_item(news_item) is expected


@pytest.mark.anyio
async def test_summarize_text_uses_openrouter():
    service = SummaryService()

    with patch(
        "app.ai.summary_service.OpenRouterClient.generate_text_response",
        new_callable=AsyncMock,
        return_value="Short summary",
    ) as mock_generate:
        summary = await service.summarize_text(
            title="Article title",
            text="Article body",
            prompt="Summarize briefly",
        )

    assert summary == "Short summary"
    mock_generate.assert_awaited_once_with(
        "Summarize briefly\n\nArticle Title: Article title"
        "\nArticle Text: Article body"
    )
