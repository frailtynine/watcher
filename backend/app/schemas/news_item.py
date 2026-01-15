from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any


class NewsItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    url: str | None = Field(None, max_length=1000)
    external_id: str | None = Field(None, max_length=255)
    published_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class NewsItemCreate(NewsItemBase):
    source_id: int


class NewsItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    url: str | None = Field(None, max_length=1000)
    external_id: str | None = Field(None, max_length=255)
    published_at: datetime | None = None
    processed: bool | None = None
    result: bool | None = None
    processed_at: datetime | None = None
    ai_response: Dict[str, Any] | None = None
    settings: Dict[str, Any] | None = None
    raw_data: Dict[str, Any] | None = None


class NewsItemRead(NewsItemBase):
    id: int
    source_id: int
    fetched_at: datetime
    processed: bool
    result: bool | None
    processed_at: datetime | None
    ai_response: Dict[str, Any] | None
    
    class Config:
        from_attributes = True
