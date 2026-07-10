from .user import UserRead, UserCreate, UserUpdate
from .news_task import NewsTaskRead, NewsTaskCreate, NewsTaskUpdate
from .source import SourceRead, SourceCreate, SourceUpdate
from .source_news_task import SourceNewsTaskRead, SourceNewsTaskCreate
from .news_item import NewsItemRead, NewsItemCreate, NewsItemUpdate
from .news_item_news_task import (
    NewsItemNewsTaskRead,
    NewsItemNewsTaskCreate,
    NewsItemNewsTaskUpdate,
)
from .newspaper import NewspaperRead
from .telegram_bot import TelegramBotCreate, TelegramBotRead
from .telegram_bot_news_task import (
    TelegramBotNewsTaskCreate,
    TelegramBotNewsTaskRead,
)
from .ai_debug import (
    AIDeduplicationDebugRequest,
    AIDeduplicationDebugResponse,
    AISummaryDebugRequest,
    AISummaryDebugResponse,
)

__all__ = [
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "NewsTaskRead",
    "NewsTaskCreate",
    "NewsTaskUpdate",
    "SourceRead",
    "SourceCreate",
    "SourceUpdate",
    "SourceNewsTaskRead",
    "SourceNewsTaskCreate",
    "NewsItemRead",
    "NewsItemCreate",
    "NewsItemUpdate",
    "NewsItemNewsTaskRead",
    "NewsItemNewsTaskCreate",
    "NewsItemNewsTaskUpdate",
    "NewspaperRead",
    "TelegramBotCreate",
    "TelegramBotRead",
    "TelegramBotNewsTaskCreate",
    "TelegramBotNewsTaskRead",
    "AIDeduplicationDebugRequest",
    "AIDeduplicationDebugResponse",
    "AISummaryDebugRequest",
    "AISummaryDebugResponse",
]
