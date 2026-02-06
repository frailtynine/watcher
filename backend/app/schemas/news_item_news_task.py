from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NewsItemNewsTaskBase(BaseModel):
    news_item_id: int
    news_task_id: int


class NewsItemNewsTaskCreate(NewsItemNewsTaskBase):
    pass


class NewsItemNewsTaskUpdate(BaseModel):
    processed: bool | None = None
    result: bool | None = None
    processed_at: datetime | None = None
    ai_response: dict | None = None


class NewsItemNewsTaskRead(NewsItemNewsTaskBase):
    processed: bool
    result: bool | None
    processed_at: datetime | None
    ai_response: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
