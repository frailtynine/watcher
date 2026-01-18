from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud import news_item_crud, source_crud
from app.schemas import NewsItemCreate, NewsItemRead, NewsItemUpdate
from app.api.auth import current_active_user
from app.models import User

router = APIRouter()


@router.post("/", response_model=NewsItemRead, status_code=201)
async def create_news_item(
    news_item: NewsItemCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Create a new news item"""
    # Verify source ownership
    source = await source_crud.get(db, id=news_item.source_id, user_id=user.id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    created = await news_item_crud.create(
        db,
        news_item,
        schema_to_select=NewsItemRead,
        return_as_model=True
    )
    return created


@router.get("/", response_model=list[NewsItemRead])
async def list_news_items(
    skip: int = 0,
    limit: int = 100,
    source_id: int | None = Query(None),
    processed: bool | None = Query(None),
    result: bool | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """List news items with optional filters"""
    # Build filter params
    filters = {}
    if source_id is not None:
        # Verify source ownership
        source = await source_crud.get(db, id=source_id, user_id=user.id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        filters["source_id"] = source_id

    if processed is not None:
        filters["processed"] = processed

    if result is not None:
        filters["result"] = result

    items = await news_item_crud.get_multi(
        db,
        offset=skip,
        limit=limit,
        schema_to_select=NewsItemRead,
        return_as_model=True,
        **filters
    )
    return items["data"]


@router.get("/{item_id}", response_model=NewsItemRead)
async def get_news_item(
    item_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get a specific news item"""
    item = await news_item_crud.get(
        db,
        id=item_id,
        schema_to_select=NewsItemRead,
        return_as_model=True,
    )
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")

    source = await source_crud.get(db, id=item.source_id, user_id=user.id)
    if not source:
        raise HTTPException(status_code=404, detail="News item not found")

    return item


@router.patch("/{item_id}", response_model=NewsItemRead)
async def update_news_item(
    item_id: int,
    news_item_update: NewsItemUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Update a news item"""
    item = await news_item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")

    source = await source_crud.get(
        db, id=item["source_id"], user_id=user.id
    )
    if not source:
        raise HTTPException(status_code=404, detail="News item not found")

    updated = await news_item_crud.update(
        db,
        news_item_update,
        id=item_id,
        schema_to_select=NewsItemRead,
        return_as_model=True
    )
    return updated


@router.delete("/{item_id}", status_code=204)
async def delete_news_item(
    item_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Delete a news item"""
    item = await news_item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")

    source = await source_crud.get(
        db, id=item["source_id"], user_id=user.id
    )
    if not source:
        raise HTTPException(status_code=404, detail="News item not found")

    await news_item_crud.delete(db, id=item_id)
    return None
