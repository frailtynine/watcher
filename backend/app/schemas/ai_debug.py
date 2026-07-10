from pydantic import BaseModel, Field


class AIDeduplicationDebugRequest(BaseModel):
    candidate_title: str = Field(..., min_length=1, max_length=500)
    candidate_content: str = Field(..., min_length=1)
    recent_headlines: list[str] = Field(default_factory=list, max_length=200)
    task_id: int | None = None
    use_task_context: bool = False
    cutoff_hours: int = Field(default=24, ge=24, le=168)


class AIDeduplicationDebugResponse(BaseModel):
    is_new: bool
    thinking: str
    headlines_used_count: int


class AISummaryDebugRequest(BaseModel):
    link: str = Field(..., min_length=1, max_length=2048)
    task_id: int | None = None


class AISummaryDebugResponse(BaseModel):
    summary: str
    prompt_used: str
    language: str
    task_id: int | None = None
