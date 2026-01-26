"""RSS feed producer for fetching news from RSS/Atom feeds."""

from datetime import datetime, timezone
from typing import List, Optional
import asyncio
import feedparser
from email.utils import parsedate_to_datetime

from sqlalchemy import select

from app.models.source import Source, SourceType
from app.models.news_item import NewsItem
from app.db import get_async_session
from app.core import settings
from .base import BaseProducer


class RSSProducer(BaseProducer):
    """Producer for RSS/Atom feeds."""

    async def fetch(self, source: Source) -> List[NewsItem]:
        """Fetch news items from RSS feed.

        Args:
            source: Source model instance with RSS URL in source field

        Returns:
            List of NewsItem instances
        """
        items = []

        try:
            self.logger.debug(f"Fetching RSS feed: {source.source}")

            # feedparser.parse is synchronous
            feed = await self._parse_feed(source.source)

            # Check for feed errors
            if feed.get("bozo", False):
                self.logger.warning(
                    f"Feed parsing error for {source.name}: "
                    f"{feed.get('bozo_exception')}"
                )

            # Process feed entries
            for entry in feed.get("entries", []):
                try:
                    item = self._parse_entry(source, entry)
                    if item:
                        items.append(item)
                except Exception as e:
                    self.logger.error(
                        f"Error parsing entry from {source.name}: {e}",
                        exc_info=True
                    )
                    continue

            self.logger.info(
                f"Fetched {len(items)} items from RSS feed {source.name}"
            )

        except Exception as e:
            self.logger.error(
                f"Error fetching RSS feed {source.name}: {e}",
                exc_info=True
            )
            return []

        return items

    async def _parse_feed(self, url: str) -> feedparser.FeedParserDict:
        """Parse RSS feed from URL.

        Args:
            url: Feed URL

        Returns:
            Parsed feed dictionary
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, feedparser.parse, url)

    def _parse_entry(
        self, source: Source, entry: dict
    ) -> Optional[NewsItem]:
        """Parse a single feed entry into NewsItem.

        Per RSS spec, required fields: title, link, description.
        If any are missing, skip the entry.

        Args:
            source: Source model instance
            entry: Feed entry dictionary

        Returns:
            NewsItem instance or None if entry cannot be parsed
        """
        # RSS required fields: title, link, description
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        description = entry.get("description", "").strip()

        # Skip if any required field is missing
        if not title or not url or not description:
            self.logger.debug(
                f"Skipping entry missing required fields - "
                f"title: {bool(title)}, link: {bool(url)}, "
                f"description: {bool(description)}"
            )
            return None

        # Extract published date
        published_at = self._parse_date(entry)

        # Use entry ID or URL as external_id
        external_id = entry.get("id") or url

        # Store minimal raw data
        raw_data = {
            "title": title,
            "link": url,
            "description": description,
            "published": entry.get("published") or entry.get("updated"),
        }

        return self._create_news_item(
            source_id=source.id,
            title=title,
            content=description,
            url=url,
            external_id=external_id,
            published_at=published_at,
            raw_data=raw_data,
        )

    def _parse_date(self, entry: dict) -> datetime:
        """Parse publication date from feed entry.

        Args:
            entry: Feed entry dictionary

        Returns:
            datetime object (defaults to current time if parsing fails)
        """
        # Try published_parsed first
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                import time
                return datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=timezone.utc
                )
            except Exception:
                pass

        # Try updated_parsed
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                import time
                return datetime.fromtimestamp(
                    time.mktime(entry.updated_parsed),
                    tz=timezone.utc
                )
            except Exception:
                pass

        # Try parsing published string
        if entry.get("published"):
            try:
                dt = parsedate_to_datetime(entry["published"])
                # Ensure timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass

        # Try parsing updated string
        if entry.get("updated"):
            try:
                dt = parsedate_to_datetime(entry["updated"])
                # Ensure timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass

        # Default to current time (UTC)
        return datetime.now(timezone.utc)


async def rss_producer_job():
    """Job to fetch news items from all active RSS sources."""
    producer = RSSProducer()
    producer.logger.info("Starting RSS producer job")

    # Fetch active RSS sources
    async for session in get_async_session():
        try:
            stmt = select(Source).where(
                Source.type == SourceType.RSS,
                Source.active.is_(True)
            )
            result = await session.execute(stmt)
            sources = list(result.scalars().all())
            break
        except Exception as e:
            producer.logger.error(
                f"Failed to fetch sources: {e}", exc_info=True
            )
            await session.rollback()
            return

    if not sources:
        producer.logger.info("No active RSS sources to process")
        return

    producer.logger.info(f"Processing {len(sources)} RSS sources")

    # Process sources concurrently with limit
    semaphore = asyncio.Semaphore(settings.RSS_FETCH_CONCURRENCY)

    async def process_source_safe(source: Source):
        """Process source with semaphore and error handling."""
        async with semaphore:
            try:
                return await producer.process_source(source)
            except Exception as e:
                producer.logger.error(
                    f"Error processing {source.name}: {e}",
                    exc_info=True
                )
                return 0

    # Execute and gather results
    results = await asyncio.gather(*[process_source_safe(s) for s in sources])
    total_items = sum(results)
    producer.logger.info(
        f"RSS job complete: {len(sources)} sources, {total_items} new items"
    )
