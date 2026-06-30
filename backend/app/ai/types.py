"""Typed contracts for the AI consumer pipeline."""

from dataclasses import dataclass
from datetime import datetime

from app.ai.base import ProcessingResult


@dataclass(frozen=True)
class TaskContext:
    task_id: int
    user_id: int
    name: str
    prompt: str


@dataclass(frozen=True)
class QueuedNewsPayload:
    news_item_id: int
    task_id: int
    source_id: int
    title: str
    content: str
    url: str | None
    published_at: datetime


@dataclass(frozen=True)
class EvaluationOutcome:
    task_id: int
    news_item_id: int
    payload: QueuedNewsPayload
    result: ProcessingResult | None


@dataclass(frozen=True)
class UserProcessingContext:
    user_id: int
    email: str
    settings: dict
    tasks: list[TaskContext]


@dataclass(frozen=True)
class TaskRunStats:
    queued: int = 0
    processed: int = 0
    matched: int = 0
    rejected: int = 0
    errors: int = 0


@dataclass(frozen=True)
class PersistResult:
    stats: TaskRunStats
    successful: list[EvaluationOutcome]
    matched: list[EvaluationOutcome]


@dataclass(frozen=True)
class NotificationTarget:
    encrypted_bot_token: str
    chat_id: str
