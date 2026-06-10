from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.utils import utcnow_naive


class TelegramBotNewsTask(Base):
    __tablename__ = "telegram_bot_news_task"

    telegram_bot_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_bot.id"),
        primary_key=True,
    )
    news_task_id: Mapped[int] = mapped_column(
        ForeignKey("news_task.id"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False,
    )
