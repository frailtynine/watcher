from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    settings: dict = {}


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    settings: dict | None = None
