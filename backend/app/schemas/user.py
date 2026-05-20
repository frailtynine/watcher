from fastapi_users import schemas
from pydantic import Field, field_validator

from app.core.user_settings import settings_presence


class UserRead(schemas.BaseUser[int]):
    settings: dict[str, bool] = Field(default_factory=dict)

    @field_validator("settings", mode="before")
    def mark_settings_presence(cls, value: dict | None) -> dict[str, bool]:
        return settings_presence(value)


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    settings: dict[str, str | None] | None = None
