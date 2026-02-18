"""RSS feed validation utilities."""

import logging
import asyncio
from typing import Optional

import feedparser
import aiohttp

logger = logging.getLogger(__name__)


class RSSValidationError(Exception):
    """Custom exception for RSS validation errors."""
    pass


async def validate_rss_feed(url: str, timeout: int = 10) -> dict:
    """Validate if an RSS feed is valid and accessible.

    Args:
        url: Feed URL to validate
        timeout: Timeout for HTTP request in seconds

    Returns:
        dict with keys:
            - valid: bool - Whether feed is valid and accessible
            - url: str - The validated URL
            - title: str - Feed title (if accessible)
            - error: str - Error message (if not valid)

    Raises:
        RSSValidationError: If validation cannot be performed
    """
    if not url or not url.strip():
        return {
            "valid": False,
            "url": url,
            "title": None,
            "error": "URL cannot be empty"
        }

    url = url.strip()

    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return {
            "valid": False,
            "url": url,
            "title": None,
            "error": "URL must start with http:// or https://"
        }

    try:
        # Fetch the feed content with timeout
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        return {
                            "valid": False,
                            "url": url,
                            "title": None,
                            "error": (
                                f"HTTP error: status code {response.status}"
                            )
                        }

                    content = await response.read()

            except asyncio.TimeoutError:
                return {
                    "valid": False,
                    "url": url,
                    "title": None,
                    "error": f"Request timeout after {timeout} seconds"
                }
            except aiohttp.ClientError as e:
                return {
                    "valid": False,
                    "url": url,
                    "title": None,
                    "error": f"Network error: {str(e)}"
                }

        # Parse the feed
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(
            None,
            feedparser.parse,
            content
        )

        # Check for parsing errors
        if feed.get("bozo", False):
            bozo_exception = feed.get("bozo_exception")
            # Some feeds have minor issues but are still usable
            # Only reject if it's a serious parsing error
            if bozo_exception and not feed.get("entries"):
                return {
                    "valid": False,
                    "url": url,
                    "title": None,
                    "error": (
                        f"Feed parsing error: {str(bozo_exception)}"
                    )
                }
            # Log warning but continue
            logger.warning(
                f"Feed has minor parsing issues: {bozo_exception}"
            )

        # Check if feed has entries
        if not feed.get("entries"):
            return {
                "valid": False,
                "url": url,
                "title": None,
                "error": "Feed has no entries"
            }

        # Validate feed structure - check that at least one entry
        # has required fields
        has_valid_entry = False
        for entry in feed.get("entries", []):
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            description = entry.get("description", "").strip()

            if title and link and description:
                has_valid_entry = True
                break

        if not has_valid_entry:
            return {
                "valid": False,
                "url": url,
                "title": None,
                "error": (
                    "Feed entries missing required fields "
                    "(title, link, description)"
                )
            }

        # Extract feed title
        feed_title = None
        if feed.get("feed"):
            feed_title = (
                feed.feed.get("title", "").strip() or
                feed.feed.get("subtitle", "").strip() or
                None
            )

        return {
            "valid": True,
            "url": url,
            "title": feed_title,
            "error": None
        }

    except RSSValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error validating RSS feed: {e}",
            exc_info=True,
        )
        raise RSSValidationError(
            f"Failed to validate feed: {str(e)}"
        )
