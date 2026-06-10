from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelegramBotChatRead(BaseModel):
    chat_id: str
    task_id: int


class TelegramBotCreate(BaseModel):
    bot_token: str = Field(..., min_length=1)


class TelegramBotCreateInternal(BaseModel):
    user_id: int
    bot_token: str
    bot_name: str
    bot_tg_id: str
    chats: list[TelegramBotChatRead] = Field(default_factory=list)
    is_active: bool = True


class TelegramBotRead(BaseModel):
    id: int
    user_id: int
    bot_name: str
    bot_tg_id: str
    bot_token: bool = True
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("bot_token", mode="before")
    @classmethod
    def mask_bot_token(cls, value: object) -> bool:
        return bool(value)
