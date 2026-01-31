"""Base producer class for all news sources."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.models.source import Source
from app.models.news_item import NewsItem
from app.models.news_task import NewsTask
from app.models.source_news_task import SourceNewsTask
from app.db import get_async_session

logger = logging.getLogger(__name__)


class BaseProducer(ABC):
    """Abstract base class for news producers."""

    def __init__(self):
        """Initialize producer with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    async def fetch(self, source: Source) -> List[NewsItem]:
        """Fetch news items from the source.

        Args:
            source: Source model instance

        Returns:
            List of NewsItem instances (not yet persisted)

        Raises:
            Exception: Any errors should be caught and logged
        """
        pass

    async def process_source(self, source: Source) -> int:
        """Process a source - fetch, deduplicate, and store items.

        Args:
            source: Source model instance

        Returns:
            Number of new items stored
        """
        try:
            self.logger.info(
                f"Processing source: {source.name} (ID: {source.id})"
            )

            # Fetch items
            items = await self.fetch(source)
            self.logger.debug(
                f"Fetched {len(items)} items from {source.name}"
            )
        except Exception as e:
            self.logger.error(
                f"Error fetching items from source {source.name}: {e}",
                exc_info=True
            )
            return 0

        # Deduplicate and store
        new_items = 0
        async for session in get_async_session():
            try:
                for item in items:
                    if await self._is_duplicate(item, session):
                        self.logger.debug(
                            f"Skipping duplicate item: {item.title}"
                        )
                        continue
                    session.add(item)
                    new_items += 1

                # Update source last_fetched_at
                source.last_fetched_at = datetime.now(
                    timezone.utc
                ).replace(tzinfo=None)
                session.add(source)

                # Commit all changes
                await session.commit()

                self.logger.info(
                    f"Stored {new_items} new items from {source.name}"
                )
                return new_items

            except Exception as e:
                self.logger.error(
                    f"Error processing source {source.name}: {e}",
                    exc_info=True
                )
                await session.rollback()
                return 0

    async def _is_duplicate(
        self,
        item: NewsItem,
        session: AsyncSession,
    ) -> bool:
        """Check if news item already exists in database.

        Args:
            item: NewsItem to check

        Returns:
            True if duplicate exists, False otherwise
        """
        # Check by URL if available
        if item.url:
            stmt = select(NewsItem).where(
                NewsItem.url == item.url,
                NewsItem.source_id == item.source_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return True

        # Check by external_id and source_id combination
        if item.external_id:
            stmt = select(NewsItem).where(
                NewsItem.external_id == item.external_id,
                NewsItem.source_id == item.source_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return True

        return False

    def _create_news_item(
        self,
        source_id: UUID | int,
        title: str,
        content: str,
        url: Optional[str] = None,
        external_id: Optional[str] = None,
        published_at: Optional[datetime] = None,
        settings: Optional[Dict[str, Any]] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> NewsItem:
        """Helper method to create NewsItem instance.

        Args:
            source_id: ID of the source
            title: Item title
            content: Item content
            url: Item URL (optional)
            external_id: External identifier (optional)
            published_at: Publication datetime (optional)
            settings: Item-specific settings (optional)
            raw_data: Raw data from source (optional)

        Returns:
            NewsItem instance
        """
        # Strip timezone info for database (uses TIMESTAMP WITHOUT TIME ZONE)
        published = published_at or datetime.now(timezone.utc)
        if published.tzinfo is not None:
            published = published.replace(tzinfo=None)

        fetched = datetime.now(timezone.utc).replace(tzinfo=None)

        return NewsItem(
            source_id=source_id,
            title=title,
            content=content,
            url=url,
            external_id=external_id,
            published_at=published,
            fetched_at=fetched,
            processed=False,
            settings=settings or {},
            raw_data=raw_data or {},
        )

    async def get_sources(
        self,
        source_type: str,
        session: AsyncSession
    ) -> List[Source]:
        stmt = (
            select(Source)
            .join(SourceNewsTask, SourceNewsTask.source_id == Source.id)
            .join(NewsTask, SourceNewsTask.news_task_id == NewsTask.id)
            .where(
                Source.type == source_type,
                Source.active.is_(True),
                NewsTask.active.is_(True)
            )
            .distinct()
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def run_job(
        self,
        source_type: str,
        concurrency_limit: int = 5
    ) -> None:
        """Run producer job for all active sources of given type.

        Args:
            source_type: Type of sources to process
            concurrency_limit: Maximum concurrent source processing

        """
        self.logger.info(f"Starting {source_type} producer job")

        # Fetch active sources
        sources: list[Source] = []
        async for session in get_async_session():
            try:
                sources = await self.get_sources(
                    source_type=source_type,
                    session=session
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to fetch sources: {e}", exc_info=True
                )
                await session.rollback()
            finally:
                break

        if not sources:
            self.logger.info(f"No active {source_type} sources to process")
            return

        self.logger.info(f"Processing {len(sources)} {source_type} sources")

        # Process sources concurrently
        semaphore = asyncio.Semaphore(concurrency_limit)
        results = await asyncio.gather(
            *[self.process_source_safe(s, semaphore) for s in sources]
        )
        total_items = sum(results)
        self.logger.info(
            f"{source_type} job complete: {len(sources)} sources, "
            f"{total_items} new items"
        )

    async def process_source_safe(
        self,
        source: Source,
        semaphore: asyncio.Semaphore
    ) -> int:
        """Process source with semaphore and error handling.

        Args:
            source: Source to process
            semaphore: Asyncio semaphore for concurrency control

        """
        async with semaphore:
            try:
                return await self.process_source(source)
            except Exception as e:
                self.logger.error(
                    f"Error processing {source.name}: {e}",
                    exc_info=True
                )
                return 0
