from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


def utcnow_naive():
    """Return current UTC time as naive datetime (for TIMESTAMP WITHOUT TIME ZONE)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class NewsTask(Base):
    __tablename__ = "news_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    sources: Mapped[list["Source"]] = relationship(
        "Source",
        secondary="source_news_task",
        back_populates="news_tasks"
    )
