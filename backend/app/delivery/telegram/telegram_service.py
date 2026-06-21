from sqlalchemy import select

from app.db.database import get_async_session
from app.crud import telegram_bot_crud
from app.models.news_task import NewsTask
from app.models.telegram_bot import TelegramBot
from app.models.telegram_bot_news_task import TelegramBotNewsTask


class TelegramService:
    async def get_active_bots(self) -> list[dict]:
        async for session in get_async_session():
            result = await telegram_bot_crud.get_multi(
                session,
                is_active=True,
            )
            return result["data"]
        return []

    async def get_bot_instance(
        self, user_id: int, telegram_bot_id: int
    ) -> dict | None:
        bot = None
        async for session in get_async_session():
            bot = await telegram_bot_crud.get(session, id=telegram_bot_id)
            break
        if bot and bot["user_id"] == user_id:
            return bot
        return None

    async def get_bot_instance_by_tg_id(
        self,
        bot_tg_id: str,
    ) -> dict | None:
        async for session in get_async_session():
            bot = await telegram_bot_crud.get(
                session,
                bot_tg_id=bot_tg_id,
            )
            return bot
        return None

    async def get_active_tasks_for_bot(
        self,
        telegram_bot_id: int,
    ) -> list[dict[str, int | str]]:
        async for session in get_async_session():
            stmt = (
                select(NewsTask.id, NewsTask.name)
                .join(
                    TelegramBotNewsTask,
                    TelegramBotNewsTask.news_task_id == NewsTask.id,
                )
                .where(
                    TelegramBotNewsTask.telegram_bot_id == telegram_bot_id,
                    NewsTask.active.is_(True),
                )
                .order_by(NewsTask.created_at.desc())
            )
            result = await session.execute(stmt)
            return [{"id": row.id, "name": row.name} for row in result.all()]
        return []

    async def save_chat_subscription(
        self,
        telegram_bot_id: int,
        chat_id: int | str,
        task_id: int,
    ) -> bool:
        async for session in get_async_session():
            bot = await session.get(TelegramBot, telegram_bot_id)
            if not bot:
                return False

            has_task_stmt = select(TelegramBotNewsTask).where(
                TelegramBotNewsTask.telegram_bot_id == telegram_bot_id,
                TelegramBotNewsTask.news_task_id == task_id,
            )
            has_task_result = await session.execute(has_task_stmt)
            if has_task_result.scalar_one_or_none() is None:
                return False

            normalized_chat_id = str(chat_id)
            chats = list(bot.chats or [])

            for chat in chats:
                if (
                    str(chat.get("chat_id")) == normalized_chat_id
                    and chat.get("task_id") == task_id
                ):
                    return True

            chats.append(
                {
                    "chat_id": normalized_chat_id,
                    "task_id": task_id,
                }
            )

            bot.chats = chats
            await session.commit()
            return True

        return False
