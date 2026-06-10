from telegram.ext import Application
from telegram import Bot

from app.models.user import User
from app.models.telegram_bot import TelegramBot
from app.core.encryption import decrypt_value
from app.core.config import settings


class TelegramBot:
    """Build Telegram bot application instances for one user."""

    def __init__(self, bot: TelegramBot):
        self.bot = bot

    def _get_decrypted_bot_credentials(self) -> str:
        """Decrypt bot token for storage and return it."""
        return decrypt_value(
            self.bot.bot_token,
            settings.ENCRYPTION_KEY,
        )
    
    def get_bot(self) -> Bot:
        """Get a Telegram Bot instance with decrypted credentials."""
        return Bot(token=self._get_decrypted_bot_credentials())
    
    async def send_message(self, chat_id: int, text: str, callback_data: str | None = None) -> None:
        """Send a message to a specific chat using the bot."""
        bot = self.get_bot()
        async with bot:
            await bot.send_message(chat_id=chat_id, text=text)
        

    def build_application(
        self,
    ) -> Application:
        """Create one Telegram Application instance from credentials.

        Manager code can later start the returned instance with polling or
        webhook lifecycle methods.
        """
        return Application.builder().token(
            self._get_decrypted_bot_credentials()
        ).build()
