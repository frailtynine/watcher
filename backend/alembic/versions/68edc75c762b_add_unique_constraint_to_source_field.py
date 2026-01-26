"""Add unique constraint to source field

Revision ID: 68edc75c762b
Revises: 5e28f0bda1d5
Create Date: 2026-01-26 21:27:02.974965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68edc75c762b'
down_revision: Union[str, Sequence[str], None] = '5e28f0bda1d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Delete source_news_task entries for duplicate sources
    op.execute("""
        DELETE FROM source_news_task
        WHERE source_id NOT IN (
            SELECT MIN(id)
            FROM source
            GROUP BY source
        )
    """)
    
    # Delete news_items for duplicate sources
    op.execute("""
        DELETE FROM news_item
        WHERE source_id NOT IN (
            SELECT MIN(id)
            FROM source
            GROUP BY source
        )
    """)
    
    # Remove duplicate sources, keeping only the oldest one
    op.execute("""
        DELETE FROM source
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM source
            GROUP BY source
        )
    """)
    
    op.create_unique_constraint(
        'uq_source_source', 'source', ['source']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_source_source', 'source', type_='unique')
