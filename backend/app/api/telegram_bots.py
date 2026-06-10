from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_active_user
from app.crud import telegram_bot_crud
from app.db import get_async_session
from app.models import User
from app.schemas.telegram_bot import (
    TelegramBotCreate,
    TelegramBotCreateInternal,
    TelegramBotRead,
)
from app.validators import (
    TelegramBotValidationError,
    validate_telegram_bot_token,
)

router = APIRouter()


@router.post("/", response_model=TelegramBotRead, status_code=201)
async def create_telegram_bot(
    payload: TelegramBotCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        validation_result = await validate_telegram_bot_token(
            payload.bot_token
        )
    except TelegramBotValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    bot_to_create = TelegramBotCreateInternal(
        user_id=user.id,
        bot_token=payload.bot_token,
        bot_name=validation_result["bot_name"],
        bot_tg_id=validation_result["bot_tg_id"],
    )

    try:
        return await telegram_bot_crud.create(
            db,
            bot_to_create,
            schema_to_select=TelegramBotRead,
            return_as_model=True,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Telegram bot is already connected.",
        ) from exc


@router.delete("/{bot_id}", status_code=204)
async def delete_telegram_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    bot = await telegram_bot_crud.get(db, id=bot_id)
    if not bot or bot["user_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram bot not found.",
        )
    await telegram_bot_crud.delete(db, id=bot_id)
