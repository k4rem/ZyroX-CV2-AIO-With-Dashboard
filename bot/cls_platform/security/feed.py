"""Audit feed, gateway signals, and coalesced fallback fetch. Record only."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cls_platform.database import session_scope
from cls_platform.security.attribution import (
    AuditCandidate,
    AttributionState,
    classify_targetless_candidates,
    confirmed_prerequisites,
    correlation_key,
    counts_for_containment,
    is_late,
    times_match,
    snowflake_from_time,
    targets_comparable,
)
from cls_platform.security.config import ensure_guild_config
from cls_platform.security.constants import (
    FETCH_LIMIT,
    GATEWAY_DEDUPE_MAX_S,
    PROPOSED_FETCH_DELAYS_S,
    PROPOSED_SKEW_S,
    PROPOSED_T_ATTR_S,
    AttributionState as Attr,
)
from cls_platform.security.guild_gate import security_guild_eligible
from cls_platform.security.models import (
    SecurityAlertOutbox,
    SecurityGatewaySignal,
    SecurityGuildState,
    SecurityObservation,
    SecurityResponseAction,
)
from cls_platform.security.taxonomy import action_spec
from cls_platform.services.audit import _redact

logger = logging.getLogger(__name__)

Sleep = Callable[[float], Awaitable[None]]
Clock = Callable[[], datetime]
BUFFER_LIMIT = 1000

_locks: dict[int, asyncio.Lock] = {}
_buffers: dict[int, deque] = defaultdict(lambda: deque(maxlen=BUFFER_LIMIT))
_dropped: dict[int, int] = defaultdict(int)


def guild_lock(guild_id: int) -> asyncio.Lock:
    lock = _locks.get(guild_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[guild_id] = lock
    return lock


def dropped_signal_count(guild_id: int) -> int:
    return _dropped[guild_id]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FetchPage:
    entries: list[AuditCandidate] = field(default_factory=list)
    error: Optional[str] = None
    retry_after: float = 0.0


class AuditLogSource:
    async def fetch(
        self,
        guild_id: int,
        discord_action: str,
        *,
        after_id: int,
        limit: int,
    ) -> FetchPage:
        raise NotImplementedError


class TokenBucket:
    def __init__(self, rate: float = 1.0, burst: int = 3) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.updated = 0.0
        self.waits: list[float] = []

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.updated)
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.updated = now

    async def acquire(self, *, now_fn: Callable[[], float], sleep: Sleep) -> None:
        while True:
            now = now_fn()
            self._refill(now)
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait = (1 - self.tokens) / self.rate
            self.waits.append(wait)
            await sleep(wait)


class ObservationFeed:
    def __init__(
        self,
        source: Optional[AuditLogSource] = None,
        *,
        clock: Clock = _utcnow,
        sleep: Sleep = asyncio.sleep,
        monotonic: Optional[Callable[[], float]] = None,
        cls_user_id: Optional[int] = None,
    ) -> None:
        self.source = source
        self.clock = clock
        self.sleep = sleep
        self.monotonic = monotonic or (lambda: self.clock().timestamp())
        self.cls_user_id = cls_user_id
        self._buckets: dict[int, TokenBucket] = {}
        self._tasks: dict[tuple[int, str], asyncio.Task] = {}
        self.fetch_calls = 0

    def _bucket(self, guild_id: int) -> TokenBucket:
        bucket = self._buckets.get(guild_id)
        if bucket is None:
            bucket = TokenBucket()
            self._buckets[guild_id] = bucket
        return bucket

    async def record_gateway_signal(
        self,
        *,
        guild_id: int,
        action_class: str,
        target_id: Optional[int],
        change_digest: str,
        discord_action: Optional[str],
        seen_at: Optional[datetime] = None,
        schedule: bool = True,
    ) -> Optional[uuid.UUID]:
        if not security_guild_eligible(guild_id):
            return None
        spec = action_spec(action_class)
        if not spec.active or not spec.gateway_visible:
            return None
        moment = seen_at or self.clock()
        try:
            signal_id = await self._insert_signal(
                guild_id=guild_id,
                action_class=action_class,
                target_id=target_id,
                change_digest=change_digest,
                discord_action=discord_action or (spec.discord_actions[0] if spec.discord_actions else None),
                seen_at=moment,
            )
        except Exception:
            logger.exception("security observation buffer guild=%s", guild_id)
            self._buffer(guild_id, action_class, target_id, change_digest)
            return None
        if schedule and signal_id is not None:
            action_name = discord_action or (spec.discord_actions[0] if spec.discord_actions else None)
            if action_name:
                pending = await self._signal_is_pending(signal_id)
                if pending:
                    self.schedule_fallback(guild_id, action_name)
        return signal_id

    def _buffer(self, guild_id: int, action_class: str, target_id: Optional[int], digest: str) -> None:
        buf = _buffers[guild_id]
        if len(buf) >= BUFFER_LIMIT:
            _dropped[guild_id] += 1
            return
        buf.append((action_class, target_id, digest))

    async def _insert_signal(
        self,
        *,
        guild_id: int,
        action_class: str,
        target_id: Optional[int],
        change_digest: str,
        discord_action: Optional[str],
        seen_at: datetime,
    ) -> Optional[uuid.UUID]:
        await ensure_guild_config(guild_id)
        key = correlation_key(guild_id, action_class, target_id, change_digest)
        async with guild_lock(guild_id):
            async with session_scope() as session:
                config_window = await self._dedupe_window(session, guild_id)
                window_start = seen_at - timedelta(seconds=config_window)
                existing = (
                    await session.execute(
                        select(SecurityGatewaySignal)
                        .where(
                            SecurityGatewaySignal.guild_id == guild_id,
                            SecurityGatewaySignal.correlation_key == key,
                            SecurityGatewaySignal.state == "PENDING",
                            SecurityGatewaySignal.first_seen_at >= window_start,
                        )
                        .order_by(SecurityGatewaySignal.first_seen_at.asc())
                    )
                ).scalars().first()
                if existing is not None:
                    existing.duplicate_count = int(existing.duplicate_count) + 1
                    existing.last_seen_at = seen_at
                    await session.flush()
                    return existing.id
                linked = await self._existing_observation(
                    session, guild_id, action_class, target_id, seen_at
                )
                signal = SecurityGatewaySignal(
                    guild_id=guild_id,
                    action_class=action_class,
                    target_id=target_id,
                    change_digest=change_digest,
                    correlation_key=key,
                    state="LINKED" if linked is not None else "PENDING",
                    duplicate_count=1,
                    first_seen_at=seen_at,
                    last_seen_at=seen_at,
                    linked_observation_id=linked,
                    discord_action=discord_action,
                    payload=_redact({"action_class": action_class, "target_id": target_id}),
                )
                session.add(signal)
                if linked is not None:
                    await session.execute(
                        update(SecurityObservation)
                        .where(SecurityObservation.id == linked)
                        .values(corroborated=True)
                    )
                await session.flush()
                return signal.id

    async def _dedupe_window(self, session, guild_id: int) -> int:
        from cls_platform.security.models import SecurityGuildConfig

        row = (
            await session.execute(
                select(SecurityGuildConfig.gateway_dedupe_s).where(
                    SecurityGuildConfig.guild_id == guild_id
                )
            )
        ).scalar_one()
        return min(int(row), GATEWAY_DEDUPE_MAX_S)

    async def _existing_observation(self, session, guild_id, action_class, target_id, seen_at):
        stmt = select(SecurityObservation).where(
            SecurityObservation.guild_id == guild_id,
            SecurityObservation.action_class == action_class,
            SecurityObservation.audit_entry_id.is_not(None),
        )
        if targets_comparable(action_class):
            stmt = stmt.where(SecurityObservation.target_id == target_id)
        rows = (await session.execute(stmt)).scalars().all()
        for row in rows:
            if row.entry_created_at is None:
                continue
            if times_match(row.entry_created_at, seen_at):
                return row.id
        return None

    async def ingest_audit(
        self,
        candidate: AuditCandidate,
        *,
        guild_id: int,
        received_at: Optional[datetime] = None,
        source: str = "audit_push",
    ) -> Optional[uuid.UUID]:
        if not security_guild_eligible(guild_id):
            return None
        spec = action_spec(candidate.action_class)
        if not spec.active:
            return None
        moment = received_at or self.clock()
        late = is_late(
            received_at=moment,
            entry_created_at=candidate.entry_created_at,
            source=source,
        )
        state, actor_id, reason, candidates = await self._classify(guild_id, candidate, source)
        if state is AttributionState.CONFIRMED and not confirmed_prerequisites(candidate):
            state = AttributionState.UNATTRIBUTED
            actor_id = None
            reason = "missing actor or comparable target"
        eligible = counts_for_containment(state=state, late=late)
        audit_id = None if state in {AttributionState.AMBIGUOUS, AttributionState.UNATTRIBUTED} else candidate.audit_entry_id
        if state is AttributionState.PROBABLE:
            audit_id = candidate.audit_entry_id
        try:
            obs_id = await self._insert_observation(
                guild_id=guild_id,
                candidate=candidate,
                received_at=moment,
                source=source,
                late=late,
                state=state,
                actor_id=actor_id,
                reason=reason,
                candidate_ids=candidates,
                counts=eligible,
                audit_id=audit_id,
            )
        except Exception:
            logger.exception("security audit buffer guild=%s", guild_id)
            self._buffer(guild_id, candidate.action_class, candidate.target_id, candidate.change_digest)
            return None
        if obs_id is not None and audit_id is not None:
            await self._link_signals(guild_id, candidate, obs_id, late)
            await self._advance_watermark(guild_id, audit_id)
        if obs_id is not None:
            await self._attach_incident(obs_id, moment)
        return obs_id

    async def _classify(self, guild_id: int, candidate: AuditCandidate, source: str):
        actor = candidate.actor_id
        ids = [actor] if actor is not None else []
        if self.cls_user_id is not None and actor == self.cls_user_id:
            matched = await self._ledger_match(guild_id, candidate)
            if matched:
                return AttributionState.SELF, actor, "response ledger match", ids
            return AttributionState.CLS_PROXIED, actor, "cls actor without security ledger match", ids
        if not confirmed_prerequisites(candidate):
            return AttributionState.UNATTRIBUTED, None, "audit entry missing actor or target", ids
        if targets_comparable(candidate.action_class):
            return AttributionState.CONFIRMED, actor, source, ids
        return AttributionState.PROBABLE, actor, "no comparable target", ids

    async def _ledger_match(self, guild_id: int, candidate: AuditCandidate) -> bool:
        async with session_scope() as session:
            rows = (
                await session.execute(
                    select(SecurityResponseAction).where(SecurityResponseAction.guild_id == guild_id)
                )
            ).scalars().all()
        for row in rows:
            if candidate.target_id is not None and row.subject_id == candidate.target_id:
                return True
            if row.subject_id == candidate.actor_id:
                return True
        return False

    async def _insert_observation(self, **kwargs) -> Optional[uuid.UUID]:
        candidate: AuditCandidate = kwargs["candidate"]
        values = dict(
            id=uuid.uuid4(),
            guild_id=kwargs["guild_id"],
            audit_entry_id=kwargs["audit_id"],
            action_class=candidate.action_class,
            discord_action=candidate.discord_action,
            target_id=candidate.target_id,
            actor_id=kwargs["actor_id"],
            attribution_state=kwargs["state"].value,
            late=kwargs["late"],
            corroborated=False,
            received_at=kwargs["received_at"],
            entry_created_at=candidate.entry_created_at,
            source=kwargs["source"],
            severity=action_spec(candidate.action_class).severity,
            change_digest=candidate.change_digest or None,
            attribution_method=kwargs["source"],
            attribution_reason=kwargs["reason"],
            candidate_actor_ids=kwargs["candidate_ids"] or None,
            permission_diff=_redact(candidate.permission_diff) if candidate.permission_diff else None,
            counts_for_containment=kwargs["counts"],
        )
        async with session_scope() as session:
            if kwargs["audit_id"] is None:
                row = SecurityObservation(**values)
                session.add(row)
                await session.flush()
                return row.id
            stmt = (
                pg_insert(SecurityObservation)
                .values(**values)
                .on_conflict_do_nothing(
                    index_elements=["guild_id", "audit_entry_id"],
                    index_where=text("audit_entry_id IS NOT NULL"),
                )
                .returning(SecurityObservation.id)
            )
            inserted = (await session.execute(stmt)).scalar_one_or_none()
            if inserted is not None:
                return inserted
            existing = (
                await session.execute(
                    select(SecurityObservation.id).where(
                        SecurityObservation.guild_id == kwargs["guild_id"],
                        SecurityObservation.audit_entry_id == kwargs["audit_id"],
                    )
                )
            ).scalar_one()
            return existing

    async def _link_signals(self, guild_id: int, candidate: AuditCandidate, observation_id, late: bool) -> None:
        async with guild_lock(guild_id):
            async with session_scope() as session:
                rows = (
                    await session.execute(
                        select(SecurityGatewaySignal)
                        .where(
                            SecurityGatewaySignal.guild_id == guild_id,
                            SecurityGatewaySignal.action_class == candidate.action_class,
                            SecurityGatewaySignal.state == "PENDING",
                        )
                        .order_by(SecurityGatewaySignal.first_seen_at.asc())
                    )
                ).scalars().all()
                matching = []
                for row in rows:
                    if not times_match(candidate.entry_created_at, row.first_seen_at):
                        continue
                    if targets_comparable(candidate.action_class) and row.target_id != candidate.target_id:
                        continue
                    matching.append(row)
                if not matching:
                    await self._supersede_expired(session, guild_id, candidate, observation_id)
                    return
                earliest = matching[0]
                earliest.state = "LINKED"
                earliest.linked_observation_id = observation_id
                await session.execute(
                    update(SecurityObservation)
                    .where(SecurityObservation.id == observation_id)
                    .values(corroborated=True)
                )
                for other in matching[1:]:
                    if other.correlation_key == earliest.correlation_key:
                        other.state = "SUPERSEDED"
                        other.linked_observation_id = observation_id
                await self._supersede_expired(session, guild_id, candidate, observation_id)

    async def _supersede_expired(self, session, guild_id, candidate, observation_id) -> None:
        rows = (
            await session.execute(
                select(SecurityObservation).where(
                    SecurityObservation.guild_id == guild_id,
                    SecurityObservation.action_class == candidate.action_class,
                    SecurityObservation.attribution_state.in_(
                        [Attr.UNATTRIBUTED.value, Attr.AMBIGUOUS.value, Attr.PROBABLE.value]
                    ),
                    SecurityObservation.audit_entry_id.is_(None),
                    SecurityObservation.id != observation_id,
                )
            )
        ).scalars().all()
        for row in rows:
            if targets_comparable(candidate.action_class) and row.target_id not in {None, candidate.target_id}:
                continue
            if row.received_at and candidate.entry_created_at:
                if not times_match(candidate.entry_created_at, row.received_at):
                    continue
            row.superseded_by_observation_id = observation_id

    async def _advance_watermark(self, guild_id: int, audit_entry_id: int) -> None:
        async with session_scope() as session:
            state = (
                await session.execute(
                    select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id)
                )
            ).scalar_one_or_none()
            if state is None:
                return
            current = state.last_audit_entry_id or 0
            if audit_entry_id > current:
                state.last_audit_entry_id = audit_entry_id

    def schedule_fallback(self, guild_id: int, discord_action: str) -> None:
        key = (guild_id, discord_action)
        task = self._tasks.get(key)
        if task is not None and not task.done():
            return
        self._tasks[key] = asyncio.create_task(self.run_fallback(guild_id, discord_action))

    async def run_fallback(self, guild_id: int, discord_action: str) -> None:
        if self.source is None:
            await self.sleep(float(PROPOSED_T_ATTR_S))
            await self.expire_pending(guild_id, discord_action, reason="no audit source configured")
            return
        start = self.clock()
        for offset in PROPOSED_FETCH_DELAYS_S:
            wait = offset - (self.clock() - start).total_seconds()
            if wait > 0:
                await self.sleep(wait)
            if not await self._has_pending(guild_id, discord_action):
                return
            await self._bucket(guild_id).acquire(now_fn=self.monotonic, sleep=self.sleep)
            after_id = await self._fetch_after(guild_id)
            self.fetch_calls += 1
            page = await self.source.fetch(
                guild_id, discord_action, after_id=after_id, limit=FETCH_LIMIT
            )
            if page.error == "forbidden":
                await self._forbid(guild_id, discord_action)
                return
            if page.error == "rate_limited":
                delay = max(0.0, float(page.retry_after or 0))
                if delay:
                    await self.sleep(delay)
                continue
            for entry in page.entries:
                if entry.discord_action != discord_action and entry.action_class:
                    pass
                await self.ingest_audit(entry, guild_id=guild_id, source="audit_fetch", received_at=self.clock())
        await self.expire_pending(guild_id, discord_action)

    async def _signal_is_pending(self, signal_id: uuid.UUID) -> bool:
        async with session_scope() as session:
            state = (
                await session.execute(
                    select(SecurityGatewaySignal.state).where(SecurityGatewaySignal.id == signal_id)
                )
            ).scalar_one_or_none()
            return state == "PENDING"

    async def _has_pending(self, guild_id: int, discord_action: str) -> bool:
        async with session_scope() as session:
            row = (
                await session.execute(
                    select(SecurityGatewaySignal.id).where(
                        SecurityGatewaySignal.guild_id == guild_id,
                        SecurityGatewaySignal.discord_action == discord_action,
                        SecurityGatewaySignal.state == "PENDING",
                    )
                )
            ).first()
            return row is not None

    async def _fetch_after(self, guild_id: int) -> int:
        async with session_scope() as session:
            state = (
                await session.execute(
                    select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id)
                )
            ).scalar_one_or_none()
            watermark = int(state.last_audit_entry_id or 0) if state else 0
            earliest = (
                await session.execute(
                    select(SecurityGatewaySignal.first_seen_at)
                    .where(
                        SecurityGatewaySignal.guild_id == guild_id,
                        SecurityGatewaySignal.state == "PENDING",
                    )
                    .order_by(SecurityGatewaySignal.first_seen_at.asc())
                )
            ).scalars().first()
        skewed = 0
        if earliest is not None:
            skewed = snowflake_from_time(earliest - timedelta(seconds=PROPOSED_SKEW_S))
        return max(watermark, skewed)

    async def _forbid(self, guild_id: int, discord_action: str) -> None:
        await self.expire_pending(guild_id, discord_action, reason="audit log forbidden")
        hour = self.clock().strftime("%Y%m%d%H")
        dedupe = f"health:view_audit_log:{guild_id}:{hour}"
        async with session_scope() as session:
            await session.execute(
                pg_insert(SecurityAlertOutbox)
                .values(
                    id=uuid.uuid4(),
                    guild_id=guild_id,
                    dedupe_key=dedupe,
                    kind="permission_health",
                    status="PENDING",
                    attempts=0,
                    next_attempt_at=self.clock(),
                    payload=_redact({"reason": "view_audit_log forbidden", "guild_id": str(guild_id)}),
                )
                .on_conflict_do_nothing(index_elements=["dedupe_key"])
            )

    async def _attach_incident(self, observation_id: uuid.UUID, moment: datetime) -> None:
        try:
            from cls_platform.security.incidents import attach_observation

            await attach_observation(observation_id, now=moment)
        except Exception:
            logger.exception("security incident attach failed observation=%s", observation_id)

    async def expire_pending(self, guild_id: int, discord_action: str, reason: str = "no audit entry by T_attr") -> None:
        created_ids: list[uuid.UUID] = []
        async with guild_lock(guild_id):
            async with session_scope() as session:
                rows = (
                    await session.execute(
                        select(SecurityGatewaySignal).where(
                            SecurityGatewaySignal.guild_id == guild_id,
                            SecurityGatewaySignal.discord_action == discord_action,
                            SecurityGatewaySignal.state == "PENDING",
                        )
                    )
                ).scalars().all()
                for row in rows:
                    row.state = "EXPIRED_UNATTRIBUTED"
                    obs = SecurityObservation(
                        guild_id=guild_id,
                        audit_entry_id=None,
                        action_class=row.action_class,
                        discord_action=discord_action,
                        target_id=row.target_id,
                        actor_id=None,
                        attribution_state=AttributionState.UNATTRIBUTED.value,
                        late=False,
                        corroborated=False,
                        received_at=self.clock(),
                        entry_created_at=None,
                        source="gateway",
                        severity=action_spec(row.action_class).severity,
                        change_digest=row.change_digest,
                        attribution_method="gateway_expiry",
                        attribution_reason=reason,
                        counts_for_containment=False,
                    )
                    session.add(obs)
                    await session.flush()
                    row.linked_observation_id = obs.id
                    created_ids.append(obs.id)
        for obs_id in created_ids:
            await self._attach_incident(obs_id, self.clock())

    async def attribute_targetless(
        self,
        *,
        guild_id: int,
        action_class: str,
        candidates: list[AuditCandidate],
        received_at: datetime,
    ) -> AttributionState:
        """Fallback classification when Discord has no comparable target."""
        in_window = candidates
        state = classify_targetless_candidates(in_window)
        if state is AttributionState.PROBABLE:
            await self.ingest_audit(in_window[0], guild_id=guild_id, received_at=received_at, source="audit_fetch")
            async with session_scope() as session:
                row = (
                    await session.execute(
                        select(SecurityObservation)
                        .where(
                            SecurityObservation.guild_id == guild_id,
                            SecurityObservation.audit_entry_id == in_window[0].audit_entry_id,
                        )
                    )
                ).scalar_one()
                row.attribution_state = AttributionState.PROBABLE.value
                row.counts_for_containment = False
                row.attribution_reason = "single targetless candidate"
            return state
        obs = SecurityObservation(
            guild_id=guild_id,
            audit_entry_id=None,
            action_class=action_class,
            attribution_state=state.value,
            late=False,
            received_at=received_at,
            source="audit_fetch",
            severity=action_spec(action_class).severity,
            attribution_reason="candidate evidence without a chosen actor" if state is AttributionState.AMBIGUOUS else "no candidate",
            candidate_actor_ids=[item.actor_id for item in in_window if item.actor_id],
            counts_for_containment=False,
            actor_id=None,
        )
        async with session_scope() as session:
            session.add(obs)
        return state

    async def reconcile_new_session(self, *, resumed: bool, entries: list[tuple[int, AuditCandidate]]) -> int:
        if resumed:
            return 0
        written = 0
        for guild_id, entry in entries:
            obs = await self.ingest_audit(
                entry,
                guild_id=guild_id,
                source="reconciliation",
                received_at=self.clock(),
            )
            if obs is not None:
                written += 1
        return written
