import pytest
from httpx import AsyncClient
from app.models import Source, NewsTask

pytestmark = pytest.mark.anyio


async def test_associate_source_with_task_success(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test associating a source with a task."""
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_id"] == test_source.id
    assert data["news_task_id"] == test_news_task.id


async def test_associate_missing_source_id(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test association fails without source_id."""
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "news_task_id": 1,
        },
    )
    assert response.status_code == 422


async def test_associate_missing_task_id(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test association fails without news_task_id."""
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": 1,
        },
    )
    assert response.status_code == 422


async def test_associate_invalid_source(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test association fails with non-existent source."""
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": 99999,
            "news_task_id": test_news_task.id,
        },
    )
    assert response.status_code == 404


async def test_associate_invalid_task(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test association fails with non-existent task."""
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": 99999,
        },
    )
    assert response.status_code == 404


async def test_associate_duplicate(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test duplicate association fails."""
    # Create first association
    await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )

    # Try to create duplicate
    response = await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )
    assert response.status_code == 400


async def test_associate_unauthorized(
    client: AsyncClient,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test association requires authentication."""
    response = await client.post(
        "/api/associations/",
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )
    assert response.status_code == 401


async def test_list_tasks_for_source(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test listing tasks for a source."""
    # Create association
    await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )

    # List tasks for source
    response = await client.get(
        f"/api/associations/source/{test_source.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["news_task_id"] == test_news_task.id


async def test_list_tasks_for_invalid_source(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing tasks for non-existent source returns 404."""
    response = await client.get(
        "/api/associations/source/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_list_sources_for_task(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test listing sources for a task."""
    # Create association
    await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )

    # List sources for task
    response = await client.get(
        f"/api/associations/task/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_id"] == test_source.id


async def test_list_sources_for_invalid_task(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test listing sources for non-existent task returns 404."""
    response = await client.get(
        "/api/associations/task/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_disassociate_source_from_task(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
    test_news_task: NewsTask,
):
    """Test removing association between source and task."""
    # Create association
    await client.post(
        "/api/associations/",
        headers=auth_headers,
        json={
            "source_id": test_source.id,
            "news_task_id": test_news_task.id,
        },
    )

    # Remove association
    response = await client.delete(
        f"/api/associations/{test_source.id}/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/associations/source/{test_source.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_disassociate_invalid_source(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test disassociating non-existent source returns 404."""
    response = await client.delete(
        f"/api/associations/99999/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_disassociate_invalid_task(
    client: AsyncClient,
    auth_headers: dict,
    test_source: Source,
):
    """Test disassociating non-existent task returns 404."""
    response = await client.delete(
        f"/api/associations/{test_source.id}/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
