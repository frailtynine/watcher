from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_active_user
from app.crud import video_project_crud
from app.db import get_async_session
from app.models import User, VideoProject
from app.schemas import (
    VideoProjectCreate,
    VideoProjectRead,
    VideoProjectUpdate,
)
from app.schemas.video_project import VideoProjectCreateInternal


router = APIRouter()


@router.post("/", response_model=VideoProjectRead, status_code=201)
async def create_video_project(
    payload: VideoProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    internal = VideoProjectCreateInternal(
        **payload.model_dump(),
        user_id=user.id,
    )
    return await video_project_crud.create(
        db,
        internal,
        schema_to_select=VideoProjectRead,
        return_as_model=True,
    )


@router.get("/", response_model=list[VideoProjectRead])
async def list_video_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    result = await video_project_crud.get_multi(
        db,
        offset=skip,
        limit=limit,
        user_id=user.id,
        schema_to_select=VideoProjectRead,
        return_as_model=True,
    )
    return result["data"]


@router.get("/{video_id}", response_model=VideoProjectRead)
async def get_video_project(
    video_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    project = await video_project_crud.get(db, id=video_id, user_id=user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Video project not found")
    return project


@router.patch("/{video_id}", response_model=VideoProjectRead)
async def update_video_project(
    video_id: int,
    payload: VideoProjectUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    existing = await video_project_crud.get(db, id=video_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Video project not found")

    update_dict = payload.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

    stmt = (
        update(VideoProject)
        .where(VideoProject.id == video_id)
        .values(**update_dict)
        .returning(VideoProject)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


@router.delete("/{video_id}", status_code=204)
async def delete_video_project(
    video_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    existing = await video_project_crud.get(db, id=video_id, user_id=user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Video project not found")

    await video_project_crud.delete(db, id=video_id)
    return None
