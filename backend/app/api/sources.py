from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud import source_crud
from app.schemas import SourceCreate, SourceRead, SourceUpdate
from app.api.auth import current_active_user
from app.models import User

router = APIRouter()


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    source: SourceCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Create a new source for the current user"""
    from app.schemas.source import SourceCreateInternal
    source_internal = SourceCreateInternal(**source.model_dump(), user_id=user.id)
    created = await source_crud.create(
        db,
        source_internal,
        schema_to_select=SourceRead,
        return_as_model=True
    )
    return created


@router.get("/search", response_model=list[SourceRead])
async def search_sources(
    q: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Search sources by name for the current user"""
    from sqlalchemy import select, or_
    from app.models import Source
    
    stmt = (
        select(Source)
        .where(Source.user_id == user.id)
        .where(
            or_(
                Source.name.ilike(f"%{q}%"),
                Source.source.ilike(f"%{q}%")
            )
        )
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    sources = result.scalars().all()
    return sources


@router.get("/", response_model=list[SourceRead])
async def list_sources(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """List all sources for the current user"""
    result = await source_crud.get_multi(
        db,
        offset=skip,
        limit=limit,
        user_id=user.id,
        schema_to_select=SourceRead,
        return_as_model=True
    )
    return result["data"]


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get a specific source"""
    source = await source_crud.get(db, id=source_id, user_id=user.id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: int,
    source_update: SourceUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Update a source"""
    # Check ownership
    existing = await source_crud.get(db, id=source_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    
    updated = await source_crud.update(
        db,
        source_update,
        id=source_id,
        schema_to_select=SourceRead,
        return_as_model=True
    )
    return updated


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Delete a source"""
    # Check ownership
    existing = await source_crud.get(db, id=source_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    
    await source_crud.delete(db, id=source_id)
    return None
