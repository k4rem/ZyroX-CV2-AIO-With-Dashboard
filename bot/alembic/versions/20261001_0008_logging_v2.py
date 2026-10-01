"""Logging V2 event store, message content, and routes."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0008"
down_revision: Union[str, None] = "20261001_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "log_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_confidence", sa.String(16), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_log_events_guild_time", "log_events", ["guild_id", "occurred_at"])
    op.create_index("ix_log_events_guild_category_time", "log_events", ["guild_id", "category", "occurred_at"])
    op.create_index("ix_log_events_guild_type", "log_events", ["guild_id", "event_type"])
    op.create_index("ix_log_events_guild_actor", "log_events", ["guild_id", "actor_id"])
    op.create_index("ix_log_events_guild_target", "log_events", ["guild_id", "target_id"])
    op.create_table(
        "log_message_content",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("message_id", sa.BigInteger(), primary_key=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_log_message_content_created", "log_message_content", ["created_at"])
    op.create_table(
        "log_routes",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("category", sa.String(32), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("log_routes")
    op.drop_index("ix_log_message_content_created", table_name="log_message_content")
    op.drop_table("log_message_content")
    op.drop_index("ix_log_events_guild_target", table_name="log_events")
    op.drop_index("ix_log_events_guild_actor", table_name="log_events")
    op.drop_index("ix_log_events_guild_type", table_name="log_events")
    op.drop_index("ix_log_events_guild_category_time", table_name="log_events")
    op.drop_index("ix_log_events_guild_time", table_name="log_events")
    op.drop_table("log_events")
