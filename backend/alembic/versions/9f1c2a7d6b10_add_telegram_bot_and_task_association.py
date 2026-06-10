"""add telegram_bot and bot-task association tables

Revision ID: 9f1c2a7d6b10
Revises: b8a1e4f7c912
Create Date: 2026-06-08 13:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f1c2a7d6b10"
down_revision: Union[str, Sequence[str], None] = "b8a1e4f7c912"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "telegram_bot",
        "chat_ids",
        new_column_name="chats",
        existing_type=sa.JSON(),
        existing_nullable=False,
    )

    op.create_table(
        "telegram_bot_news_task",
        sa.Column("telegram_bot_id", sa.Integer(), nullable=False),
        sa.Column("news_task_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["news_task_id"], ["news_task.id"]),
        sa.ForeignKeyConstraint(["telegram_bot_id"], ["telegram_bot.id"]),
        sa.PrimaryKeyConstraint("telegram_bot_id", "news_task_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("telegram_bot_news_task")
    op.alter_column(
        "telegram_bot",
        "chats",
        new_column_name="chat_ids",
        existing_type=sa.JSON(),
        existing_nullable=False,
    )
