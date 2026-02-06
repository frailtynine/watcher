from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db import Base
from app.models.utils import utcnow_naive


class NewsItemNewsTask(Base):
    """Association table between NewsItem and NewsTask with processing results"""
    __tablename__ = "news_item_news_task"

    news_item_id: Mapped[int] = mapped_column(
        ForeignKey("news_item.id"),
        primary_key=True
    )
    news_task_id: Mapped[int] = mapped_column(
        ForeignKey("news_task.id"),
        primary_key=True
    )
    
    # Processing results
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    ai_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False
    )

    # Relationships
    news_item: Mapped["NewsItem"] = relationship(  # type: ignore # noqa: F821
        "NewsItem",
        back_populates="task_results"
    )
    news_task: Mapped["NewsTask"] = relationship(  # type: ignore # noqa: F821
        "NewsTask",
        back_populates="item_results"
    )
