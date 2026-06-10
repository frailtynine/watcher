import pytest
from httpx import AsyncClient
from sqlalchemy import select
from unittest.mock import patch

from app.core.config import settings
from app.core.encryption import decrypt_value
from app.models import TelegramBot

pytestmark = pytest.mark.anyio


async def test_create_telegram_bot_success(
    client: AsyncClient,
    auth_headers: dict,
    db_session_maker,
):
    with patch(
        "app.api.telegram_bots.validate_telegram_bot_token"
    ) as mock_validate:
        mock_validate.return_value = {
            "bot_name": "newswatcher_bot",
            "bot_tg_id": "123456789",
        }

        response = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "123456:ABCDEF"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["bot_name"] == "newswatcher_bot"
    assert data["bot_tg_id"] == "123456789"
    assert data["bot_token"] is True
    assert "chats" not in data
    assert data["is_active"] is True

    async with db_session_maker() as session:
        result = await session.execute(
            select(TelegramBot).where(TelegramBot.bot_tg_id == "123456789")
        )
        created_bot = result.scalar_one()

    assert (
        decrypt_value(created_bot.bot_token, settings.ENCRYPTION_KEY)
        == "123456:ABCDEF"
    )


async def test_create_telegram_bot_invalid_token(
    client: AsyncClient,
    auth_headers: dict,
):
    with patch(
        "app.api.telegram_bots.validate_telegram_bot_token"
    ) as mock_validate:
        from app.validators import TelegramBotValidationError

        mock_validate.side_effect = TelegramBotValidationError(
            "Invalid Telegram bot token."
        )

        response = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "bad-token"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Telegram bot token."


async def test_create_telegram_bot_duplicate_tg_id(
    client: AsyncClient,
    auth_headers: dict,
):
    with patch(
        "app.api.telegram_bots.validate_telegram_bot_token"
    ) as mock_validate:
        mock_validate.return_value = {
            "bot_name": "newswatcher_bot",
            "bot_tg_id": "123456789",
        }

        first = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "123456:ABCDEF"},
        )
        second = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "123456:ZZZZZZ"},
        )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Telegram bot is already connected."


async def test_get_current_user_includes_telegram_bots(
    client: AsyncClient,
    auth_headers: dict,
):
    with patch(
        "app.api.telegram_bots.validate_telegram_bot_token"
    ) as mock_validate:
        mock_validate.return_value = {
            "bot_name": "delivery_bot",
            "bot_tg_id": "987654321",
        }
        create_response = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "987654:AAAAAA"},
        )
        assert create_response.status_code == 201

    me_response = await client.get("/api/users/me", headers=auth_headers)
    assert me_response.status_code == 200
    data = me_response.json()
    assert len(data["settings"]["telegram_bots"]) == 1
    assert data["settings"]["telegram_bots"][0]["bot_name"] == "delivery_bot"
    assert data["settings"]["telegram_bots"][0]["bot_tg_id"] == "987654321"


async def test_create_and_delete_telegram_bot_success(
    client: AsyncClient,
    auth_headers: dict,
    db_session_maker,
):
    with patch(
        "app.api.telegram_bots.validate_telegram_bot_token"
    ) as mock_validate:
        mock_validate.return_value = {
            "bot_name": "test_bot_delete",
            "bot_tg_id": "1234567",
        }

        response = await client.post(
            "/api/telegram-bots/",
            headers=auth_headers,
            json={"bot_token": "123456:ABCDEF"},
        )

    assert response.status_code == 201
    data = response.json()
    delete_response = await client.delete(
        f"/api/telegram-bots/{data['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204
