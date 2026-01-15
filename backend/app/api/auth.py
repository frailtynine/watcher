from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from app.models import User
from app.schemas import UserRead, UserCreate, UserUpdate
from app.core.users import get_user_manager
from app.core.auth import auth_backend


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

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

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Export current user dependency
current_active_user = fastapi_users.current_user(active=True)
