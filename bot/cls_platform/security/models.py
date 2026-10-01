"""Phase 2A security tables. Schema authority is the Alembic revision."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.models import Base


class SecurityGuildConfig(Base):
    __tablename__ = "security_guild_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    human_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="OBSERVE")
    bot_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="OBSERVE")
    quarantine_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    incident_inactivity_s: Mapped[int] = mapped_column(Integer, nullable=False, default=900)
    incident_max_lifetime_s: Mapped[int] = mapped_column(Integer, nullable=False, default=21600)
    gateway_dedupe_s: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityActionPolicy(Base):
    __tablename__ = "security_action_policies"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    action_class: Mapped[str] = mapped_column(String(64), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    window_s: Mapped[int] = mapped_column(Integer, nullable=False)
    tier_floor: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    containment_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rule_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    distinct_targets: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threshold_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DEVELOPMENT_PROPOSAL"
    )


class SecurityTrustedActor(Base):
    __tablename__ = "security_trusted_actors"
    __table_args__ = (
        Index(
            "uq_security_trusted_actors_active",
            "guild_id",
            "subject_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityGuildState(Base):
    __tablename__ = "security_guild_state"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_audit_entry_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    last_reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trust_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_passed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ops_destination_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guild_owner_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityIncident(Base):
    __tablename__ = "security_incidents"
    __table_args__ = (
        Index(
            "uq_security_incidents_active",
            "guild_id",
            "subject_id",
            "engine",
            unique=True,
            postgresql_where=text("status = 'ACTIVE' AND subject_id IS NOT NULL"),
        ),
        Index(
            "uq_security_incidents_unattributed_active",
            "guild_id",
            "engine",
            unique=True,
            postgresql_where=text("status = 'ACTIVE' AND subject_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    subject_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    engine: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    closure: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    previous_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=True
    )
    trust_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    tier_map_version: Mapped[str] = mapped_column(String(32), nullable=False)
    quarantine_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


class SecurityObservation(Base):
    __tablename__ = "security_observations"
    __table_args__ = (
        Index(
            "uq_security_observations_audit",
            "guild_id",
            "audit_entry_id",
            unique=True,
            postgresql_where=text("audit_entry_id IS NOT NULL"),
        ),
        Index("ix_security_observations_actor_time", "guild_id", "actor_id", "entry_created_at"),
        Index(
            "ix_security_observations_action_target_time",
            "guild_id",
            "action_class",
            "target_id",
            "entry_created_at",
        ),
        Index("ix_security_observations_incident", "incident_id"),
        CheckConstraint(
            "counts_for_containment = false OR (attribution_state = 'CONFIRMED' AND late = false)",
            name="ck_security_observations_containment_count",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    audit_entry_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action_class: Mapped[str] = mapped_column(String(64), nullable=False)
    discord_action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    attribution_state: Mapped[str] = mapped_column(String(32), nullable=False)
    late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corroborated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    superseded_by_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_observations.id"), nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    permission_tier: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    actor_is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    change_digest: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    attribution_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    attribution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    candidate_actor_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    permission_diff: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    counts_for_containment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityGatewaySignal(Base):
    __tablename__ = "security_gateway_signals"
    __table_args__ = (
        Index(
            "ix_security_gateway_signals_correlation",
            "guild_id",
            "correlation_key",
            "first_seen_at",
        ),
        Index(
            "ix_security_gateway_signals_state_action",
            "guild_id",
            "state",
            "discord_action",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_class: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    change_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    linked_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_observations.id"), nullable=True
    )
    discord_action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)


class SecurityIncidentEvent(Base):
    __tablename__ = "security_incident_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=False
    )
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityResponseAction(Base):
    __tablename__ = "security_response_actions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_security_response_actions_idempotency"),
        CheckConstraint(
            "effective_mode <> 'OBSERVE' OR discord_mutation = false",
            name="ck_security_response_observe_no_mutation",
        ),
        CheckConstraint(
            "outcome <> 'WOULD_CONTAIN' OR discord_mutation = false",
            name="ck_security_response_would_contain_no_mutation",
        ),
        CheckConstraint(
            "discord_mutation = false OR effective_mode = 'ENFORCE'",
            name="ck_security_response_mutation_requires_enforce",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=True
    )
    subject_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    effective_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    discord_mutation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rule_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ledger_action_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lease_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discord_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityQuarantine(Base):
    __tablename__ = "security_quarantines"
    __table_args__ = (
        Index(
            "uq_security_quarantines_open",
            "guild_id",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('APPLYING', 'ACTIVE', 'PARTIAL_QUARANTINE')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    prior_role_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    prior_role_perms: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    removed_role_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    residual: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityMaintenanceWindow(Base):
    __tablename__ = "security_maintenance_windows"
    __table_args__ = (
        Index(
            "uq_security_maintenance_windows_active",
            "guild_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_reason: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class SecurityAlertOutbox(Base):
    __tablename__ = "security_alert_outbox"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_security_alert_outbox_dedupe"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("security_incidents.id"), nullable=True
    )
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
