"""News producers package for fetching content from various sources."""

from .base import BaseProducer
from .rss import RSSProducer
from .telegram import TelegramProducer

__all__ = ["BaseProducer", "RSSProducer", "TelegramProducer"]
