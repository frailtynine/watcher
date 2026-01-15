from datetime import datetime
from pydantic import BaseModel, Field
from app.models.source import SourceType


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: SourceType
    source: str = Field(..., min_length=1, max_length=500)  # URL or channel_id
    active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceCreateInternal(SourceBase):
    """Internal schema with user_id for creation"""
    user_id: int


class SourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: SourceType | None = None
    source: str | None = Field(None, min_length=1, max_length=500)
    active: bool | None = None


class SourceRead(SourceBase):
    id: int
    user_id: int
    last_fetched_at: datetime | None
    created_at: datetime
    
    class Config:
        from_attributes = True
