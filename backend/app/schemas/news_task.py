from datetime import datetime
from pydantic import BaseModel, Field


class NewsTaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)
    active: bool = True


class NewsTaskCreate(NewsTaskBase):
    pass


class NewsTaskCreateInternal(NewsTaskBase):
    """Internal schema with user_id for creation"""
    user_id: int


class NewsTaskUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    prompt: str | None = Field(None, min_length=1)
    active: bool | None = None


class NewsTaskRead(NewsTaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    sources_count: int = 0

    class Config:
        from_attributes = True
