"""Initial schema baseline.

Revision ID: 001
Revises:
Create Date: 2024-12-08

This is a baseline migration - the schema already exists in the database.
After deploying SQLAlchemy, run: alembic stamp 001
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Schema already exists in database.

    This migration exists only to establish the baseline.
    All 13 tables and 11 enums are already created via Supabase migrations.
    """
    pass


def downgrade() -> None:
    """Cannot downgrade - would drop entire schema."""
    raise RuntimeError("Cannot downgrade initial baseline migration")
