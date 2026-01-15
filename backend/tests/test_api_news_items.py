import pytest
from datetime import datetime
from httpx import AsyncClient

from app.models import User, Source, NewsItem
from app.models.source import SourceType

pytestmark = pytest.mark.anyio


@pytest.fixture
async def test_source(db_session_maker, test_user: User) -> Source:
    """Create a test source."""
    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            type=SourceType.RSS,
            source="https://example.com/feed",
            active=True,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source


@pytest.fixture
async def test_news_item(db_session_maker, test_source: Source) -> NewsItem:
    """Create a test news item."""
    async with db_session_maker() as session:
        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News Title",
            content="Test news content here.",
            url="https://example.com/news/1",
            published_at=datetime.utcnow(),
            processed=False,
            settings={},
            raw_data={},
        )
        session.add(news_item)
        await session.commit()
        await session.refresh(news_item)
        return news_item


async def test_list_news_items_empty(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing news items when empty."""
    response = await client.get("/api/news-items/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_news_items(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test listing news items."""
    response = await client.get("/api/news-items/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test News Title"


async def test_get_news_item(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test getting a specific news item."""
    response = await client.get(
        f"/api/news-items/{test_news_item.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_news_item.id
    assert data["title"] == "Test News Title"


async def test_get_news_item_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting a non-existent news item."""
    response = await client.get("/api/news-items/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_list_news_items_unauthorized(client: AsyncClient):
    """Test that listing news items requires auth."""
    response = await client.get("/api/news-items/")
    assert response.status_code == 401
