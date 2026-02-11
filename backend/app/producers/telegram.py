"""Telegram channel producer for fetching messages."""

from typing import Optional
import asyncio

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Message

from app.models.source import Source, SourceType
from app.models.news_item import NewsItem
from .base import BaseProducer
from app.db.database import get_async_session


class TelegramProducer(BaseProducer):
    """Producer for Telegram channels."""

    def __init__(
        self,
        api_id: str,
        api_hash: str,
        session_string: str
    ):
        """Initialize Telegram producer.

        Args:
            api_id: Telegram API ID (required)
            api_hash: Telegram API hash (required)
            session_string: Telegram session string (required)
        """
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.sources = []

    async def fetch(self, source: Source) -> list[NewsItem]:
        """Fetch method not used - Telegram uses event-driven approach.

        This method exists to satisfy the BaseProducer abstract interface,
        but is not called. Use run_job() for event-driven message collection.

        Args:
            source: Source model instance

        Returns:
            Empty list (not implemented)
        """
        self.logger.warning(
            "fetch() is not implemented for Telegram - use run_job() instead"
        )
        return []

    async def _resolve_entities(self, client: TelegramClient) -> list:
        """Resolve Telegram channel/chat entities from source strings.

        Args:
            client: Connected TelegramClient instance

        Returns:
            List of resolved Telegram entities
        """
        entities = []
        async with client:
            for source in self.sources:
                entity = await client.get_entity(source.source)
                entities.append(entity)
        if not entities:
            self.logger.warning("No entities could be resolved")

        return entities

    def _get_client(self) -> TelegramClient:
        """Get Telegram client instance.

        Returns:
            TelegramClient instance (not connected)
        """
        return TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash
        )

    async def _get_client_with_entities(self) -> TelegramClient:
        """Get Telegram client (not started).

        Returns:
            TelegramClient instance (not connected)
        """
        client = self._get_client()
        entities = await self._resolve_entities(client)
        self.logger.info(f"Adding event handlers for {len(entities)} entities")
        client.add_event_handler(
            self._handle_new_message,
            events.NewMessage(
                chats=entities,
                forwards=False,
            )
        )
        return client

    def _parse_message(
        self, source: Source, message: Message
    ) -> Optional[NewsItem]:
        """Parse Telegram message into NewsItem.

        Args:
            source: Source model instance
            message: Telegram message object

        Returns:
            NewsItem instance or None
        """
        # Skip messages without text
        if not message.text:
            return None

        # Use message text as both title and content
        text = message.text.strip()
        title = text[:100] + ("..." if len(text) > 100 else "")
        content = text

        # Message ID as external identifier
        external_id = str(message.id)

        # Message link (if available)
        url = None
        if (message.chat and hasattr(message.chat, "username")
                and message.chat.username):
            url = f"https://t.me/{message.chat.username}/{message.id}"

        # Published date
        published_at = message.date

        # Raw data
        raw_data = {
            "message_id": message.id,
            "chat_id": message.chat_id if message.chat_id else None,
            "views": message.views,
            "forwards": message.forwards,
            "has_media": bool(message.media),
        }

        return self._create_news_item(
            source_id=source.id,
            title=title,
            content=content,
            url=url,
            external_id=external_id,
            published_at=published_at,
            raw_data=raw_data,
        )

    async def test_handler(self, event: events.NewMessage.Event) -> None:
        """Test handler to log incoming messages without processing."""
        self.logger.info(
            f"Received message in test handler from {event.chat.username}: "
            f"{event.message.text[:50]}..."
        )

    async def _handle_new_message(
        self,
        event: events.NewMessage.Event
    ) -> None:
        """Handle new Telegram message event."""
        self.logger.info(
            f"Received new message from {event.chat.username}: "
            f"{event.message.text[:50]}..."
        )
        matching_source = None
        for source in self.sources:
            if source.source == event.chat.username:
                matching_source = source
                break
        if not matching_source:
            self.logger.debug(
                f"Received message from {event.chat.username} "
                f"which does not match any active source"
            )
            return
        item = self._parse_message(
            source=matching_source,
            message=event.message
        )
        if not item:
            self.logger.debug(
                f"Parsed message from {event.chat.username} "
                f"but it did not contain valid content"
            )
            return
        async for session in get_async_session():
            try:
                if not await self._is_duplicate(item, session):
                    session.add(item)
                    await session.commit()
                    self.logger.info(
                        f"✓ New message from {matching_source.name}: "
                        f"{item.title}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error storing message: {e}", exc_info=True
                )
                await session.rollback()
            finally:
                break

    async def run_job(self) -> None:
        """Run Telegram producer job - watch for updates continuously.

        This method runs indefinitely, watching for updates from all active
        Telegram sources.
        """

        while True:
            try:
                self.sources = await self.get_sources(
                    source_type=SourceType.TELEGRAM
                )
                client = await self._get_client_with_entities()
                if not client:
                    self.logger.warning(
                        "No Telegram client available - retrying in 1 minute"
                    )
                    await asyncio.sleep(60)
                    continue

                self.logger.info(
                    f"Starting Telegram client for {len(self.sources)} sources"
                )
                async with client:
                    await asyncio.wait_for(
                            client.run_until_disconnected(),
                            timeout=20,
                        )
            except asyncio.TimeoutError:
                self.logger.warning(
                    "Restarting Telegram client..."
                )
            except Exception as e:
                self.logger.error(
                    f"Telegram producer error: {e}", exc_info=True
                )
                await asyncio.sleep(60)


async def telegram_producer_job(
    api_id: str,
    api_hash: str,
    session_string: str
):
    """Job to watch Telegram channels for new messages.

    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_string: Telegram session string
    """
    producer = TelegramProducer(
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string
    )
    await producer.run_job()
