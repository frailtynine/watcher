from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import FastAPIUsers, exceptions

from app.models import User
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
):
    return UserRead.model_validate(user)


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
):
    update_data = user_update.model_dump(exclude_unset=True)

    if "settings" in update_data:
        update_data["settings"] = merge_settings_for_storage(
            user.settings,
            update_data["settings"],
        )

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

    return UserRead.model_validate(updated_user)
