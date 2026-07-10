import pytest
from httpx import AsyncClient
from app.models import NewsTask

pytestmark = pytest.mark.anyio


async def test_create_news_task_success(
    client: AsyncClient, auth_headers: dict
):
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
    assert data["settings"]["delivery"]["telegram"]["summary"] is False
    assert data["settings"]["delivery"]["telegram"]["lang"] == "en"
    assert (
        data["settings"]["delivery"]["telegram"]["prompt"]
        == "Retell the news article in a neutral way in a short form, no more than three sentences"
    )
    assert "id" in data


async def test_create_news_task_with_custom_settings(
    client: AsyncClient, auth_headers: dict
):
    """Test creating a news task with custom delivery settings."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "DE News",
            "prompt": "Summarize fintech updates",
            "active": True,
            "settings": {
                "delivery": {
                    "telegram": {
                        "summary": True,
                        "lang": "de",
                        "prompt": "Retell the article neutrally in two short sentences.",
                    }
                }
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["settings"]["delivery"]["telegram"]["summary"] is True
    assert data["settings"]["delivery"]["telegram"]["lang"] == "de"
    assert (
        data["settings"]["delivery"]["telegram"]["prompt"]
        == "Retell the article neutrally in two short sentences."
    )


async def test_create_news_task_missing_name(
    client: AsyncClient, auth_headers: dict
):
    """Test creating task fails without name."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "prompt": "Some prompt",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_empty_name(
    client: AsyncClient, auth_headers: dict
):
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


async def test_create_news_task_missing_prompt(
    client: AsyncClient, auth_headers: dict
):
    """Test creating task fails without prompt."""
    response = await client.post(
        "/api/news-tasks/",
        headers=auth_headers,
        json={
            "name": "Task Name",
        },
    )
    assert response.status_code == 422


async def test_create_news_task_empty_prompt(
    client: AsyncClient, auth_headers: dict
):
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


async def test_get_news_task_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Test getting non-existent task returns 404."""
    response = await client.get("/api/news-tasks/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_get_news_task_unauthorized(
    client: AsyncClient, test_news_task: NewsTask
):
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
    assert "settings" in data


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


async def test_update_news_task_not_found(
    client: AsyncClient, auth_headers: dict
):
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


async def test_delete_news_task_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Test deleting non-existent task returns 404."""
    response = await client.delete(
        "/api/news-tasks/99999", headers=auth_headers
    )
    assert response.status_code == 404


async def test_associate_telegram_bot_with_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
    test_telegram_bot,
):
    """Test creating telegram bot association for task."""
    response = await client.post(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots/{test_telegram_bot.id}",
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["telegram_bot_id"] == test_telegram_bot.id
    assert data["news_task_id"] == test_news_task.id


async def test_associate_telegram_bot_with_task_duplicate(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
    test_telegram_bot,
):
    """Test duplicate bot-task association is rejected."""
    url = f"/api/news-tasks/{test_news_task.id}/telegram-bots/{test_telegram_bot.id}"

    first = await client.post(url, headers=auth_headers)
    second = await client.post(url, headers=auth_headers)

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Association already exists"


async def test_associate_telegram_bot_with_task_missing_task(
    client: AsyncClient,
    auth_headers: dict,
    test_telegram_bot,
):
    """Test bot-task association fails if task does not exist."""
    response = await client.post(
        f"/api/news-tasks/99999/telegram-bots/{test_telegram_bot.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "News task not found"


async def test_associate_telegram_bot_with_task_missing_bot(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test bot-task association fails if bot does not exist."""
    response = await client.post(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Telegram bot not found"


async def test_disassociate_telegram_bot_from_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
    test_telegram_bot,
):
    """Test removing telegram bot association from task."""
    url = f"/api/news-tasks/{test_news_task.id}/telegram-bots/{test_telegram_bot.id}"

    create_response = await client.post(url, headers=auth_headers)
    assert create_response.status_code == 201

    delete_response = await client.delete(url, headers=auth_headers)
    assert delete_response.status_code == 204


async def test_disassociate_telegram_bot_from_task_not_found(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
    test_telegram_bot,
):
    """Test deleting non-existent bot-task association returns 404."""
    response = await client.delete(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots/{test_telegram_bot.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Association not found"


async def test_disassociate_telegram_bot_from_task_missing_task(
    client: AsyncClient,
    auth_headers: dict,
    test_telegram_bot,
):
    """Test removing association fails when task does not exist."""
    response = await client.delete(
        f"/api/news-tasks/99999/telegram-bots/{test_telegram_bot.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "News task not found"


async def test_disassociate_telegram_bot_from_task_missing_bot(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
):
    """Test removing association fails when bot does not exist."""
    response = await client.delete(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Telegram bot not found"


async def test_list_telegram_bots_for_task(
    client: AsyncClient,
    auth_headers: dict,
    test_news_task: NewsTask,
    test_telegram_bot,
):
    """Test listing bot associations for a task."""
    create_response = await client.post(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots/{test_telegram_bot.id}",
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    response = await client.get(
        f"/api/news-tasks/{test_news_task.id}/telegram-bots",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["telegram_bot_id"] == test_telegram_bot.id
    assert data[0]["news_task_id"] == test_news_task.id
