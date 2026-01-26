"""Telegram channel producer for fetching messages."""

from typing import List, Optional

from telethon import TelegramClient
from telethon.tl.types import Message

from app.models.source import Source
from app.models.news_item import NewsItem
from .base import BaseProducer


class TelegramProducer(BaseProducer):
    """Producer for Telegram channels."""

    def __init__(
        self,
        session,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None
    ):
        """Initialize Telegram producer.

        Args:
            session: SQLAlchemy async session
            api_id: Telegram API ID (optional)
            api_hash: Telegram API hash (optional)
        """
        super().__init__(session)
        self.api_id = api_id
        self.api_hash = api_hash
        self._client: Optional[TelegramClient] = None

    async def fetch(self, source: Source) -> List[NewsItem]:
        """Fetch messages from Telegram channel.

        Args:
            source: Source with channel ID/username in source field

        Returns:
            List of NewsItem instances
        """
        items = []

        try:
            # Get Telegram session string from user settings
            session_string = await self._get_session_string(source)

            if not session_string:
                self.logger.error(
                    f"No Telegram session string for {source.name}"
                )
                return []

            # Initialize client
            client = await self._get_client(session_string)

            # Fetch recent messages
            channel = source.source
            self.logger.debug(
                f"Fetching messages from channel: {channel}"
            )

            messages = await client.get_messages(channel, limit=100)

            # Process messages
            for message in messages:
                try:
                    item = self._parse_message(source, message)
                    if item:
                        items.append(item)
                except Exception as e:
                    self.logger.error(
                        f"Error parsing message from {source.name}: {e}",
                        exc_info=True
                    )
                    continue

            self.logger.info(
                f"Fetched {len(items)} messages from "
                f"Telegram channel {source.name}"
            )

        except Exception as e:
            self.logger.error(
                f"Error fetching Telegram messages from "
                f"{source.name}: {e}",
                exc_info=True
            )
            return []

        return items

    async def _get_session_string(
        self, source: Source
    ) -> Optional[str]:
        """Get Telegram session string from user settings.

        Args:
            source: Source model instance

        Returns:
            Session string or None
        """
        # Load user relationship if not loaded
        if not source.user:
            from sqlalchemy import select
            from app.models.user import User

            stmt = select(User).where(User.id == source.user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            source.user = user

        # Extract session string from user settings
        settings = source.user.settings or {}
        return settings.get("telegram_session")

    async def _get_client(
        self, session_string: str
    ) -> TelegramClient:
        """Get or create Telegram client.

        Args:
            session_string: Telegram session string

        Returns:
            Initialized TelegramClient
        """
        if not self._client or not self._client.is_connected():
            self._client = TelegramClient(
                session_string,
                self.api_id or "YOUR_API_ID",
                self.api_hash or "YOUR_API_HASH"
            )
            await self._client.start()

        return self._client

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

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnect client."""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
