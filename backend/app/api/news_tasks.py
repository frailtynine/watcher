from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_async_session
from app.crud import (
    news_task_crud,
    telegram_bot_crud,
    telegram_bot_news_task_crud,
)
from app.schemas import NewsTaskCreate, NewsTaskRead, NewsTaskUpdate
from app.schemas.telegram_bot_news_task import (
    TelegramBotNewsTaskCreate,
    TelegramBotNewsTaskRead,
)
from app.api.auth import current_active_user
from app.models import User, NewsTask, SourceNewsTask

router = APIRouter()


@router.post("/", response_model=NewsTaskRead, status_code=201)
async def create_news_task(
    news_task: NewsTaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Create a new news task for the current user"""
    from app.schemas.news_task import NewsTaskCreateInternal

    task_internal = NewsTaskCreateInternal(
        **news_task.model_dump(), user_id=user.id
    )
    created = await news_task_crud.create(
        db, task_internal, schema_to_select=NewsTaskRead, return_as_model=True
    )
    return created


@router.get("/", response_model=list[NewsTaskRead])
async def list_news_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """List all news tasks for the current user with sources count"""
    result = await news_task_crud.get_multi(
        db,
        offset=skip,
        limit=limit,
        user_id=user.id,
        schema_to_select=NewsTaskRead,
        return_as_model=True,
    )

    tasks = result["data"]

    # Get sources count for each task
    task_ids = [task.id for task in tasks]
    if task_ids:
        stmt = (
            select(
                SourceNewsTask.news_task_id,
                func.count(SourceNewsTask.source_id).label("count"),
            )
            .where(SourceNewsTask.news_task_id.in_(task_ids))
            .group_by(SourceNewsTask.news_task_id)
        )
        result_counts = await db.execute(stmt)
        counts_dict = {row.news_task_id: row.count for row in result_counts}

        for task in tasks:
            task.sources_count = counts_dict.get(task.id, 0)

    return tasks


@router.get("/{task_id}", response_model=NewsTaskRead)
async def get_news_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get a specific news task"""
    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")
    return task


@router.patch("/{task_id}", response_model=NewsTaskRead)
async def update_news_task(
    task_id: int,
    news_task_update: NewsTaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Update a news task"""
    from datetime import datetime, timezone

    # Check ownership
    existing = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="News task not found")

    # Manually set updated_at to naive UTC to avoid timezone mismatch
    # (FastCRUD auto-sets it with timezone-aware datetime)
    update_dict = news_task_update.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

    # Use raw SQL update to avoid FastCRUD's auto-timezone handling
    from sqlalchemy import update

    stmt = (
        update(NewsTask)
        .where(NewsTask.id == task_id)
        .values(**update_dict)
        .returning(NewsTask)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated = result.scalar_one()

    return updated


@router.delete("/{task_id}", status_code=204)
async def delete_news_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete a news task"""
    # Check ownership
    existing = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="News task not found")

    await news_task_crud.delete(db, id=task_id)
    return None


@router.post(
    "/{task_id}/telegram-bots/{bot_id}",
    response_model=TelegramBotNewsTaskRead,
    status_code=201,
)
async def associate_telegram_bot_with_task(
    task_id: int,
    bot_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Associate a Telegram bot with a news task."""
    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    bot = await telegram_bot_crud.get(db, id=bot_id, user_id=user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Telegram bot not found")

    existing = await telegram_bot_news_task_crud.get(
        db,
        telegram_bot_id=bot_id,
        news_task_id=task_id,
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Association already exists"
        )

    association = TelegramBotNewsTaskCreate(
        telegram_bot_id=bot_id,
        news_task_id=task_id,
    )
    return await telegram_bot_news_task_crud.create(
        db,
        association,
        schema_to_select=TelegramBotNewsTaskRead,
        return_as_model=True,
    )


@router.get(
    "/{task_id}/telegram-bots",
    response_model=list[TelegramBotNewsTaskRead],
)
async def list_telegram_bots_for_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    associations = await telegram_bot_news_task_crud.get_multi(
        db,
        news_task_id=task_id,
        schema_to_select=TelegramBotNewsTaskRead,
        return_as_model=True,
    )
    return associations["data"]


@router.delete("/{task_id}/telegram-bots/{bot_id}", status_code=204)
async def disassociate_telegram_bot_from_task(
    task_id: int,
    bot_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    bot = await telegram_bot_crud.get(db, id=bot_id, user_id=user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Telegram bot not found")

    existing = await telegram_bot_news_task_crud.get(
        db,
        telegram_bot_id=bot_id,
        news_task_id=task_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Association not found")

    await telegram_bot_news_task_crud.delete(
        db,
        telegram_bot_id=bot_id,
        news_task_id=task_id,
    )
    return None
