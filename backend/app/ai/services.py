"""Service boundaries for AI consumer pipeline."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.types import (
    EvaluationOutcome,
    NotificationTarget,
    PersistResult,
    QueuedNewsPayload,
    TaskContext,
    TaskRunStats,
    UserProcessingContext,
)
from app.models.news_item import NewsItem
from app.models.news_item_news_task import NewsItemNewsTask
from app.models.news_task import NewsTask
from app.models.source_news_task import SourceNewsTask
from app.models.telegram_bot import TelegramBot
from app.models.telegram_bot_news_task import TelegramBotNewsTask
from app.models.user import User
from app.models.utils import utcnow_naive

logger = logging.getLogger(__name__)


class TaskSelectionService:
    """Read-focused selectors for user/task/news pipeline."""

    async def get_active_user_ids(self, db: AsyncSession) -> list[int]:
        stmt = select(User.id).where(User.is_active.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def load_user_context(
        self, db: AsyncSession, user_id: int
    ) -> UserProcessingContext | None:
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            return None

        tasks_stmt = select(NewsTask).where(
            and_(NewsTask.user_id == user_id, NewsTask.active.is_(True))
        )
        tasks_result = await db.execute(tasks_stmt)
        tasks = list(tasks_result.scalars().all())

        task_contexts = [
            TaskContext(
                task_id=task.id,
                user_id=task.user_id,
                name=task.name,
                prompt=task.prompt,
            )
            for task in tasks
        ]

        return UserProcessingContext(
            user_id=user.id,
            email=user.email,
            settings=dict(user.settings or {}),
            tasks=task_contexts,
        )

    async def get_queued_news_for_task(
        self,
        db: AsyncSession,
        task: TaskContext,
        max_age_hours: int = 4,
    ) -> list[QueuedNewsPayload]:
        cutoff_time = utcnow_naive() - timedelta(hours=max_age_hours)
        stmt = (
            select(NewsItem)
            .join(
                SourceNewsTask, NewsItem.source_id == SourceNewsTask.source_id
            )
            .outerjoin(
                NewsItemNewsTask,
                and_(
                    NewsItemNewsTask.news_item_id == NewsItem.id,
                    NewsItemNewsTask.news_task_id == task.task_id,
                ),
            )
            .where(
                and_(
                    SourceNewsTask.news_task_id == task.task_id,
                    NewsItem.published_at >= cutoff_time,
                    or_(
                        NewsItemNewsTask.news_item_id.is_(None),
                        NewsItemNewsTask.processed.is_(False),
                    ),
                )
            )
            .distinct(NewsItem.id)
        )
        result = await db.execute(stmt)
        news_items = list(result.scalars().all())
        return [
            QueuedNewsPayload(
                news_item_id=item.id,
                task_id=task.task_id,
                source_id=item.source_id,
                title=item.title,
                content=item.content,
                url=item.url,
                published_at=item.published_at,
            )
            for item in news_items
        ]


class TaskResultService:
    """Write-focused persistence for evaluation outcomes."""

    async def persist_task_outcomes(
        self,
        db: AsyncSession,
        outcomes: list[EvaluationOutcome],
    ) -> PersistResult:
        successful = [o for o in outcomes if o.result is not None]
        if not successful:
            return PersistResult(
                stats=TaskRunStats(queued=len(outcomes), errors=len(outcomes)),
                successful=[],
                matched=[],
            )

        now = utcnow_naive()
        keys = {(o.news_item_id, o.task_id) for o in successful}
        news_item_ids = [key[0] for key in keys]
        task_ids = [key[1] for key in keys]

        existing_stmt = select(NewsItemNewsTask).where(
            NewsItemNewsTask.news_item_id.in_(news_item_ids),
            NewsItemNewsTask.news_task_id.in_(task_ids),
        )
        existing_result = await db.execute(existing_stmt)
        existing_records = {
            (record.news_item_id, record.news_task_id): record
            for record in existing_result.scalars().all()
        }

        matched: list[EvaluationOutcome] = []
        for outcome in successful:
            result = outcome.result
            if result is None:
                continue

            key = (outcome.news_item_id, outcome.task_id)
            ai_response = {
                "thinking": result.thinking,
                "tokens_used": result.tokens_used,
                "processed_at": now.isoformat(),
            }
            record = existing_records.get(key)
            if record:
                record.processed = True
                record.result = result.result
                record.processed_at = now
                record.ai_response = ai_response
            else:
                db.add(
                    NewsItemNewsTask(
                        news_item_id=outcome.news_item_id,
                        news_task_id=outcome.task_id,
                        processed=True,
                        result=result.result,
                        processed_at=now,
                        ai_response=ai_response,
                    )
                )

            if result.result:
                matched.append(outcome)

        await db.commit()

        processed = len(successful)
        matched_count = len(matched)
        rejected = sum(
            1 for o in successful if o.result and not o.result.result
        )
        errors = len(outcomes) - processed

        return PersistResult(
            stats=TaskRunStats(
                queued=len(outcomes),
                processed=processed,
                matched=matched_count,
                rejected=rejected,
                errors=errors,
            ),
            successful=successful,
            matched=matched,
        )


class NotificationService:
    """Facade for task-bot mapping and Telegram dispatch."""

    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)

    async def get_task_bot_ids(
        self, db: AsyncSession, task_id: int
    ) -> list[int]:
        stmt = select(TelegramBotNewsTask.telegram_bot_id).where(
            TelegramBotNewsTask.news_task_id == task_id
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_notification_targets(
        self, db: AsyncSession, user_id: int, task_id: int
    ) -> list[NotificationTarget]:
        bot_ids = await self.get_task_bot_ids(db, task_id)
        if not bot_ids:
            return []

        stmt = select(TelegramBot).where(
            TelegramBot.id.in_(bot_ids),
            TelegramBot.user_id == user_id,
            TelegramBot.is_active.is_(True),
        )
        result = await db.execute(stmt)
        bots = list(result.scalars().all())
        targets: list[NotificationTarget] = []
        for bot in bots:
            if not bot.bot_token:
                continue
            for chat in bot.chats or []:
                if chat.get("task_id") != task_id:
                    continue
                chat_id = str(chat.get("chat_id") or "")
                if not chat_id:
                    continue
                targets.append(
                    NotificationTarget(
                        encrypted_bot_token=bot.bot_token,
                        chat_id=chat_id,
                    )
                )
        return targets
