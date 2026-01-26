import pytest
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from fastapi_users.db import SQLAlchemyUserDatabase

from app.db import Base
from app.main import get_app
from app.db.database import get_async_session
from app.models import User
from app.core.users import UserManager
from app.schemas import UserCreate

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@db:5432/newswatcher_test"
)

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session_maker(db_engine):
    """Create a session maker for tests."""
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(db_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with db_session_maker() as session:
        yield session


@pytest.fixture
async def fastapi_app(db_session_maker):
    """Create a test FastAPI app with overridden dependencies."""
    application = get_app()

    async def override_get_async_session():
        async with db_session_maker() as session:
            yield session

    application.dependency_overrides[get_async_session] = (
        override_get_async_session
    )

    yield application

    application.dependency_overrides.clear()


@pytest.fixture
async def client(fastapi_app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(db_session_maker) -> User:
    """Create a test user."""
    async with db_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)

        user_create = UserCreate(
            email=TEST_USER_EMAIL,
            password=TEST_USER_PASSWORD,
        )
        user = await user_manager.create(user_create)
        return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get auth headers with JWT token."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        },
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_source(db_session_maker, test_user: User):
    """Create a test source."""
    from app.models import Source
    from app.models.source import SourceType

    async with db_session_maker() as session:
        source = Source(
            user_id=test_user.id,
            name="Test Source",
            type=SourceType.RSS,
            source="https://example.com/feed",
            active=True,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source


@pytest.fixture
async def test_news_task(db_session_maker, test_user: User):
    """Create a test news task."""
    from app.models import NewsTask

    async with db_session_maker() as session:
        task = NewsTask(
            user_id=test_user.id,
            name="Test Task",
            prompt="Summarize news",
            active=True,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task
