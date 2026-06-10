import logging

from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


class TelegramBotValidationError(ValueError):
    pass


async def validate_telegram_bot_token(bot_token: str) -> dict[str, str]:
    token = bot_token.strip()
    if not token:
        raise TelegramBotValidationError("Telegram bot token is required.")

    try:
        bot = Bot(token=token)
        me = await bot.get_me()
    except TelegramError as exc:
        logger.warning("Telegram bot token validation failed: %s", exc)
        raise TelegramBotValidationError(
            "Invalid Telegram bot token."
        ) from exc
    except Exception as exc:
        logger.error(
            "Unexpected Telegram bot validation error",
            exc_info=True,
        )
        raise TelegramBotValidationError(
            "Failed to validate Telegram bot token."
        ) from exc

    if not me.is_bot:
        raise TelegramBotValidationError(
            "Provided token does not belong to a bot."
        )

    if not me.username:
        raise TelegramBotValidationError(
            "Telegram bot username is unavailable."
        )

    return {
        "bot_name": me.username,
        "bot_tg_id": str(me.id),
    }
