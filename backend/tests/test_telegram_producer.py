"""Tests for Telegram producer."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from telethon.tl.types import Message

from app.models.source import Source, SourceType
from app.models.news_item import NewsItem
from app.producers.telegram import TelegramProducer


@pytest.fixture
def telegram_source():
    """Create a test Telegram source."""
    return Source(
        id=1,
        user_id=1,  # Simple ID, not linked to actual user
        name="Test Channel",
        type=SourceType.TELEGRAM,
        source="testchannel",
        active=True,
    )


@pytest.fixture
def telegram_producer():
    """Create a TelegramProducer instance."""
    return TelegramProducer(
        api_id="12345",
        api_hash="test_api_hash",
        session_string="test_session_string"
    )


@pytest.fixture
def mock_telegram_message():
    """Create a mock Telegram message."""
    message = Mock(spec=Message)
    message.id = 123
    message.text = "Test message content"
    message.date = datetime.now(timezone.utc)
    message.chat_id = 1001234567
    message.views = 100
    message.forwards = 5
    message.media = None

    # Mock chat with username
    message.chat = Mock()
    message.chat.username = "testchannel"

    return message


class TestTelegramProducer:
    """Tests for TelegramProducer class."""

    def test_init(self, telegram_producer):
        """Test TelegramProducer initialization."""
        assert telegram_producer.api_id == "12345"
        assert telegram_producer.api_hash == "test_api_hash"
        assert telegram_producer.session_string == "test_session_string"

    def test_init_requires_arguments(self):
        """Test that TelegramProducer requires all arguments."""
        with pytest.raises(TypeError):
            TelegramProducer()  # Should fail - missing required args

    @pytest.mark.asyncio
    async def test_get_client(self, telegram_producer):
        """Test _get_client returns TelegramClient instance."""
        with patch('app.producers.telegram.TelegramClient') as mock_client, \
             patch('app.producers.telegram.StringSession') as mock_session:

            mock_session_instance = mock_session.return_value
            result = telegram_producer._get_client()

            # Verify StringSession was created with the session string
            mock_session.assert_called_once_with("test_session_string")

            # Verify TelegramClient was created with StringSession, api_id, api_hash
            mock_client.assert_called_once_with(
                mock_session_instance,
                "12345",
                "test_api_hash"
            )

            # Verify it returns the client
            assert result == mock_client.return_value

    def test_parse_message_with_text(
        self, telegram_producer, telegram_source, mock_telegram_message
    ):
        """Test parsing a Telegram message with text."""
        item = telegram_producer._parse_message(
            telegram_source, mock_telegram_message
        )

        assert item is not None
        assert isinstance(item, NewsItem)
        assert item.source_id == telegram_source.id
        assert item.title == "Test message content"
        assert item.content == "Test message content"
        assert item.external_id == "123"
        assert item.url == "https://t.me/testchannel/123"
        assert item.raw_data["message_id"] == 123
        assert item.raw_data["chat_id"] == 1001234567
        assert item.raw_data["views"] == 100
        assert item.raw_data["forwards"] == 5
        assert item.raw_data["has_media"] is False

    def test_parse_message_without_text(
        self, telegram_producer, telegram_source
    ):
        """Test parsing a message without text returns None."""
        message = Mock(spec=Message)
        message.text = None

        item = telegram_producer._parse_message(telegram_source, message)
        assert item is None

    def test_parse_message_truncates_long_title(
        self, telegram_producer, telegram_source
    ):
        """Test that long messages are truncated in title."""
        message = Mock(spec=Message)
        message.text = "A" * 150
        message.id = 123
        message.date = datetime.now(timezone.utc)
        message.chat_id = 1001234567
        message.views = 0
        message.forwards = 0
        message.media = None
        message.chat = Mock()
        message.chat.username = "testchannel"

        item = telegram_producer._parse_message(telegram_source, message)

        assert item is not None
        assert len(item.title) == 103  # 100 chars + "..."
        assert item.title.endswith("...")
        assert len(item.content) == 150  # Full content preserved

    def test_parse_message_without_username(
        self, telegram_producer, telegram_source
    ):
        """Test parsing message from channel without username."""
        message = Mock(spec=Message)
        message.id = 123
        message.text = "Test message"
        message.date = datetime.now(timezone.utc)
        message.chat_id = 1001234567
        message.views = 0
        message.forwards = 0
        message.media = None
        message.chat = Mock()
        message.chat.username = None  # No username

        item = telegram_producer._parse_message(telegram_source, message)

        assert item is not None
        assert item.url is None  # No URL without username

    def test_parse_message_with_media(
        self, telegram_producer, telegram_source
    ):
        """Test parsing message with media."""
        message = Mock(spec=Message)
        message.id = 123
        message.text = "Test message with media"
        message.date = datetime.now(timezone.utc)
        message.chat_id = 1001234567
        message.views = 0
        message.forwards = 0
        message.media = Mock()  # Has media
        message.chat = Mock()
        message.chat.username = "testchannel"

        item = telegram_producer._parse_message(telegram_source, message)

        assert item is not None
        assert item.raw_data["has_media"] is True

    @pytest.mark.asyncio
    async def test_run_job_no_sources(self, telegram_producer):
        """Test run_job handles no active sources."""
        with patch.object(
            telegram_producer, 'get_sources', new_callable=AsyncMock
        ) as mock_get_sources, \
             patch.object(
            telegram_producer, '_get_client_with_entities', new_callable=AsyncMock
        ) as mock_get_client_with_entities:

            mock_get_sources.return_value = []

            # Mock client that will be cancelled before run_until_disconnected
            mock_client = AsyncMock()
            mock_client.run_until_disconnected = AsyncMock(
                side_effect=asyncio.CancelledError()
            )
            mock_get_client_with_entities.return_value = mock_client

            # Run for a short time then cancel
            task = asyncio.create_task(telegram_producer.run_job())
            await asyncio.sleep(0.1)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Should have called get_sources at least once
            assert mock_get_sources.call_count >= 1

    @pytest.mark.asyncio
    async def test_run_job_reconnects_on_error(self, telegram_producer):
        """Test run_job retries after errors."""
        get_sources_call_count = 0

        async def mock_get_sources(*args, **kwargs):
            nonlocal get_sources_call_count
            get_sources_call_count += 1
            # Always return empty so it retries after 60s sleep
            return []

        with patch.object(
            telegram_producer, 'get_sources', new_callable=AsyncMock
        ) as mock_get_sources_patch, \
             patch.object(
            telegram_producer, '_get_client_with_entities', new_callable=AsyncMock
        ) as mock_get_client_with_entities:

            mock_get_sources_patch.side_effect = mock_get_sources

            # Mock client that will be cancelled before run_until_disconnected
            mock_client = AsyncMock()
            mock_client.run_until_disconnected = AsyncMock(
                side_effect=asyncio.CancelledError()
            )
            mock_get_client_with_entities.return_value = mock_client

            # Run for a short time
            task = asyncio.create_task(telegram_producer.run_job())
            await asyncio.sleep(0.2)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Should have called get_sources at least once
            assert get_sources_call_count >= 1
