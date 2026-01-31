from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.utils import utcnow_naive


class SourceNewsTask(Base):
    __tablename__ = "source_news_task"

    source_id: Mapped[int] = mapped_column(
        ForeignKey("source.id"),
        primary_key=True
    )
    news_task_id: Mapped[int] = mapped_column(
        ForeignKey("news_task.id"),
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive,
        nullable=False
    )
