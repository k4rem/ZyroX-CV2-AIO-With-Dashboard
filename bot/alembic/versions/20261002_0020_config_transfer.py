"""Config transfer history and pre-import snapshots."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0020"
down_revision: Union[str, None] = "20261002_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_import_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("source_guild_id", sa.String(32), nullable=False),
        sa.Column("source_guild_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("modules", postgresql.JSONB(), nullable=False),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("format_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_config_import_history_guild", "config_import_history", ["guild_id"])
    op.create_table(
        "config_import_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("modules", postgresql.JSONB(), nullable=False),
        sa.Column("bundle", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("config_import_snapshots")
    op.drop_index("ix_config_import_history_guild", table_name="config_import_history")
    op.drop_table("config_import_history")
