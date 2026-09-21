import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.delivery.telegram.telegram_service import TelegramService


logger = logging.getLogger(__name__)


class TelegramApp:
    """Runtime wrapper for one Telegram bot application instance."""

    SUBSCRIBE_CALLBACK_PREFIX = "task:"
    UNSUBSCRIBE_CALLBACK_PREFIX = "stop:"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self._service = TelegramService()
        self.application = self._build_application()

    def _build_application(self) -> Application:
        application = Application.builder().token(self.bot_token).build()
        application.add_handler(CommandHandler("start", self._on_start))
        application.add_handler(CommandHandler("stop", self._on_stop))
        application.add_handler(
            CallbackQueryHandler(
                self._on_task_selected,
                pattern=rf"^{self.SUBSCRIBE_CALLBACK_PREFIX}\d+$",
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                self._on_stop_selected,
                pattern=rf"^{self.UNSUBSCRIBE_CALLBACK_PREFIX}\d+$",
            )
        )
        return application

    async def _on_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if not update.effective_user or not update.effective_chat:
            logger.info("Telegram /start ignored: missing user or chat")
            return

        me = await context.bot.get_me()
        logger.info(
            "Telegram /start received bot_id=%s bot_username=%s user_id=%s chat_id=%s chat_type=%s",
            me.id,
            me.username,
            update.effective_user.id,
            update.effective_chat.id,
            update.effective_chat.type,
        )
        bot_data = await self._service.get_bot_instance_by_tg_id(str(me.id))
        if not bot_data:
            logger.warning(
                "Telegram /start bot not linked bot_id=%s user_id=%s chat_id=%s",
                me.id,
                update.effective_user.id,
                update.effective_chat.id,
            )
            await update.effective_chat.send_message(
                "This bot is not connected in NewsWatcher yet."
            )
            return

        tasks = await self._service.get_active_tasks_for_bot(bot_data["id"])
        logger.info(
            "Telegram /start resolved bot_record_id=%s tasks=%s user_id=%s chat_id=%s",
            bot_data["id"],
            [task["id"] for task in tasks],
            update.effective_user.id,
            update.effective_chat.id,
        )
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
                        callback_data=(
                            f"{self.SUBSCRIBE_CALLBACK_PREFIX}{task['id']}"
                        ),
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
            logger.info("Telegram task selection ignored: missing query or chat")
            return

        await query.answer()

        data = query.data or ""
        if not data.startswith(self.SUBSCRIBE_CALLBACK_PREFIX):
            return

        task_id_raw = data.removeprefix(self.SUBSCRIBE_CALLBACK_PREFIX)
        if not task_id_raw.isdigit():
            logger.warning("Telegram task selection invalid payload=%r", data)
            return

        me = await context.bot.get_me()
        bot_data = await self._service.get_bot_instance_by_tg_id(str(me.id))
        if not bot_data:
            logger.warning(
                "Telegram task selection bot not linked bot_id=%s user_id=%s chat_id=%s payload=%s",
                me.id,
                update.effective_user.id if update.effective_user else None,
                update.effective_chat.id,
                data,
            )
            await query.edit_message_text("Bot is not linked in NewsWatcher.")
            return

        logger.info(
            "Telegram task selection received bot_record_id=%s bot_id=%s user_id=%s chat_id=%s task_id=%s",
            bot_data["id"],
            me.id,
            update.effective_user.id if update.effective_user else None,
            update.effective_chat.id,
            task_id_raw,
        )
        saved = await self._service.save_chat_subscription(
            telegram_bot_id=bot_data["id"],
            chat_id=update.effective_chat.id,
            task_id=int(task_id_raw),
        )

        if not saved:
            logger.warning(
                "Telegram task selection failed bot_record_id=%s user_id=%s chat_id=%s task_id=%s",
                bot_data["id"],
                update.effective_user.id if update.effective_user else None,
                update.effective_chat.id,
                task_id_raw,
            )
            await query.edit_message_text(
                "Could not save chat subscription for this task."
            )
            return

        logger.info(
            "Telegram task selection saved bot_record_id=%s user_id=%s chat_id=%s task_id=%s",
            bot_data["id"],
            update.effective_user.id if update.effective_user else None,
            update.effective_chat.id,
            task_id_raw,
        )
        await query.edit_message_text("Done. This chat is now subscribed.")

    async def _on_stop(
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

        tasks = await self._service.get_chat_subscriptions_for_bot(
            telegram_bot_id=bot_data["id"],
            chat_id=update.effective_chat.id,
        )
        if not tasks:
            await update.effective_chat.send_message(
                "This chat is not subscribed to any tasks yet."
            )
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=str(task["name"]),
                        callback_data=(
                            f"{self.UNSUBSCRIBE_CALLBACK_PREFIX}{task['id']}"
                        ),
                    )
                ]
                for task in tasks
            ]
        )

        await update.effective_chat.send_message(
            "Select a task to stop for this chat:",
            reply_markup=keyboard,
        )

    async def _on_stop_selected(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        query = update.callback_query
        if not query or not update.effective_chat:
            return

        await query.answer()

        data = query.data or ""
        if not data.startswith(self.UNSUBSCRIBE_CALLBACK_PREFIX):
            return

        task_id_raw = data.removeprefix(self.UNSUBSCRIBE_CALLBACK_PREFIX)
        if not task_id_raw.isdigit():
            return

        me = await context.bot.get_me()
        bot_data = await self._service.get_bot_instance_by_tg_id(str(me.id))
        if not bot_data:
            await query.edit_message_text("Bot is not linked in NewsWatcher.")
            return

        removed = await self._service.remove_chat_subscription(
            telegram_bot_id=bot_data["id"],
            chat_id=update.effective_chat.id,
            task_id=int(task_id_raw),
        )

        if not removed:
            await query.edit_message_text(
                "Could not remove chat subscription for this task."
            )
            return

        await query.edit_message_text(
            "Done. This chat is no longer subscribed."
        )

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
