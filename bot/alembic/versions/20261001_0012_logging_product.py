"""Logging ignores, legacy migration marker, and message attachment metadata."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0012"
down_revision: Union[str, None] = "20261001_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("log_message_content", sa.Column("attachments", postgresql.JSONB(), nullable=True))
    op.create_table(
        "log_ignores",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("kind", sa.String(16), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), primary_key=True),
    )
    op.create_table(
        "log_migrations",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("migrated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("log_migrations")
    op.drop_table("log_ignores")
    op.drop_column("log_message_content", "attachments")
