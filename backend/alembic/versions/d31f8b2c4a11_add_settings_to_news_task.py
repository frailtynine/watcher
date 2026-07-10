"""add settings to news_task

Revision ID: d31f8b2c4a11
Revises: 9f1c2a7d6b10
Create Date: 2026-07-08 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d31f8b2c4a11"
down_revision: Union[str, Sequence[str], None] = "9f1c2a7d6b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "news_task",
        sa.Column(
            "settings",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                '\'{"delivery": {"telegram": {"summary": false, "lang": "en", "prompt": "Retell the news article in a neutral way in a short form, no more than three sentences"}}}\'::json'
            ),
        ),
    )
    op.alter_column("news_task", "settings", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("news_task", "settings")
