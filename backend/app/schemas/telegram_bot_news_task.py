from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelegramBotNewsTaskCreate(BaseModel):
    telegram_bot_id: int
    news_task_id: int


class TelegramBotNewsTaskRead(BaseModel):
    telegram_bot_id: int
    news_task_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
