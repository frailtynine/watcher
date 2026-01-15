from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class SourceType(str, PyEnum):
    RSS = "RSS"
    TELEGRAM = "Telegram"


class Source(Base):
    __tablename__ = "source"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)  # URL or channel_id
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    news_tasks: Mapped[list["NewsTask"]] = relationship(
        "NewsTask",
        secondary="source_news_task",
        back_populates="sources"
    )
    news_items: Mapped[list["NewsItem"]] = relationship("NewsItem", back_populates="source")
