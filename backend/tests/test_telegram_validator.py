"""Tests for Telegram channel validation."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from telethon.errors import (
    UsernameInvalidError,
    UsernameNotOccupiedError,
    ChannelPrivateError,
    FloodWaitError,
)

from app.validators.telegram import (
    validate_telegram_channel,
    TelegramValidationError
)


@pytest.fixture(autouse=True)
def mock_string_session():
    """Mock StringSession to avoid validation - auto-applied to all tests."""
    with patch('app.validators.telegram.StringSession') as mock:
        mock.return_value = Mock()
        yield mock


@pytest.mark.asyncio
async def test_validate_telegram_channel_success():
    """Test successful channel validation."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:

        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        # Mock entity (channel)
        mock_entity = Mock()
        mock_entity.broadcast = True  # It's a channel
        mock_entity.title = "Test Channel"
        mock_client.get_entity = AsyncMock(return_value=mock_entity)

        result = await validate_telegram_channel(
            channel="testchannel",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is True
        assert result["channel_id"] == "testchannel"
        assert result["title"] == "Test Channel"
        assert result["error"] is None

        # Verify client was properly closed
        mock_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_validate_telegram_channel_with_at_symbol():
    """Test channel validation with @ prefix."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        mock_entity = Mock()
        mock_entity.broadcast = True
        mock_entity.title = "Test Channel"
        mock_client.get_entity = AsyncMock(return_value=mock_entity)

        result = await validate_telegram_channel(
            channel="@testchannel",  # With @ prefix
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        # Should normalize by removing @
        assert result["channel_id"] == "testchannel"
        mock_client.get_entity.assert_called_with("testchannel")


@pytest.mark.asyncio
async def test_validate_telegram_channel_not_found():
    """Test validation when channel doesn't exist."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        mock_client.get_entity = AsyncMock(
            side_effect=UsernameNotOccupiedError("request")
        )

        result = await validate_telegram_channel(
            channel="nonexistent",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is False
        assert result["channel_id"] == "nonexistent"
        assert result["title"] is None
        assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_invalid_username():
    """Test validation with invalid username format."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        mock_client.get_entity = AsyncMock(
            side_effect=UsernameInvalidError("request")
        )

        result = await validate_telegram_channel(
            channel="inv@lid",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is False
        assert "invalid" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_private():
    """Test validation when channel is private."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        mock_client.get_entity = AsyncMock(
            side_effect=ChannelPrivateError("request")
        )

        result = await validate_telegram_channel(
            channel="privatechannel",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is False
        assert "private" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_rate_limited():
    """Test validation when rate limited."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        flood_error = FloodWaitError("request", 60)
        mock_client.get_entity = AsyncMock(side_effect=flood_error)

        result = await validate_telegram_channel(
            channel="testchannel",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is False
        assert "60" in result["error"]
        assert "rate" in result["error"].lower() or "again" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_not_broadcast():
    """Test validation when entity is not a broadcast channel."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        # Mock entity without broadcast attribute (e.g., a user or group)
        mock_entity = Mock(spec=[])  # No broadcast attribute
        mock_client.get_entity = AsyncMock(return_value=mock_entity)

        result = await validate_telegram_channel(
            channel="notachannel",
            api_id="12345",
            api_hash="test_hash",
            session_string="test_session"
        )

        assert result["valid"] is False
        assert "not a channel" in result["error"].lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_not_authorized():
    """Test validation when client is not authorized."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        with pytest.raises(TelegramValidationError) as exc_info:
            await validate_telegram_channel(
                channel="testchannel",
                api_id="12345",
                api_hash="test_hash",
                session_string="test_session"
            )

        assert "not authorized" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_telegram_channel_connection_error():
    """Test validation when connection fails."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client.is_connected = Mock(return_value=False)
        mock_client.disconnect = AsyncMock()

        with pytest.raises(TelegramValidationError):
            await validate_telegram_channel(
                channel="testchannel",
                api_id="12345",
                api_hash="test_hash",
                session_string="test_session"
            )


@pytest.mark.asyncio
async def test_validate_telegram_channel_cleanup_on_error():
    """Test that client is disconnected even when error occurs."""
    with patch('app.validators.telegram.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.is_connected = Mock(return_value=True)
        mock_client.disconnect = AsyncMock()

        mock_client.get_entity = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(TelegramValidationError):
            await validate_telegram_channel(
                channel="testchannel",
                api_id="12345",
                api_hash="test_hash",
                session_string="test_session"
            )

        # Client should be disconnected even on error
        mock_client.disconnect.assert_called_once()
