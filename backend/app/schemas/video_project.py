from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VideoProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    video_json: dict
    clip_urls: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("video_json")
    @classmethod
    def validate_video_json(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("video_json must be a JSON object")
        return value

    @field_validator("clip_urls")
    @classmethod
    def validate_clip_urls(cls, value: list[str]) -> list[str]:
        if len(value) > 50:
            raise ValueError("clip_urls cannot contain more than 50 items")
        return value


class VideoProjectCreate(VideoProjectBase):
    pass


class VideoProjectCreateInternal(VideoProjectBase):
    user_id: int


class VideoProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    video_json: dict | None = None
    clip_urls: list[str] | None = Field(None, max_length=50)

    @field_validator("video_json")
    @classmethod
    def validate_video_json(cls, value: dict | None) -> dict | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("video_json must be a JSON object")
        return value

    @field_validator("clip_urls")
    @classmethod
    def validate_clip_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) > 50:
            raise ValueError("clip_urls cannot contain more than 50 items")
        return value


class VideoProjectRead(VideoProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
