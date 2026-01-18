import pytest
from httpx import AsyncClient
from app.models import User, NewsTask

pytestmark = pytest.mark.anyio


async def test_create_news_task_success(client: AsyncClient, auth_headers: dict):
    """Test creating a news task with valid data."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "AI News Summary",
            "prompt": "Summarize the latest AI developments",
            "active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AI News Summary"
    assert data["prompt"] == "Summarize the latest AI developments"
    assert "id" in data


async def test_create_news_task_missing_name(client: AsyncClient, auth_headers: dict):
    """Test creating task fails without name."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "prompt": "Some prompt",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_empty_name(client: AsyncClient, auth_headers: dict):
    """Test creating task fails with empty name."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "",
            "prompt": "Some prompt",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_missing_prompt(client: AsyncClient, auth_headers: dict):
    """Test creating task fails without prompt."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "Task Name",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_empty_prompt(client: AsyncClient, auth_headers: dict):
    """Test creating task fails with empty prompt."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "Task Name",
            "prompt": "",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_unauthorized(client: AsyncClient):
    """Test creating task requires authentication."""
    response = await client.post(
        "/api/news-tasks/",
        json={
            "name": "Task Name",
            "prompt": "Some prompt",
        },
    )
    assert response.status_code == 401


async def test_list_news_tasks_empty(client: AsyncClient, auth_headers: dict):
    """Test listing tasks when empty."""
    response = await client.get("/api/news-tasks/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_news_tasks(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test listing tasks."""
    response = await client.get("/api/news-tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Task"


async def test_list_news_tasks_unauthorized(client: AsyncClient):
    """Test listing tasks requires authentication."""
    response = await client.get("/api/news-tasks/")
    assert response.status_code == 401


async def test_get_news_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test getting a specific task."""
    response = await client.get(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_news_task.id
    assert data["name"] == "Test Task"


async def test_get_news_task_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent task returns 404."""
    response = await client.get("/api/news-tasks/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_get_news_task_unauthorized(client: AsyncClient, test_news_task: NewsTask):
    """Test getting task requires authentication."""
    response = await client.get(f"/api/news-tasks/{test_news_task.id}")
    assert response.status_code == 401


# @pytest.mark.skip(reason="FastCRUD passes timezone-aware datetime for onupdate fields with TIMESTAMP WITHOUT TIME ZONE")
async def test_update_news_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test updating a task."""
    response = await client.patch(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
        json={
            "name": "Updated Task",
            "active": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Task"
    assert data["active"] is False


async def test_update_news_task_invalid_name(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test updating task with empty name fails."""
    response = await client.patch(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
        json={"name": ""},
    )
    assert response.status_code == 422


async def test_update_news_task_invalid_prompt(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test updating task with empty prompt fails."""
    response = await client.patch(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
        json={"prompt": ""},
    )
    assert response.status_code == 422


async def test_update_news_task_not_found(client: AsyncClient, auth_headers: dict):
    """Test updating non-existent task returns 404."""
    response = await client.patch(
        "/api/news-tasks/99999",
        headers=auth_headers,
        json={"name": "Updated Name"},
    )
    assert response.status_code == 404


async def test_delete_news_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test deleting a task."""
    response = await client.delete(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/news-tasks/{test_news_task.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_delete_news_task_not_found(client: AsyncClient, auth_headers: dict):
    """Test deleting non-existent task returns 404."""
    response = await client.delete("/api/news-tasks/99999", headers=auth_headers)
    assert response.status_code == 404
