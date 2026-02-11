"""Telegram channel validation utilities."""

import logging

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import (
    UsernameInvalidError,
    UsernameNotOccupiedError,
    ChannelPrivateError,
    FloodWaitError,
)

logger = logging.getLogger(__name__)


class TelegramValidationError(Exception):
    """Custom exception for Telegram validation errors."""
    pass


async def validate_telegram_channel(
    channel: str,
    api_id: str,
    api_hash: str,
    session_string: str
) -> dict:
    """Validate if a Telegram channel exists and is accessible.

    Args:
        channel: Channel username (with or without @) or numeric ID
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_string: Telegram session string

    Returns:
        dict with keys:
            - valid: bool - Whether channel is valid and accessible
            - channel_id: str - Normalized channel identifier
            - title: str - Channel title (if accessible)
            - error: str - Error message (if not valid)

    Raises:
        TelegramValidationError: If validation cannot be performed
    """
    # Normalize channel identifier
    normalized_channel = channel.strip()
    if normalized_channel.startswith('@'):
        normalized_channel = normalized_channel[1:]

    client = None
    try:
        # Create and connect client
        client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash
        )
        await client.connect()

        if not await client.is_user_authorized():
            raise TelegramValidationError(
                "Telegram client not authorized. Please check session string."
            )

        # Try to get the entity (channel)
        try:
            entity = await client.get_entity(normalized_channel)

            # Check if it's actually a channel (not a user or group)
            if not hasattr(entity, 'broadcast'):
                return {
                    "valid": False,
                    "channel_id": normalized_channel,
                    "title": None,
                    "error": "This is not a channel."
                }

            # Successfully found the channel
            return {
                "valid": True,
                "channel_id": normalized_channel,
                "title": entity.title if hasattr(entity, 'title') else None,
                "error": None
            }

        except UsernameInvalidError:
            return {
                "valid": False,
                "channel_id": normalized_channel,
                "title": None,
                "error": "Invalid channel username format."
            }
        except UsernameNotOccupiedError:
            return {
                "valid": False,
                "channel_id": normalized_channel,
                "title": None,
                "error": "Channel not found. This username is not occupied."
            }
        except ChannelPrivateError:
            return {
                "valid": False,
                "channel_id": normalized_channel,
                "title": None,
                "error": "Channel is private. You must join it first."
            }
        except FloodWaitError as e:
            return {
                "valid": False,
                "channel_id": normalized_channel,
                "title": None,
                "error": (
                    f"Rate limited. Please try again in {e.seconds} "
                    "seconds."
                ),
            }
        except ValueError as e:
            # Numeric ID but invalid format
            return {
                "valid": False,
                "channel_id": normalized_channel,
                "title": None,
                "error": f"Invalid channel identifier: {str(e)}"
            }

    except TelegramValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error validating Telegram channel: {e}",
            exc_info=True,
        )
        raise TelegramValidationError(
            f"Failed to validate channel: {str(e)}"
        )
    finally:
        if client and client.is_connected():
            await client.disconnect()


async def subscribe_to_validated_channel(
    client: TelegramClient,
    channel: str
):
    """Subscribe to a validated Telegram channel.

    Args:
        client: An authorized TelegramClient instance

    Raises:
        TelegramValidationError: If subscription fails
    """
    try:
        async with client:
            await client(JoinChannelRequest(channel))
            logger.info(f"✓ Joined channel: {channel}")
    except Exception as e:
        logger.error(
            f"Error subscribing to Telegram channel: {e}",
            exc_info=True,
        )
        raise TelegramValidationError(
            f"Failed to subscribe to channel: {str(e)}"
        )
