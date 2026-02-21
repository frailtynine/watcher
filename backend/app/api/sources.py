from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.crud import source_crud
from app.models import SourceType
from app.schemas import SourceCreate, SourceRead, SourceUpdate
from app.api.auth import current_active_user
from app.models import User
from app.core import settings
from app.validators import validate_telegram_channel, validate_rss_feed

router = APIRouter()


class TelegramValidationRequest(BaseModel):
    channel: str


class TelegramValidationResponse(BaseModel):
    valid: bool
    channel_id: str
    title: str | None
    error: str | None


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    source: SourceCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Create a new source for the current user"""
    from app.schemas.source import SourceCreateInternal

    # Validate based on source type
    if source.type == SourceType.TELEGRAM:
        # Validate Telegram channel before creating source
        validation_result = await validate_telegram_channel(
            channel=source.source,
            api_id=str(settings.BACKEND_TG_API_ID),
            api_hash=settings.BACKEND_TG_API_HASH,
            session_string=settings.BACKEND_TG_SESSION_STRING
        )
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid Telegram channel: "
                    f"{validation_result['error']}"
                )
            )
    elif source.type == SourceType.RSS:
        # Validate RSS feed before creating source
        validation_result = await validate_rss_feed(url=source.source)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid RSS feed: "
                    f"{validation_result['error']}"
                )
            )

        # Auto-populate name from feed title if name is generic or not provided
        feed_title = validation_result.get("title")
        if feed_title and (
            not source.name or
            source.name == "My RSS Feed" or
            len(source.name.strip()) == 0
        ):
            # Use feed title as source name
            source = SourceCreate(
                name=feed_title,
                type=source.type,
                source=source.source,
                active=source.active
            )

    source_internal = SourceCreateInternal(
        **source.model_dump(),
        user_id=user.id,
    )
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
