"""Phase 1 platform core schema

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30
"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260330_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dashboard_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("auth_time", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(255), nullable=True),
    )
    op.create_index("ix_dashboard_sessions_discord_user_id", "dashboard_sessions", ["discord_user_id"])

    op.create_table(
        "dashboard_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("template_key", sa.String(32), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "dashboard_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("discord_user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dashboard_roles.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dashboard_grants_guild_id", "dashboard_grants", ["guild_id"])
    op.create_index("ix_dashboard_grants_discord_user_id", "dashboard_grants", ["discord_user_id"])
    op.create_index("ix_dashboard_grants_guild_user", "dashboard_grants", ["guild_id", "discord_user_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("target", sa.String(255), nullable=True),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_events_guild_id", "audit_events", ["guild_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    op.create_table(
        "scheduler_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("dedupe_key", sa.String(255), nullable=True, unique=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scheduler_jobs_job_type", "scheduler_jobs", ["job_type"])
    op.create_index("ix_scheduler_jobs_run_at", "scheduler_jobs", ["run_at"])
    op.create_index("ix_scheduler_jobs_status", "scheduler_jobs", ["status"])

    op.create_table(
        "snapshot_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("snapshot_meta", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_snapshot_metadata_guild_id", "snapshot_metadata", ["guild_id"])

    roles = sa.table(
        "dashboard_roles",
        sa.column("id", postgresql.UUID),
        sa.column("name", sa.String),
        sa.column("template_key", sa.String),
        sa.column("capabilities", postgresql.JSONB),
    )
    from cls_platform.capabilities import ADMIN_CAPS, MODERATOR_CAPS, SUPPORT_CAPS

    op.bulk_insert(
        roles,
        [
            {"id": uuid.uuid4(), "name": "Admin", "template_key": "admin", "capabilities": ADMIN_CAPS},
            {"id": uuid.uuid4(), "name": "Moderator", "template_key": "moderator", "capabilities": MODERATOR_CAPS},
            {"id": uuid.uuid4(), "name": "Support", "template_key": "support", "capabilities": SUPPORT_CAPS},
        ],
    )

    op.execute(
        """
        REVOKE UPDATE, DELETE ON audit_events FROM PUBLIC;
        """
    )


def downgrade() -> None:
    op.drop_table("snapshot_metadata")
    op.drop_table("scheduler_jobs")
    op.drop_table("audit_events")
    op.drop_table("dashboard_grants")
    op.drop_table("dashboard_roles")
    op.drop_table("dashboard_sessions")
