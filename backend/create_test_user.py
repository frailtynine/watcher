#!/usr/bin/env python
"""Create a test user for development"""
import asyncio
from app.db import get_async_session
from app.models import User
from app.schemas import UserCreate


async def create_user():
    # Get database session
    async for session in get_async_session():
        # Get user manager
        from fastapi_users.db import SQLAlchemyUserDatabase
        user_db = SQLAlchemyUserDatabase(session, User)

        # Import user manager class and create instance
        from app.core.users import UserManager
        user_manager = UserManager(user_db)

        # Create user
        user_create = UserCreate(
            email="test@example.com",
            password="password123"
        )

        try:
            user = await user_manager.create(user_create)
            print(f'✅ Test user created: {user.email} / password123')
        except Exception as e:
            print(f'❌ Error creating user: {e}')

        break  # Only use first session


if __name__ == '__main__':
    asyncio.run(create_user())
