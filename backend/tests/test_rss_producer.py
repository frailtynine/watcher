"""Tests for RSS producer."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock

from app.producers.rss import RSSProducer
from app.models.source import Source, SourceType


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.execute = MagicMock()
    return session


@pytest.fixture
def rss_source():
    """Create a test RSS source."""
    source = Source(
        id=uuid4(),
        user_id=uuid4(),
        name="Test RSS Feed",
        type=SourceType.RSS,
        source="https://example.com/feed.xml",
        active=True,
    )
    return source


@pytest.fixture
def mock_feed_data():
    """Mock RSS feed data."""
    return {
        "bozo": False,
        "entries": [
            {
                "title": "Test Article 1",
                "link": "https://example.com/article1",
                "description": "This is a test article description",
                "published": "Mon, 15 Jan 2024 10:00:00 GMT",
                "id": "article1",
            },
            {
                "title": "Test Article 2",
                "link": "https://example.com/article2",
                "description": "Description of article 2",
                "published": "Mon, 15 Jan 2024 11:00:00 GMT",
                "id": "article2",
            },
            {
                "title": "Article without description",
                "link": "https://example.com/article3",
            },
            {
                "link": "https://example.com/article4",
                "description": "Description without title",
            },
            {
                "title": "Article without link",
                "description": "Description without link",
            },
        ],
    }


@pytest.mark.asyncio
async def test_rss_producer_fetch_success(
    mock_session, rss_source, mock_feed_data
):
    """Test successful RSS feed fetching."""
    producer = RSSProducer()

    with patch("feedparser.parse", return_value=mock_feed_data):
        items = await producer.fetch(rss_source)

    # Should get 2 items (3 others missing required fields)
    assert len(items) == 2

    # Check first item
    assert items[0].title == "Test Article 1"
    assert items[0].content == "This is a test article description"
    assert items[0].url == "https://example.com/article1"
    assert items[0].external_id == "article1"
    assert items[0].source_id == rss_source.id

    # Check raw_data structure (minimal fields)
    assert "title" in items[0].raw_data
    assert "link" in items[0].raw_data
    assert "description" in items[0].raw_data
    assert "published" in items[0].raw_data

    # Check second item
    assert items[1].title == "Test Article 2"
    assert items[1].content == "Description of article 2"
    assert items[1].url == "https://example.com/article2"


@pytest.mark.asyncio
async def test_rss_producer_handles_bozo_feed(mock_session, rss_source):
    """Test handling of malformed feeds."""
    producer = RSSProducer()

    bozo_feed = {
        "bozo": True,
        "bozo_exception": Exception("Malformed XML"),
        "entries": [
            {
                "title": "Article from bad feed",
                "link": "https://example.com/article",
                "description": "Description here",
            }
        ],
    }

    with patch("feedparser.parse", return_value=bozo_feed):
        items = await producer.fetch(rss_source)

    # Should still process entries despite bozo flag
    assert len(items) == 1
    assert items[0].title == "Article from bad feed"


@pytest.mark.asyncio
async def test_rss_producer_handles_fetch_error(
    mock_session, rss_source
):
    """Test error handling during feed fetching."""
    producer = RSSProducer()

    with patch("feedparser.parse", side_effect=Exception("Network error")):
        items = await producer.fetch(rss_source)

    # Should return empty list on error
    assert len(items) == 0


@pytest.mark.asyncio
async def test_rss_producer_date_parsing(mock_session, rss_source):
    """Test various date format parsing."""
    producer = RSSProducer()

    feed_with_dates = {
        "bozo": False,
        "entries": [
            {
                "title": "Article with published_parsed",
                "description": "Content",
                "link": "https://example.com/1",
                "published_parsed": (2024, 1, 15, 10, 0, 0, 0, 15, 0),
            },
            {
                "title": "Article with published string",
                "description": "Content",
                "link": "https://example.com/2",
                "published": "Mon, 15 Jan 2024 10:00:00 GMT",
            },
        ],
    }

    with patch("feedparser.parse", return_value=feed_with_dates):
        items = await producer.fetch(rss_source)

    assert len(items) == 2
    assert all(isinstance(item.published_at, datetime) for item in items)


@pytest.mark.asyncio
async def test_rss_producer_required_fields(mock_session, rss_source):
    """Test entries missing required fields are skipped."""
    producer = RSSProducer()

    feed = {
        "bozo": False,
        "entries": [
            {
                "title": "Valid entry",
                "link": "https://example.com/1",
                "description": "Valid description",
            },
            {
                "link": "https://example.com/2",
                "description": "Description only",
            },
            {
                "title": "Title only",
                "description": "Description",
            },
            {
                "title": "Title",
                "link": "https://example.com/3",
            },
        ],
    }

    with patch("feedparser.parse", return_value=feed):
        items = await producer.fetch(rss_source)

    # Only the first entry has all required fields
    assert len(items) == 1
    assert items[0].title == "Valid entry"
