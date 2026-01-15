from datetime import datetime
from pydantic import BaseModel


class SourceNewsTaskCreate(BaseModel):
    source_id: int
    news_task_id: int


class SourceNewsTaskRead(BaseModel):
    source_id: int
    news_task_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
