from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.user_settings import settings_presence


class TelegramBotSettingsRead(BaseModel):
    id: int
    bot_name: str
    bot_tg_id: str
    is_active: bool


class UserSettingsRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    gemini_api_key: bool | None = None
    telegram_api_id: bool | None = None
    telegram_api_hash: bool | None = None
    telegram_session_string: bool | None = None
    telegram_bots: list[TelegramBotSettingsRead] = Field(default_factory=list)


class UserSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    gemini_api_key: str | None = None
    telegram_api_id: str | None = None
    telegram_api_hash: str | None = None
    telegram_session_string: str | None = None


class UserRead(schemas.BaseUser[int]):
    settings: UserSettingsRead = Field(default_factory=UserSettingsRead)

    @field_validator("settings", mode="before")
    def mark_settings_presence(cls, value: dict | None) -> dict:
        return settings_presence(value)


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    settings: UserSettingsUpdate | None = None
