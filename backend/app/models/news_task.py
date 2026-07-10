from datetime import datetime
from typing import TypedDict
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db import Base
from app.models.utils import utcnow_naive


class TelegramDeliverySettings(TypedDict):
    summary: bool
    lang: str
    prompt: str


class DeliverySettings(TypedDict):
    telegram: TelegramDeliverySettings


class NewsTaskSettings(TypedDict):
    delivery: DeliverySettings


def default_news_task_settings() -> NewsTaskSettings:
    return {
        "delivery": {
            "telegram": {
                "summary": False,
                "lang": "en",
                "prompt": "Retell the news article in a neutral way in a short form, no more than three sentences",
            }
        }
    }


class NewsTask(Base):
    __tablename__ = "news_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[NewsTaskSettings] = mapped_column(
        JSON,
        nullable=False,
        default=default_news_task_settings,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False
    )
    # Relationships
    sources: Mapped[list["Source"]] = relationship(  # type: ignore # noqa: F821
        "Source", secondary="source_news_task", back_populates="news_tasks"
    )
    item_results: Mapped[list["NewsItemNewsTask"]] = relationship(  # type: ignore # noqa: F821
        "NewsItemNewsTask",
        back_populates="news_task",
        cascade="all, delete-orphan",
    )
    newspaper: Mapped[list["Newspaper"]] = relationship(  # type: ignore # noqa: F821
        "Newspaper",
        back_populates="news_task",
        uselist=False,
        cascade="all, delete-orphan",
    )
    telegram_bots: Mapped[list["TelegramBot"]] = relationship(  # type: ignore # noqa: F821
        "TelegramBot",
        secondary="telegram_bot_news_task",
        back_populates="news_tasks",
    )
