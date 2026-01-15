from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud import news_task_crud
from app.schemas import NewsTaskCreate, NewsTaskRead, NewsTaskUpdate
from app.api.auth import current_active_user
from app.models import User

router = APIRouter()


@router.post("/", response_model=NewsTaskRead, status_code=201)
async def create_news_task(
    news_task: NewsTaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Create a new news task for the current user"""
    from app.schemas.news_task import NewsTaskCreateInternal
    task_internal = NewsTaskCreateInternal(**news_task.model_dump(), user_id=user.id)
    created = await news_task_crud.create(
        db,
        task_internal,
        schema_to_select=NewsTaskRead,
        return_as_model=True
    )
    return created


@router.get("/", response_model=list[NewsTaskRead])
async def list_news_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """List all news tasks for the current user"""
    result = await news_task_crud.get_multi(
        db,
        offset=skip,
        limit=limit,
        user_id=user.id,
        schema_to_select=NewsTaskRead,
        return_as_model=True
    )
    return result["data"]


@router.get("/{task_id}", response_model=NewsTaskRead)
async def get_news_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
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
    user: User = Depends(current_active_user)
):
    """Update a news task"""
    # Check ownership
    existing = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="News task not found")
    
    updated = await news_task_crud.update(
        db,
        news_task_update,
        id=task_id,
        schema_to_select=NewsTaskRead,
        return_as_model=True
    )
    return updated


@router.delete("/{task_id}", status_code=204)
async def delete_news_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Delete a news task"""
    # Check ownership
    existing = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="News task not found")
    
    await news_task_crud.delete(db, id=task_id)
    return None
