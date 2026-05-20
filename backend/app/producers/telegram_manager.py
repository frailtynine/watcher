"""Manager for multiple user Telegram producer tasks."""

import asyncio
import logging
from typing import Dict

from sqlalchemy import select

from app.core.config import settings
from app.core.encryption import decrypt_value
from app.db.database import get_async_session
from app.models.user import User
from app.producers.telegram import TelegramProducer


logger = logging.getLogger(__name__)


class TelegramManager:
    """Manages multiple Telegram producer tasks, one per user."""

    def __init__(self, check_interval_seconds: int = 300):
        self.check_interval = check_interval_seconds
        self.user_tasks: Dict[int, asyncio.Task] = {}
        self.running = False

    async def _get_active_users(self) -> list[User]:
        """Get all users with valid Telegram credentials."""
        async for session in get_async_session():
            result = await session.execute(
                select(User).where(User.is_active.is_(True))
            )
            users = result.scalars().all()
            break

        active_users = []
        for user in users:
            if not user.settings:
                continue

            encrypted_api_id = user.settings.get('telegram_api_id')
            encrypted_api_hash = user.settings.get('telegram_api_hash')
            encrypted_session = user.settings.get('telegram_session_string')

            has_credentials = all([
                encrypted_api_id,
                encrypted_api_hash,
                encrypted_session,
            ])

            if has_credentials:
                active_users.append(user)

        return active_users

    async def _run_user_producer(self, user: User) -> None:
        """Run Telegram producer for a specific user."""
        logger.info(
            f"Starting Telegram producer for user {user.id} ({user.email})"
        )
        encrypted_settings = user.settings or {}
        try:
            producer = TelegramProducer(
                api_id=str(
                    decrypt_value(
                        encrypted_settings['telegram_api_id'],
                        settings.ENCRYPTION_KEY,
                    )
                ),
                api_hash=decrypt_value(
                    encrypted_settings['telegram_api_hash'],
                    settings.ENCRYPTION_KEY,
                ),
                session_string=decrypt_value(
                    encrypted_settings['telegram_session_string'],
                    settings.ENCRYPTION_KEY,
                ),
                user_id=user.id
            )
            await producer.run_job()
        except asyncio.CancelledError:
            logger.info(f"Telegram producer for user {user.id} cancelled")
            raise
        except Exception as e:
            logger.error(
                f"Telegram producer for user {user.id} failed: {e}",
                exc_info=True
            )

    async def _start_user_task(self, user: User) -> None:
        """Start a new task for a user."""
        if user.id not in self.user_tasks:
            task = asyncio.create_task(
                self._run_user_producer(user),
                name=f"telegram_user_{user.id}"
            )
            self.user_tasks[user.id] = task
            logger.info(f"Started Telegram task for user {user.id}")

    async def _stop_user_task(self, user_id: int) -> None:
        """Stop task for a user."""
        if user_id in self.user_tasks:
            task = self.user_tasks[user_id]
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=10.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

            del self.user_tasks[user_id]
            logger.info(f"Stopped Telegram task for user {user_id}")

    async def _sync_tasks(self) -> None:
        """Synchronize running tasks with active users."""
        try:
            active_users = await self._get_active_users()
            active_user_ids = {user.id for user in active_users}
            current_task_ids = set(self.user_tasks.keys())

            # Start new users
            for user in active_users:
                if user.id not in current_task_ids:
                    await self._start_user_task(user)

            # Stop removed users
            for user_id in current_task_ids - active_user_ids:
                await self._stop_user_task(user_id)

            # Clean up finished tasks
            for user_id, task in list(self.user_tasks.items()):
                if task.done():
                    logger.warning(
                        f"Task for user {user_id} finished unexpectedly"
                    )
                    del self.user_tasks[user_id]

            if active_users:
                logger.info(
                    f"Telegram manager: {len(self.user_tasks)} active tasks"
                )

        except Exception as e:
            logger.error(f"Error syncing Telegram tasks: {e}", exc_info=True)

    async def run(self) -> None:
        """Run the manager - checks for new users every interval."""
        self.running = True
        logger.info(
            f"Starting Telegram manager (interval: {self.check_interval}s)"
        )

        try:
            while self.running:
                await self._sync_tasks()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Telegram manager cancelled, cleaning up...")
            for user_id in list(self.user_tasks.keys()):
                await self._stop_user_task(user_id)
            raise


async def telegram_manager_job(check_interval_seconds: int = 300):
    """Entry point for Telegram manager."""
    manager = TelegramManager(check_interval_seconds=check_interval_seconds)
    await manager.run()
