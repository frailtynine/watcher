from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

from app.core.encryption import decrypt_value
from app.core.config import settings


class TelegramSender:
    """Build Telegram bot application instances for one user."""

    def __init__(self, encrypted_bot_token: str):
        self.encrypted_bot_token = encrypted_bot_token

    def _get_decrypted_bot_token(self) -> str:
        """Decrypt bot token for storage and return it."""
        return decrypt_value(
            self.encrypted_bot_token,
            settings.ENCRYPTION_KEY,
        )

    def _get_bot(self) -> Bot:
        """Get a Telegram Bot instance with decrypted credentials."""
        return Bot(token=self._get_decrypted_bot_token())

    def _build_keyboard(self, callback_data: str) -> InlineKeyboardMarkup:
        """Build a keyboard layout for Telegram messages."""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="👎",
                    callback_data=callback_data,
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # TODO: Advanced text format
    async def send_message(
        self,
        user_id: int | str,
        chat_id: int | str,
        newstask_id: int | str,
        news_url: str,
    ) -> None:
        """Send a message to a specific chat using the bot."""
        # Callback function not implemented yet, so no keyboard for now
        # keyboard = self._build_keyboard(
        #     callback_data=f"{user_id}:{newstask_id}"
        # )
        bot = self._get_bot()
        async with bot:
            await bot.send_message(
                chat_id=chat_id,
                text=news_url,
                # reply_markup=keyboard
            )

    # def build_application(
    #     self,
    # ) -> Application:
    #     """Create one Telegram Application instance from credentials.

    #     Manager code can later start the returned instance with polling or
    #     webhook lifecycle methods.
    #     """
    #     return Application.builder().token(
    #         self._get_decrypted_bot_credentials()
    #     ).build()
