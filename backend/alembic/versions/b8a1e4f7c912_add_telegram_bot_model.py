"""add telegram_bot model

Revision ID: b8a1e4f7c912
Revises: 8375ffc143c8
Create Date: 2026-06-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8a1e4f7c912"
down_revision: Union[str, Sequence[str], None] = "8375ffc143c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "telegram_bot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bot_token", sa.String(length=2048), nullable=False),
        sa.Column("bot_name", sa.String(length=255), nullable=False),
        sa.Column("bot_tg_id", sa.String(length=255), nullable=False),
        sa.Column("chat_ids", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_bot_user_id"),
        "telegram_bot",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_bot_bot_tg_id"),
        "telegram_bot",
        ["bot_tg_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_telegram_bot_bot_tg_id"), table_name="telegram_bot")
    op.drop_index(op.f("ix_telegram_bot_user_id"), table_name="telegram_bot")
    op.drop_table("telegram_bot")
