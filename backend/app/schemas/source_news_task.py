from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SourceNewsTaskCreate(BaseModel):
    source_id: int
    news_task_id: int


class SourceNewsTaskRead(BaseModel):
    source_id: int
    news_task_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
