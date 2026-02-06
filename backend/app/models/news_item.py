from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import (
    String, Text, Integer,
    ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db import Base
from app.models.utils import utcnow_naive


@dataclass
class NewsItemSettings:
    language: Optional[str] = None
    priority: Optional[int] = None
    custom_fields: Optional[Dict[str, Any]] = None


class NewsItem(Base):
    __tablename__ = "news_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("source.id"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False
    )

    # Relationships
    source: Mapped["Source"] = relationship(  # type: ignore # noqa: F821
        "Source", back_populates="news_items"
    )
    task_results: Mapped[list["NewsItemNewsTask"]] = relationship(  # type: ignore # noqa: F821
        "NewsItemNewsTask",
        back_populates="news_item",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('source_id', 'url', name='uix_source_url'),
        UniqueConstraint(
            'source_id',
            'external_id',
            name='uix_source_external_id'
        ),
    )
