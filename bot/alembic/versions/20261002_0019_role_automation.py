"""Postgres role automation: join roles and rules."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0019"
down_revision: Union[str, None] = "20261002_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "role_join_configs",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("member_role_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("bot_role_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("delay_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("screening", sa.String(16), nullable=False, server_default="immediate"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "role_automation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("trigger", sa.String(16), nullable=False),
        sa.Column("trigger_role_id", sa.BigInteger(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("action_role_id", sa.BigInteger(), nullable=False),
        sa.Column("delay_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_role_automation_rules_guild", "role_automation_rules", ["guild_id"])


def downgrade() -> None:
    op.drop_index("ix_role_automation_rules_guild", table_name="role_automation_rules")
    op.drop_table("role_automation_rules")
    op.drop_table("role_join_configs")
