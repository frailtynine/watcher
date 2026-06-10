import pytest
from unittest.mock import AsyncMock, Mock, patch

from telegram.error import TelegramError

from app.validators.telegram_bot import (
    TelegramBotValidationError,
    validate_telegram_bot_token,
)


@pytest.mark.asyncio
async def test_validate_telegram_bot_token_success():
    with patch("app.validators.telegram_bot.Bot") as bot_cls:
        bot_instance = Mock()
        bot_cls.return_value = bot_instance

        me = Mock()
        me.id = 111
        me.username = "my_news_bot"
        me.is_bot = True
        bot_instance.get_me = AsyncMock(return_value=me)

        result = await validate_telegram_bot_token(" 123:ABC ")

    bot_cls.assert_called_once_with(token="123:ABC")
    assert result["bot_name"] == "my_news_bot"
    assert result["bot_tg_id"] == "111"


@pytest.mark.asyncio
async def test_validate_telegram_bot_token_rejects_non_bot_user():
    with patch("app.validators.telegram_bot.Bot") as bot_cls:
        bot_instance = Mock()
        bot_cls.return_value = bot_instance

        me = Mock()
        me.id = 222
        me.username = "not_a_bot"
        me.is_bot = False
        bot_instance.get_me = AsyncMock(return_value=me)

        with pytest.raises(TelegramBotValidationError) as exc_info:
            await validate_telegram_bot_token("123:ABC")

    assert "does not belong to a bot" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_telegram_bot_token_invalid_token():
    with patch("app.validators.telegram_bot.Bot") as bot_cls:
        bot_instance = Mock()
        bot_cls.return_value = bot_instance
        bot_instance.get_me = AsyncMock(side_effect=TelegramError("bad token"))

        with pytest.raises(TelegramBotValidationError) as exc_info:
            await validate_telegram_bot_token("bad-token")

    assert str(exc_info.value) == "Invalid Telegram bot token."
