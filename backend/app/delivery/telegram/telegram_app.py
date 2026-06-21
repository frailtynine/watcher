from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.delivery.telegram.telegram_service import TelegramService


class TelegramApp:
    """Runtime wrapper for one Telegram bot application instance."""

    CALLBACK_PREFIX = "task:"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self._service = TelegramService()
        self.application = self._build_application()

    def _build_application(self) -> Application:
        application = Application.builder().token(self.bot_token).build()
        application.add_handler(CommandHandler("start", self._on_start))
        application.add_handler(
            CallbackQueryHandler(
                self._on_task_selected,
                pattern=rf"^{self.CALLBACK_PREFIX}\d+$",
            )
        )
        return application

    async def _on_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if not update.effective_user or not update.effective_chat:
            return

        me = await context.bot.get_me()
        bot_data = await self._service.get_bot_instance_by_tg_id(str(me.id))
        if not bot_data:
            await update.effective_chat.send_message(
                "This bot is not connected in NewsWatcher yet."
            )
            return

        tasks = await self._service.get_active_tasks_for_bot(bot_data["id"])
        if not tasks:
            await update.effective_chat.send_message(
                "No active tasks are linked to this bot yet."
            )
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=str(task["name"]),
                        callback_data=f"{self.CALLBACK_PREFIX}{task['id']}",
                    )
                ]
                for task in tasks
            ]
        )

        await update.effective_chat.send_message(
            "Select a task for this chat:",
            reply_markup=keyboard,
        )

    async def _on_task_selected(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        query = update.callback_query
        if not query or not update.effective_chat:
            return

        await query.answer()

        data = query.data or ""
        if not data.startswith(self.CALLBACK_PREFIX):
            return

        task_id_raw = data.removeprefix(self.CALLBACK_PREFIX)
        if not task_id_raw.isdigit():
            return

        me = await context.bot.get_me()
        bot_data = await self._service.get_bot_instance_by_tg_id(str(me.id))
        if not bot_data:
            await query.edit_message_text("Bot is not linked in NewsWatcher.")
            return

        saved = await self._service.save_chat_subscription(
            telegram_bot_id=bot_data["id"],
            chat_id=update.effective_chat.id,
            task_id=int(task_id_raw),
        )

        if not saved:
            await query.edit_message_text(
                "Could not save chat subscription for this task."
            )
            return

        await query.edit_message_text("Done. This chat is now subscribed.")

    async def start(self) -> None:
        """Initialize and start polling for this bot app."""
        await self.application.initialize()
        await self.application.start()
        if self.application.updater is None:
            raise RuntimeError(
                "Telegram application updater is not configured."
            )
        await self.application.updater.start_polling()

    async def stop(self) -> None:
        """Stop polling and clean up the application."""
        if self.application.updater:
            await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
