"""Example of how to integrate AI consumer into scheduler.

This file is NOT part of the codebase yet, just an example.
To integrate, add this code to app/main.py.
"""

from app.ai.consumer import AIConsumer
from app.db import get_async_session
from app.models.user import User
from sqlalchemy import select


async def ai_consumer_job():
    """Process news items with AI for all users."""
    async for db in get_async_session():
        try:
            # Get all active users
            stmt = select(User).where(User.is_active.is_(True))
            result = await db.execute(stmt)
            users = result.scalars().all()

            consumer = AIConsumer()

            for user in users:
                # Check if user has API key configured
                if (not user.settings or
                        not user.settings.get('gemini_api_key')):
                    continue

                # Process news for this user
                stats = await consumer.process_user_news(db, user)
                print(
                    f"Processed news for user {user.email}: "
                    f"{stats['processed']} items, {stats['errors']} errors"
                )

        except Exception as e:
            print(f"Error in AI consumer job: {e}")
        finally:
            break


# To add to scheduler in app/main.py:
#
# from app.producers.ai_consumer_example import ai_consumer_job
#
# scheduler.add_job(
#     ai_consumer_job,
#     'interval',
#     minutes=10,  # Run every 10 minutes
#     id='ai_consumer',
#     max_instances=1,
#     replace_existing=True
# )
