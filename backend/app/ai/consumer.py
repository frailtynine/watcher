"""AI consumer for processing news items."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import GeminiClient
from app.models.news_item import NewsItem
from app.models.news_task import NewsTask
from app.models.news_item_news_task import NewsItemNewsTask
from app.models.source_news_task import SourceNewsTask
from app.models.user import User
from app.models.utils import utcnow_naive

logger = logging.getLogger(__name__)


class AIConsumer:
    """Consumer for processing news items with AI."""

    def __init__(self):
        """Initialize AI consumer."""
        self.logger = logger.getChild(self.__class__.__name__)

    async def process_user_news(
        self,
        db: AsyncSession,
        user: User
    ) -> dict:
        """Process all unprocessed news for a user's active tasks.

        Args:
            db: Database session
            user: User instance

        Returns:
            Dict with processing statistics
        """
        api_key = self._get_user_api_key(user)
        if not api_key:
            self.logger.warning(
                f"User {user.id} has no Gemini API key configured"
            )
            return {"processed": 0, "errors": 0}

        client = GeminiClient(api_key=api_key)
        tasks = await self._get_active_tasks(db, user.id)

        total_processed = 0
        total_errors = 0

        for task in tasks:
            stats = await self._process_task_news(db, client, task)
            total_processed += stats["processed"]
            total_errors += stats["errors"]

        return {
            "processed": total_processed,
            "errors": total_errors
        }

    async def _process_task_news(
        self,
        db: AsyncSession,
        client: GeminiClient,
        task: NewsTask
    ) -> dict:
        """Process unprocessed news items for a specific task.

        Args:
            db: Database session
            client: Gemini client
            task: NewsTask instance

        Returns:
            Dict with processing statistics
        """
        news_items = await self._get_unprocessed_news(db, task)
        processed = 0
        errors = 0

        for news_item in news_items:
            try:
                result = await client.process_news(
                    news_id=news_item.id,
                    title=news_item.title,
                    content=news_item.content,
                    prompt=task.prompt
                )

                await self._save_result(db, news_item.id, task.id, result)
                processed += 1

                self.logger.debug(
                    f"Processed news {news_item.id} with task {task.id}: "
                    f"result={result.result}"
                )

            except Exception as e:
                errors += 1
                self.logger.error(
                    f"Error processing news {news_item.id} "
                    f"with task {task.id}: {e}",
                    exc_info=True
                )

        return {"processed": processed, "errors": errors}

    async def _get_active_tasks(
        self,
        db: AsyncSession,
        user_id: int
    ) -> list[NewsTask]:
        """Get all active tasks for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of active NewsTask instances
        """
        stmt = select(NewsTask).where(
            and_(
                NewsTask.user_id == user_id,
                NewsTask.active.is_(True)
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _get_unprocessed_news(
        self,
        db: AsyncSession,
        task: NewsTask
    ) -> list[NewsItem]:
        """Get unprocessed news items for a task (< 4 hours old).

        Args:
            db: Database session
            task: NewsTask instance

        Returns:
            List of NewsItem instances
        """
        cutoff_time = utcnow_naive() - timedelta(hours=4)

        # Get sources linked to this task
        stmt = (
            select(NewsItem)
            .join(SourceNewsTask, NewsItem.source_id == SourceNewsTask.source_id)
            .outerjoin(
                NewsItemNewsTask,
                and_(
                    NewsItemNewsTask.news_item_id == NewsItem.id,
                    NewsItemNewsTask.news_task_id == task.id
                )
            )
            .where(
                and_(
                    SourceNewsTask.news_task_id == task.id,
                    NewsItem.published_at >= cutoff_time,
                    or_(
                        NewsItemNewsTask.news_item_id.is_(None),
                        NewsItemNewsTask.processed.is_(False)
                    )
                )
            )
            .distinct()
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _save_result(
        self,
        db: AsyncSession,
        news_item_id: int,
        news_task_id: int,
        result
    ) -> None:
        """Save processing result to database.

        Args:
            db: Database session
            news_item_id: NewsItem ID
            news_task_id: NewsTask ID
            result: ProcessingResult instance
        """
        # Check if record exists
        stmt = select(NewsItemNewsTask).where(
            and_(
                NewsItemNewsTask.news_item_id == news_item_id,
                NewsItemNewsTask.news_task_id == news_task_id
            )
        )
        existing = await db.execute(stmt)
        record = existing.scalar_one_or_none()

        ai_response = {
            "thinking": result.thinking,
            "tokens_used": result.tokens_used,
            "processed_at": utcnow_naive().isoformat()
        }

        if record:
            # Update existing record
            record.processed = True
            record.result = result.result
            record.processed_at = utcnow_naive()
            record.ai_response = ai_response
        else:
            # Create new record
            record = NewsItemNewsTask(
                news_item_id=news_item_id,
                news_task_id=news_task_id,
                processed=True,
                result=result.result,
                processed_at=utcnow_naive(),
                ai_response=ai_response
            )
            db.add(record)

        await db.commit()

    def _get_user_api_key(self, user: User) -> Optional[str]:
        """Extract Gemini API key from user settings.

        Args:
            user: User instance

        Returns:
            API key or None if not configured
        """
        if not user.settings:
            return None
        return user.settings.get("gemini_api_key")
