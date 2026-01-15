import pytest
from datetime import datetime
import uuid
from sqlalchemy import select

from app.models.user import User
from app.models.news_task import NewsTask
from app.models.source import Source, SourceType


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test creating a User model."""
    # Use unique email to avoid conflicts
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    user = User(
        email=unique_email,
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == unique_email
    assert user.is_active is True
    assert user.is_verified is False


@pytest.mark.asyncio
async def test_create_news_task(db_session):
    """Test creating a NewsTask model."""
    # Create a user
    unique_email = f"task_owner_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create a news task
    news_task = NewsTask(
        user_id=user.id,
        name="Tech News Filter",
        prompt="Filter technology news about AI",
        active=True,
    )
    
    db_session.add(news_task)
    await db_session.commit()
    await db_session.refresh(news_task)
    
    assert news_task.id is not None
    assert news_task.user_id == user.id
    assert news_task.name == "Tech News Filter"
    assert news_task.prompt == "Filter technology news about AI"
    assert news_task.active is True
    assert isinstance(news_task.created_at, datetime)
    assert isinstance(news_task.updated_at, datetime)


@pytest.mark.asyncio
async def test_create_source(db_session):
    """Test creating a Source model."""
    # Create a user
    unique_email = f"source_owner_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create an RSS source
    source = Source(
        user_id=user.id,
        name="TechCrunch RSS",
        type=SourceType.RSS,
        source="https://techcrunch.com/feed/",
        active=True,
    )
    
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    
    assert source.id is not None
    assert source.user_id == user.id
    assert source.name == "TechCrunch RSS"
    assert source.type == SourceType.RSS
    assert source.source == "https://techcrunch.com/feed/"
    assert source.active is True
    assert isinstance(source.created_at, datetime)
