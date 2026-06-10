from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import FastAPIUsers, exceptions
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import telegram_bot_crud
from app.db import get_async_session
from app.models import User
from app.schemas.telegram_bot import TelegramBotRead
from app.schemas import UserRead, UserCreate, UserUpdate
from app.core.users import get_user_manager
from app.core.auth import auth_backend
from app.core.user_settings import merge_settings_for_storage


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

router = APIRouter()


async def _build_user_read(user: User, db: AsyncSession) -> UserRead:
    bots_result = await telegram_bot_crud.get_multi(
        db,
        user_id=user.id,
        schema_to_select=TelegramBotRead,
        return_as_model=True,
    )
    bot_settings = [
        {
            "id": bot.id,
            "bot_name": bot.bot_name,
            "bot_tg_id": bot.bot_tg_id,
            "is_active": bot.is_active,
        }
        for bot in bots_result["data"]
    ]

    payload = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "settings": {
            **(user.settings or {}),
            "telegram_bots": bot_settings,
        },
    }
    return UserRead.model_validate(payload)


# Auth routes (login, logout, verify token)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# User routes (register, read, update, delete)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


@router.get(
    "/users/me",
    response_model=UserRead,
    tags=["users"],
    name="users:current_user",
)
async def get_me(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await _build_user_read(user, db)


@router.patch(
    "/users/me",
    response_model=UserRead,
    tags=["users"],
    name="users:patch_current_user",
)
async def update_me(
    request: Request,
    user_update: UserUpdate,
    user: User = Depends(current_active_user),
    user_manager=Depends(get_user_manager),
    db: AsyncSession = Depends(get_async_session),
):
    update_data = user_update.model_dump(exclude_unset=True)

    if "settings" in update_data:
        try:
            update_data["settings"] = merge_settings_for_storage(
                user.settings,
                update_data["settings"],
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

    prepared_update = UserUpdate(**update_data)

    try:
        updated_user = await user_manager.update(
            prepared_update,
            user,
            safe=True,
            request=request,
        )
    except exceptions.InvalidPasswordException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UPDATE_USER_INVALID_PASSWORD",
                "reason": exc.reason,
            },
        ) from exc
    except exceptions.UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UPDATE_USER_EMAIL_ALREADY_EXISTS",
        ) from exc

    return await _build_user_read(updated_user, db)
