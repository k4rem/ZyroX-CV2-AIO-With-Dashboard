"""Automod V2 config, violations, and strikes."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0026"
down_revision: Union[str, None] = "20261002_0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automod_v2_configs",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preset", sa.String(16), nullable=False, server_default="balanced"),
        sa.Column("exclusions", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("escalations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("strike_ttl_seconds", sa.Integer(), nullable=False, server_default="604800"),
        sa.Column("migrated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("migration_notes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "automod_v2_rules",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("engine", sa.String(24), nullable=False, server_default="cls"),
        sa.Column("mode", sa.String(16), nullable=False, server_default="enforce"),
        sa.Column("trigger", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scope", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("message_action", sa.String(16), nullable=False, server_default="keep"),
        sa.Column("member_action", sa.String(16), nullable=False, server_default="none"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("notify_action", sa.String(16), nullable=False, server_default="none"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("guild_id", "rule_id"),
    )
    op.create_table(
        "automod_v2_violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("rule_id", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("false_positive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("result_status", sa.String(16), nullable=False, server_default="skipped"),
        sa.Column("action_keys", sa.String(120), nullable=False, server_default=""),
        sa.Column("log_event_id", sa.String(64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automod_v2_violations_guild_time", "automod_v2_violations", ["guild_id", "occurred_at"])
    op.create_table(
        "automod_v2_strikes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_id", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="automod"),
        sa.Column("violation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("moderator_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_automod_v2_strikes_member", "automod_v2_strikes", ["guild_id", "member_id"])


def downgrade() -> None:
    op.drop_index("ix_automod_v2_strikes_member", table_name="automod_v2_strikes")
    op.drop_table("automod_v2_strikes")
    op.drop_index("ix_automod_v2_violations_guild_time", table_name="automod_v2_violations")
    op.drop_table("automod_v2_violations")
    op.drop_table("automod_v2_rules")
    op.drop_table("automod_v2_configs")
