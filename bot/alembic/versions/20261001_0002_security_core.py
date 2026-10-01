"""Phase 2A security foundation.

Revision ID: 20261001_0002
Revises: 20260330_0001

ENFORCE remains in the mode vocabulary. Triggers reject ENFORCE writes and
Discord-mutation outcomes until containment exists (step 2A.6 drops those
triggers). Quarantine tables exist for later foreign keys and have no
mutation behavior.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0002"
down_revision: Union[str, None] = "20260330_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MODES = "('OFF', 'OBSERVE', 'ENFORCE')"
_ATTR = "('CONFIRMED', 'PROBABLE', 'AMBIGUOUS', 'UNATTRIBUTED', 'SELF', 'CLS_PROXIED')"
_SIGNAL = "('PENDING', 'LINKED', 'SUPERSEDED', 'EXPIRED_UNATTRIBUTED')"
_INCIDENT_STATUS = "('ACTIVE', 'CLOSED')"
_CLOSURE = "('EXPIRED_INACTIVE', 'EXPIRED_LIFETIME', 'RESOLVED', 'FALSE_POSITIVE')"
_OUTCOME = (
    "('WOULD_CONTAIN', 'ACTIVE', 'PARTIAL_QUARANTINE', 'UNCONTAINABLE_HIERARCHY', "
    "'FAILED_PERMISSION', 'FAILED_DISCORD', 'NOT_ATTEMPTED_POLICY', 'SKIPPED_TRUSTED', "
    "'SKIPPED_MODE', 'RELEASED', 'RELEASE_PARTIAL', 'RELEASE_FAILED')"
)
_ALERT = "('PENDING', 'DELIVERED', 'FAILED', 'UNDELIVERABLE_NO_DESTINATION', 'COALESCED')"
_SOURCE = "('audit_push', 'audit_fetch', 'gateway', 'reconciliation')"
_ENGINE = "('human', 'bot')"
_RULE_KIND = "('rate', 'aggregate', 'single', 'sequence')"


def upgrade() -> None:
    op.add_column("scheduler_jobs", sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scheduler_jobs", sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_scheduler_jobs_running_lease",
        "scheduler_jobs",
        ["lease_until"],
        postgresql_where=sa.text("status = 'running'"),
    )

    op.create_table(
        "security_guild_configs",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("human_mode", sa.String(16), nullable=False, server_default="OBSERVE"),
        sa.Column("bot_mode", sa.String(16), nullable=False, server_default="OBSERVE"),
        sa.Column("quarantine_role_id", sa.BigInteger(), nullable=True),
        sa.Column("incident_inactivity_s", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("incident_max_lifetime_s", sa.Integer(), nullable=False, server_default="21600"),
        sa.Column("gateway_dedupe_s", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(f"human_mode IN {_MODES}", name="ck_security_guild_configs_human_mode"),
        sa.CheckConstraint(f"bot_mode IN {_MODES}", name="ck_security_guild_configs_bot_mode"),
        sa.CheckConstraint(
            "incident_inactivity_s >= 300 AND incident_inactivity_s <= 3600",
            name="ck_security_guild_configs_inactivity",
        ),
        sa.CheckConstraint(
            "incident_max_lifetime_s >= incident_inactivity_s",
            name="ck_security_guild_configs_lifetime",
        ),
        sa.CheckConstraint(
            "gateway_dedupe_s >= 1 AND gateway_dedupe_s <= 120",
            name="ck_security_guild_configs_dedupe",
        ),
        sa.CheckConstraint("version >= 1", name="ck_security_guild_configs_version"),
    )

    op.create_table(
        "security_action_policies",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("action_class", sa.String(64), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("window_s", sa.Integer(), nullable=False),
        sa.Column("tier_floor", sa.String(32), nullable=True),
        sa.Column("containment_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rule_kind", sa.String(16), nullable=False),
        sa.Column("distinct_targets", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "threshold_status",
            sa.String(32),
            nullable=False,
            server_default="DEVELOPMENT_PROPOSAL",
        ),
        sa.CheckConstraint("threshold >= 1", name="ck_security_action_policies_threshold"),
        sa.CheckConstraint("window_s >= 0", name="ck_security_action_policies_window"),
        sa.CheckConstraint(f"rule_kind IN {_RULE_KIND}", name="ck_security_action_policies_kind"),
        sa.CheckConstraint(
            "threshold_status = 'DEVELOPMENT_PROPOSAL'",
            name="ck_security_action_policies_proposal",
        ),
    )

    op.create_table(
        "security_trusted_actors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("kind IN ('human', 'bot')", name="ck_security_trusted_actors_kind"),
        sa.CheckConstraint("subject_id > 0 AND guild_id > 0", name="ck_security_trusted_actors_ids"),
    )
    op.create_index(
        "uq_security_trusted_actors_active",
        "security_trusted_actors",
        ["guild_id", "subject_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "security_guild_state",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("last_audit_entry_id", sa.BigInteger(), nullable=True),
        sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trust_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification_passed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ops_destination_ok", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("trust_version >= 0", name="ck_security_guild_state_trust_version"),
    )

    op.create_table(
        "security_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), nullable=True),
        sa.Column("engine", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("closure", sa.String(32), nullable=True),
        sa.Column("severity", sa.String(8), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.BigInteger(), nullable=True),
        sa.Column("previous_incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trust_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("tier_map_version", sa.String(32), nullable=False),
        sa.Column("quarantine_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(f"status IN {_INCIDENT_STATUS}", name="ck_security_incidents_status"),
        sa.CheckConstraint(
            f"closure IS NULL OR closure IN {_CLOSURE}",
            name="ck_security_incidents_closure",
        ),
        sa.CheckConstraint(f"engine IN {_ENGINE}", name="ck_security_incidents_engine"),
        sa.CheckConstraint("severity IN ('C', 'H', 'M', 'L')", name="ck_security_incidents_severity"),
        sa.ForeignKeyConstraint(["previous_incident_id"], ["security_incidents.id"]),
    )
    op.create_index("ix_security_incidents_guild_id", "security_incidents", ["guild_id"])
    op.create_index(
        "uq_security_incidents_active",
        "security_incidents",
        ["guild_id", "subject_id", "engine"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE' AND subject_id IS NOT NULL"),
    )

    op.create_table(
        "security_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("audit_entry_id", sa.BigInteger(), nullable=True),
        sa.Column("action_class", sa.String(64), nullable=False),
        sa.Column("discord_action", sa.String(64), nullable=True),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("attribution_state", sa.String(32), nullable=False),
        sa.Column("late", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("corroborated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("superseded_by_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entry_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(8), nullable=False),
        sa.Column("permission_tier", sa.String(32), nullable=True),
        sa.Column("change_digest", sa.String(128), nullable=True),
        sa.Column("attribution_method", sa.String(64), nullable=True),
        sa.Column("attribution_reason", sa.Text(), nullable=True),
        sa.Column("candidate_actor_ids", postgresql.ARRAY(sa.BigInteger()), nullable=True),
        sa.Column("permission_diff", postgresql.JSONB(), nullable=True),
        sa.Column("counts_for_containment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(f"attribution_state IN {_ATTR}", name="ck_security_observations_attr"),
        sa.CheckConstraint(f"source IN {_SOURCE}", name="ck_security_observations_source"),
        sa.CheckConstraint("severity IN ('C', 'H', 'M', 'L')", name="ck_security_observations_severity"),
        sa.CheckConstraint(
            "counts_for_containment = false OR (attribution_state = 'CONFIRMED' AND late = false)",
            name="ck_security_observations_containment_count",
        ),
        sa.ForeignKeyConstraint(["superseded_by_observation_id"], ["security_observations.id"]),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"]),
    )
    op.create_index(
        "uq_security_observations_audit",
        "security_observations",
        ["guild_id", "audit_entry_id"],
        unique=True,
        postgresql_where=sa.text("audit_entry_id IS NOT NULL"),
    )
    op.create_index(
        "ix_security_observations_actor_time",
        "security_observations",
        ["guild_id", "actor_id", "entry_created_at"],
    )

    op.create_table(
        "security_gateway_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("action_class", sa.String(64), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("change_digest", sa.String(128), nullable=False),
        sa.Column("correlation_key", sa.String(255), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("linked_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discord_action", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(f"state IN {_SIGNAL}", name="ck_security_gateway_signals_state"),
        sa.CheckConstraint("duplicate_count >= 1", name="ck_security_gateway_signals_dupes"),
        sa.ForeignKeyConstraint(["linked_observation_id"], ["security_observations.id"]),
    )
    op.create_index(
        "ix_security_gateway_signals_correlation",
        "security_gateway_signals",
        ["guild_id", "correlation_key", "first_seen_at"],
        unique=False,
    )

    op.create_table(
        "security_incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"]),
    )
    op.create_index("ix_security_incident_events_incident", "security_incident_events", ["incident_id"])
    op.create_index("ix_security_incident_events_guild", "security_incident_events", ["guild_id"])

    op.create_table(
        "security_response_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_id", sa.BigInteger(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("effective_mode", sa.String(16), nullable=False),
        sa.Column("discord_mutation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rule_id", sa.String(64), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discord_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(f"outcome IN {_OUTCOME}", name="ck_security_response_outcome"),
        sa.CheckConstraint(f"effective_mode IN {_MODES}", name="ck_security_response_mode"),
        sa.CheckConstraint(
            "effective_mode <> 'OBSERVE' OR discord_mutation = false",
            name="ck_security_response_observe_no_mutation",
        ),
        sa.CheckConstraint(
            "outcome <> 'WOULD_CONTAIN' OR discord_mutation = false",
            name="ck_security_response_would_contain_no_mutation",
        ),
        sa.CheckConstraint(
            "discord_mutation = false OR effective_mode = 'ENFORCE'",
            name="ck_security_response_mutation_requires_enforce",
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"]),
        sa.UniqueConstraint("idempotency_key", name="uq_security_response_actions_idempotency"),
    )

    op.create_table(
        "security_quarantines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("prior_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=True),
        sa.Column("prior_role_perms", postgresql.JSONB(), nullable=True),
        sa.Column("removed_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=True),
        sa.Column("residual", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('APPLYING', 'ACTIVE', 'PARTIAL_QUARANTINE', 'UNCONTAINABLE_HIERARCHY', "
            "'FAILED_PERMISSION', 'FAILED_DISCORD', 'NOT_ATTEMPTED_POLICY', 'SKIPPED_TRUSTED', "
            "'SKIPPED_MODE', 'RELEASED', 'RELEASE_PARTIAL', 'RELEASE_FAILED')",
            name="ck_security_quarantines_status",
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"]),
    )
    op.create_index(
        "uq_security_quarantines_open",
        "security_quarantines",
        ["guild_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('APPLYING', 'ACTIVE', 'PARTIAL_QUARANTINE')"),
    )

    op.create_table(
        "security_maintenance_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("started_by", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_reason", sa.String(32), nullable=True),
        sa.CheckConstraint("expires_at > starts_at", name="ck_security_maintenance_order"),
        sa.CheckConstraint(
            "expires_at <= starts_at + interval '60 minutes'",
            name="ck_security_maintenance_cap",
        ),
        sa.CheckConstraint("length(reason) > 0", name="ck_security_maintenance_reason"),
    )
    op.create_index(
        "uq_security_maintenance_windows_active",
        "security_maintenance_windows",
        ["guild_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.create_table(
        "security_alert_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dedupe_key", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"status IN {_ALERT}", name="ck_security_alert_outbox_status"),
        sa.CheckConstraint("attempts >= 0", name="ck_security_alert_outbox_attempts"),
        sa.ForeignKeyConstraint(["incident_id"], ["security_incidents.id"]),
        sa.UniqueConstraint("dedupe_key", name="uq_security_alert_outbox_dedupe"),
    )
    op.create_index("ix_security_alert_outbox_status_next", "security_alert_outbox", ["status", "next_attempt_at"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_operational_enforce()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF NEW.human_mode = 'ENFORCE' OR NEW.bot_mode = 'ENFORCE' THEN
            RAISE EXCEPTION 'ENFORCE is not operational until containment is implemented';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER security_guild_configs_reject_enforce
        BEFORE INSERT OR UPDATE ON security_guild_configs
        FOR EACH ROW EXECUTE FUNCTION security_reject_operational_enforce()
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_discord_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF NEW.effective_mode = 'ENFORCE' THEN
            RAISE EXCEPTION 'ENFORCE is not operational until containment is implemented';
          END IF;
          IF NEW.discord_mutation THEN
            RAISE EXCEPTION 'Discord containment mutation is not available';
          END IF;
          IF NEW.outcome IN (
            'ACTIVE', 'PARTIAL_QUARANTINE', 'RELEASED', 'RELEASE_PARTIAL', 'RELEASE_FAILED'
          ) THEN
            RAISE EXCEPTION 'Containment outcomes are not available until quarantine execution exists';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER security_response_actions_reject_mutation
        BEFORE INSERT OR UPDATE ON security_response_actions
        FOR EACH ROW EXECUTE FUNCTION security_reject_discord_mutation()
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_incident_events_append_only()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'security_incident_events is append-only';
          END IF;
          IF TG_OP = 'DELETE'
             AND current_setting('app.allow_security_purge', true) IS DISTINCT FROM 'on' THEN
            RAISE EXCEPTION 'security_incident_events delete requires maintenance purge';
          END IF;
          RETURN OLD;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER security_incident_events_append_only
        BEFORE UPDATE OR DELETE ON security_incident_events
        FOR EACH ROW EXECUTE FUNCTION security_incident_events_append_only()
        """
    )
    op.execute("REVOKE UPDATE, DELETE ON security_incident_events FROM PUBLIC")

    op.execute(
        """
        UPDATE dashboard_roles
        SET capabilities = (
          SELECT COALESCE(jsonb_agg(DISTINCT elem), '[]'::jsonb)
          FROM (
            SELECT jsonb_array_elements(capabilities) AS elem
            UNION ALL
            SELECT '"security.incidents.manage"'::jsonb
          ) s
        )
        WHERE template_key = 'admin'
          AND NOT (capabilities @> '["security.incidents.manage"]'::jsonb);
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS security_incident_events_append_only ON security_incident_events")
    op.execute(
        "DROP TRIGGER IF EXISTS security_response_actions_reject_mutation ON security_response_actions"
    )
    op.execute("DROP TRIGGER IF EXISTS security_guild_configs_reject_enforce ON security_guild_configs")
    op.execute("DROP FUNCTION IF EXISTS security_incident_events_append_only()")
    op.execute("DROP FUNCTION IF EXISTS security_reject_discord_mutation()")
    op.execute("DROP FUNCTION IF EXISTS security_reject_operational_enforce()")
    op.execute(
        """
        UPDATE dashboard_roles
        SET capabilities = (
          SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
          FROM jsonb_array_elements(capabilities) AS elem
          WHERE elem <> '"security.incidents.manage"'::jsonb
        )
        WHERE template_key = 'admin';
        """
    )
    op.drop_table("security_alert_outbox")
    op.drop_table("security_maintenance_windows")
    op.drop_table("security_quarantines")
    op.drop_table("security_response_actions")
    op.drop_table("security_incident_events")
    op.drop_table("security_gateway_signals")
    op.drop_table("security_observations")
    op.drop_table("security_incidents")
    op.drop_table("security_guild_state")
    op.drop_table("security_trusted_actors")
    op.drop_table("security_action_policies")
    op.drop_table("security_guild_configs")
    op.drop_index("ix_scheduler_jobs_running_lease", table_name="scheduler_jobs")
    op.drop_column("scheduler_jobs", "claimed_at")
    op.drop_column("scheduler_jobs", "lease_until")
