from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import encrypt_value
from app.models import (
    NewsTask,
    Source,
    SourceNewsTask,
    NewsItem,
    NewsItemNewsTask,
    User,
    TelegramBot,
    TelegramBotNewsTask,
)
from app.schemas.telegram_bot import TelegramBotCreateInternal

# Create FastCRUD instances for each model
news_task_crud = FastCRUD(NewsTask)
source_crud = FastCRUD(Source)
source_news_task_crud = FastCRUD(SourceNewsTask)
# Disable automatic updated_at handling to avoid timezone issues
news_item_crud = FastCRUD(NewsItem, updated_at_column="")
news_item_news_task_crud = FastCRUD(NewsItemNewsTask)
user_crud = FastCRUD(User)


class TelegramBotCRUD(FastCRUD):
    async def create(
        self,
        db: AsyncSession,
        object: TelegramBotCreateInternal,
        **kwargs,
    ):
        payload = object.model_copy(
            update={
                "bot_token": encrypt_value(
                    object.bot_token.strip(),
                    settings.ENCRYPTION_KEY,
                )
            }
        )
        return await super().create(db, payload, **kwargs)


telegram_bot_crud = TelegramBotCRUD(TelegramBot)
telegram_bot_news_task_crud = FastCRUD(TelegramBotNewsTask)
