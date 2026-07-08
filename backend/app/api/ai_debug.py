from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services import NotificationService
from app.api.auth import current_active_user
from app.core.config import settings
from app.core.encryption import decrypt_value
from app.db import get_async_session
from app.models import NewsTask, User
from app.schemas.ai_debug import (
    AIDeduplicationDebugRequest,
    AIDeduplicationDebugResponse,
)


router = APIRouter()
ALLOWED_CUTOFF_HOURS = {24, 48, 72, 168}


def _resolve_gemini_api_key(user: User) -> str:
    encrypted_api_key = (user.settings or {}).get("gemini_api_key")
    if not encrypted_api_key or not isinstance(encrypted_api_key, str):
        raise HTTPException(
            status_code=400,
            detail=(
                "Gemini API key is not configured. "
                "Set it in Settings before using AI debug."
            ),
        )
    return decrypt_value(encrypted_api_key, settings.ENCRYPTION_KEY)


@router.post(
    "/deduplication",
    response_model=AIDeduplicationDebugResponse,
)
async def debug_deduplication(
    payload: AIDeduplicationDebugRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    service = NotificationService()
    recent_headlines = [
        headline.strip()
        for headline in payload.recent_headlines
        if headline and headline.strip()
    ]

    if payload.use_task_context:
        if payload.cutoff_hours not in ALLOWED_CUTOFF_HOURS:
            raise HTTPException(
                status_code=422,
                detail="cutoff_hours must be one of: 24, 48, 72, 168",
            )
        if payload.task_id is None:
            raise HTTPException(
                status_code=422,
                detail="task_id is required when use_task_context=true",
            )
        task = await db.get(NewsTask, payload.task_id)
        if not task or task.user_id != user.id:
            raise HTTPException(status_code=404, detail="Task not found")

        recent_headlines = await service.get_recent_relevant_headlines(
            db=db,
            task_id=task.id,
            hours=payload.cutoff_hours,
        )

    gemini_api_key = _resolve_gemini_api_key(user)
    is_new, thinking = await service.evaluate_deduplication_with_headlines(
        gemini_api_key=gemini_api_key,
        candidate_title=payload.candidate_title,
        candidate_content=payload.candidate_content,
        recent_headlines=recent_headlines,
    )

    return AIDeduplicationDebugResponse(
        is_new=is_new,
        thinking=f"{thinking}\n\nRecent Headlines:\n"
        + "\n".join(recent_headlines),
        headlines_used_count=len(recent_headlines),
    )
