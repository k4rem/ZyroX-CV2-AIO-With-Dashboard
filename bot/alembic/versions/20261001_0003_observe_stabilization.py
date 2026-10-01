"""Phase 2A.4.1 observe pipeline stabilization.

Revision ID: 20261001_0003
Revises: 20261001_0002

Adds delivery statuses, owner persistence, ledger match columns, hot-path
indexes, and a partial scheduler dedupe so a finished job cannot block the
next operation. No containment behavior.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261001_0003"
down_revision: Union[str, None] = "20261001_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ALERT = (
    "('PENDING', 'CLAIMED', 'DEGRADED', 'DELIVERED', 'FAILED', "
    "'UNDELIVERABLE_NO_DESTINATION', 'COALESCED')"
)
_ALERT_PREVIOUS = "('PENDING', 'DELIVERED', 'FAILED', 'UNDELIVERABLE_NO_DESTINATION', 'COALESCED')"


def upgrade() -> None:
    op.drop_constraint("scheduler_jobs_dedupe_key_key", "scheduler_jobs", type_="unique")
    op.create_index(
        "uq_scheduler_jobs_dedupe_active",
        "scheduler_jobs",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL AND status IN ('pending', 'running')"),
    )
    op.add_column("security_guild_state", sa.Column("guild_owner_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "security_observations",
        sa.Column("actor_is_bot", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("security_response_actions", sa.Column("reason_token", sa.Text(), nullable=True))
    op.add_column(
        "security_response_actions",
        sa.Column("ledger_action_class", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_security_observations_action_target_time",
        "security_observations",
        ["guild_id", "action_class", "target_id", "entry_created_at"],
    )
    op.create_index("ix_security_observations_incident", "security_observations", ["incident_id"])
    op.create_index(
        "ix_security_gateway_signals_state_action",
        "security_gateway_signals",
        ["guild_id", "state", "discord_action"],
    )
    op.create_index(
        "uq_security_incidents_unattributed_active",
        "security_incidents",
        ["guild_id", "engine"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE' AND subject_id IS NULL"),
    )
    op.drop_constraint("ck_security_alert_outbox_status", "security_alert_outbox", type_="check")
    op.create_check_constraint(
        "ck_security_alert_outbox_status",
        "security_alert_outbox",
        f"status IN {_ALERT}",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE security_alert_outbox SET status = 'PENDING' "
        "WHERE status IN ('CLAIMED', 'DEGRADED')"
    )
    op.drop_constraint("ck_security_alert_outbox_status", "security_alert_outbox", type_="check")
    op.create_check_constraint(
        "ck_security_alert_outbox_status",
        "security_alert_outbox",
        f"status IN {_ALERT_PREVIOUS}",
    )
    op.drop_index("uq_security_incidents_unattributed_active", table_name="security_incidents")
    op.drop_index("ix_security_gateway_signals_state_action", table_name="security_gateway_signals")
    op.drop_index("ix_security_observations_incident", table_name="security_observations")
    op.drop_index("ix_security_observations_action_target_time", table_name="security_observations")
    op.drop_column("security_response_actions", "ledger_action_class")
    op.drop_column("security_response_actions", "reason_token")
    op.drop_column("security_observations", "actor_is_bot")
    op.drop_column("security_guild_state", "guild_owner_id")
    op.drop_index("uq_scheduler_jobs_dedupe_active", table_name="scheduler_jobs")
    op.execute(
        """
        UPDATE scheduler_jobs AS newer
        SET dedupe_key = newer.dedupe_key || ':' || newer.id::text
        WHERE newer.dedupe_key IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM scheduler_jobs AS older
            WHERE older.dedupe_key = newer.dedupe_key
              AND older.id <> newer.id
          )
        """
    )
    op.create_unique_constraint("scheduler_jobs_dedupe_key_key", "scheduler_jobs", ["dedupe_key"])
