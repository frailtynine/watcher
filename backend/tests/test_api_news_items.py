import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models import Source, NewsItem

pytestmark = pytest.mark.anyio


@pytest.fixture
async def test_news_item(db_session_maker, test_source: Source) -> NewsItem:
    """Create a test news item."""
    async with db_session_maker() as session:
        news_item = NewsItem(
            source_id=test_source.id,
            title="Test News Title",
            content="Test news content here.",
            url="https://example.com/news/1",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
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


async def test_create_news_item_success(
    client: AsyncClient,
    auth_headers: dict,
    test_source: "Source",
):
    """Test creating a news item with valid data."""
    response = await client.post(
        "/api/news-items/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "title": "New Article",
            "content": "Article content here",
            "url": "https://example.com/article",
            "published_at": "2024-01-01T12:00:00",
            "settings": {},
            "raw_data": {},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Article"
    assert "id" in data


async def test_create_news_item_missing_title(
    client: AsyncClient,
    auth_headers: dict,
    test_source: "Source",
):
    """Test creating news item fails without title."""
    response = await client.post(
        "/api/news-items/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "content": "Content",
            "published_at": "2024-01-01T12:00:00",
        },
    )
    assert response.status_code == 422


async def test_create_news_item_empty_title(
    client: AsyncClient,
    auth_headers: dict,
    test_source: "Source",
):
    """Test creating news item fails with empty title."""
    response = await client.post(
        "/api/news-items/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "title": "",
            "content": "Content",
            "published_at": "2024-01-01T12:00:00",
        },
    )
    assert response.status_code == 422


async def test_create_news_item_missing_content(
    client: AsyncClient,
    auth_headers: dict,
    test_source: "Source",
):
    """Test creating news item fails without content."""
    response = await client.post(
        "/api/news-items/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "title": "Title",
            "published_at": "2024-01-01T12:00:00",
        },
    )
    assert response.status_code == 422


async def test_create_news_item_invalid_source(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test creating news item with non-existent source fails."""
    response = await client.post(
        "/api/news-items/",
        headers=auth_headers,
        json={
            "source_id": 99999,
            "title": "Title",
            "content": "Content",
            "published_at": "2024-01-01T12:00:00",
        },
    )
    assert response.status_code == 404


async def test_create_news_item_unauthorized(
    client: AsyncClient,
    test_source: "Source",
):
    """Test creating news item requires authentication."""
    response = await client.post(
        "/api/news-items/",
        json={
            "source_id": test_source.id,
            "title": "Title",
            "content": "Content",
            "published_at": "2024-01-01T12:00:00",
        },
    )
    assert response.status_code == 401


async def test_list_news_items_with_filters(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test listing news items with filters."""
    response = await client.get(
        f"/api/news-items/?source_id={test_news_item.source_id}&processed=false", # noqa
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


async def test_list_news_items_invalid_source_filter(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing with invalid source_id filter returns 404."""
    response = await client.get(
        "/api/news-items/?source_id=99999",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_update_news_item(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test updating a news item."""
    response = await client.patch(
        f"/api/news-items/{test_news_item.id}",
        headers=auth_headers,
        json={
            "processed": True,
            "result": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is True
    assert data["result"] is True


async def test_update_news_item_invalid_title(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test updating news item with empty title fails."""
    response = await client.patch(
        f"/api/news-items/{test_news_item.id}",
        headers=auth_headers,
        json={"title": ""},
    )
    assert response.status_code == 422


async def test_update_news_item_not_found(
    client: AsyncClient,
    auth_headers: dict
):
    """Test updating non-existent news item returns 404."""
    response = await client.patch(
        "/api/news-items/99999",
        headers=auth_headers,
        json={"processed": True},
    )
    assert response.status_code == 404


async def test_delete_news_item(
    client: AsyncClient,
    auth_headers: dict,
    test_news_item: NewsItem,
):
    """Test deleting a news item."""
    response = await client.delete(
        f"/api/news-items/{test_news_item.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/news-items/{test_news_item.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_news_item_not_found(
    client: AsyncClient,
    auth_headers: dict
):
    """Test deleting non-existent news item returns 404."""
    response = await client.delete(
        "/api/news-items/99999",
        headers=auth_headers
    )
    assert response.status_code == 404
