from unittest.mock import MagicMock

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
