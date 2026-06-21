from datetime import datetime

from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.utils import utcnow_naive


class TelegramBot(Base):
    __tablename__ = "telegram_bot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    bot_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    bot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_tg_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    chats: Mapped[list[dict[str, str | int]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow_naive,
    )

    user: Mapped["User"] = relationship(  # type: ignore # noqa: F821
        "User",
        back_populates="telegram_bots",
    )
    news_tasks: Mapped[list["NewsTask"]] = relationship(  # noqa: F821 # type: ignore
        "NewsTask",
        secondary="telegram_bot_news_task",
        back_populates="telegram_bots",
    )
