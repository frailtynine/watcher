from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud import source_news_task_crud, source_crud, news_task_crud
from app.schemas import SourceNewsTaskCreate, SourceNewsTaskRead
from app.api.auth import current_active_user
from app.models import User

router = APIRouter()


@router.post("/", response_model=SourceNewsTaskRead, status_code=201)
async def associate_source_with_task(
    association: SourceNewsTaskCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Associate a source with a news task"""
    # Verify ownership of both source and task
    source = await source_crud.get(
        db, id=association.source_id, user_id=user.id
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    task = await news_task_crud.get(
        db, id=association.news_task_id, user_id=user.id
    )
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    # Check if association already exists
    existing = await source_news_task_crud.get(
        db,
        source_id=association.source_id,
        news_task_id=association.news_task_id
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Association already exists"
        )

    created = await source_news_task_crud.create(
        db,
        association,
        schema_to_select=SourceNewsTaskRead,
        return_as_model=True
    )
    return created


@router.delete("/{source_id}/{task_id}", status_code=204)
async def disassociate_source_from_task(
    source_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Remove association between source and news task"""
    # Verify ownership
    source = await source_crud.get(db, id=source_id, user_id=user.id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    # Delete association
    await source_news_task_crud.delete(
        db, source_id=source_id, news_task_id=task_id
    )
    return None


@router.get("/source/{source_id}", response_model=list[SourceNewsTaskRead])
async def list_tasks_for_source(
    source_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """List all news tasks associated with a source"""
    # Verify ownership
    source = await source_crud.get(db, id=source_id, user_id=user.id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    associations = await source_news_task_crud.get_multi(
        db,
        source_id=source_id,
        schema_to_select=SourceNewsTaskRead,
        return_as_model=True
    )
    return associations["data"]


@router.get("/task/{task_id}", response_model=list[SourceNewsTaskRead])
async def list_sources_for_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """List all sources associated with a news task"""
    # Verify ownership
    task = await news_task_crud.get(db, id=task_id, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="News task not found")

    associations = await source_news_task_crud.get_multi(
        db,
        news_task_id=task_id,
        schema_to_select=SourceNewsTaskRead,
        return_as_model=True
    )
    return associations["data"]
