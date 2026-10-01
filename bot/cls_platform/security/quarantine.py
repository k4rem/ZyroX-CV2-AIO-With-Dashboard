"""Reversible role quarantine. No bans, kicks, timeouts, or created roles."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.security.enforce_lock import arm_enforce_session, enforce_unlocked
from cls_platform.security.models import SecurityQuarantine, SecurityResponseAction
from cls_platform.security.response_protocol import EnforceUnavailable

OPEN = ("APPLYING", "ACTIVE", "PARTIAL_QUARANTINE")


class RoleRef:
    def __init__(self, role_id: int):
        self.id = role_id


@dataclass
class QuarantineResult:
    outcome: str
    prior_role_ids: list[int] = field(default_factory=list)
    removed_role_ids: list[int] = field(default_factory=list)
    mutated: bool = False
    reason_token: str | None = None


def _classify(roles: list, bot_top: int) -> tuple[list, list]:
    removable, blocked = [], []
    for role in roles:
        if getattr(role, "managed", False):
            continue
        if getattr(role, "position", 0) >= bot_top:
            blocked.append(role)
        else:
            removable.append(role)
    return removable, blocked


async def _open_row(session, guild_id: int, user_id: int):
    return (
        await session.execute(
            select(SecurityQuarantine).where(
                SecurityQuarantine.guild_id == guild_id,
                SecurityQuarantine.user_id == user_id,
                SecurityQuarantine.status.in_(OPEN),
            )
        )
    ).scalar_one_or_none()


async def apply_quarantine(
    *,
    guild_id: int,
    user_id: int,
    member,
    bot_top_position: int,
    mode: str,
    is_root: bool,
    is_owner: bool,
    owner_known: bool,
    trusted: bool,
    action_class: str = "member.ban",
) -> QuarantineResult:
    roles = list(getattr(member, "roles", []) or [])
    prior = [int(role.id) for role in roles]
    if mode != "ENFORCE" or not enforce_unlocked():
        await _record(guild_id, user_id, "SKIPPED_MODE", action_class, False, "OBSERVE", None)
        return QuarantineResult("SKIPPED_MODE", prior)
    if is_root or is_owner or not owner_known:
        await _record(guild_id, user_id, "NOT_ATTEMPTED_POLICY", action_class, False, "OBSERVE", None)
        return QuarantineResult("NOT_ATTEMPTED_POLICY", prior)
    if trusted:
        await _record(guild_id, user_id, "SKIPPED_TRUSTED", action_class, False, "OBSERVE", None)
        return QuarantineResult("SKIPPED_TRUSTED", prior)

    async with session_scope() as session:
        existing = await _open_row(session, guild_id, user_id)
        if existing is not None:
            return QuarantineResult(
                existing.status,
                list(existing.prior_role_ids or []),
                list(existing.removed_role_ids or []),
            )

    removable, blocked = _classify(roles, bot_top_position)
    action_id = uuid.uuid4()
    token = f"CLS-SEC {action_id}"
    if blocked and not removable:
        outcome, mutated = "UNCONTAINABLE_HIERARCHY", False
    elif not removable:
        outcome, mutated = "ACTIVE", False
    else:
        outcome = "PARTIAL_QUARANTINE" if blocked else "ACTIVE"
        mutated = True

    await _persist_open(
        guild_id, user_id, prior, outcome if not mutated else "APPLYING", action_id, token, action_class, outcome if not mutated else "ACTIVE", mutated
    )
    error = None
    removed: list[int] = []
    if mutated:
        try:
            await member.remove_roles(*removable, reason=token)
            removed = [int(role.id) for role in removable]
        except PermissionError:
            outcome, mutated, error = "FAILED_PERMISSION", False, "permission"
        except Exception as exc:  # noqa: BLE001
            outcome = "FAILED_PERMISSION" if type(exc).__name__ == "Forbidden" else "FAILED_DISCORD"
            mutated = False
            error = str(exc)[:500]
        await _finish(guild_id, user_id, action_id, outcome, removed, blocked, error, mutated)
    return QuarantineResult(outcome, prior, removed, mutated, token)


async def release_quarantine(*, guild_id: int, user_id: int, member, actor_is_root: bool) -> QuarantineResult:
    if not actor_is_root:
        raise EnforceUnavailable("Quarantine release is Root only")
    if not enforce_unlocked():
        raise EnforceUnavailable("ENFORCE is locked")
    async with session_scope() as session:
        row = await _open_row(session, guild_id, user_id)
        if row is None:
            return QuarantineResult("RELEASED")
        prior = list(row.prior_role_ids or [])
        row_id = row.id
    present = {int(role.id) for role in getattr(member, "roles", []) or []}
    wanted = [role_id for role_id in prior if role_id not in present]
    token = f"CLS-SEC release {row_id}"
    try:
        if wanted:
            await member.add_roles(*[RoleRef(role_id) for role_id in wanted], reason=token)
        outcome, mutated, error = "RELEASED", bool(wanted), None
    except Exception as exc:  # noqa: BLE001
        outcome, mutated, error = "RELEASE_FAILED", False, str(exc)[:500]
    async with session_scope() as session:
        await arm_enforce_session(session)
        row = await _open_row(session, guild_id, user_id)
        if row is not None:
            row.status = outcome
        session.add(
            SecurityResponseAction(
                guild_id=guild_id,
                subject_id=user_id,
                idempotency_key=f"release:{guild_id}:{user_id}:{uuid.uuid4()}",
                outcome=outcome,
                effective_mode="ENFORCE",
                discord_mutation=mutated,
                ledger_action_class="quarantine.release",
                reason_token=token,
                discord_error=error,
            )
        )
    return QuarantineResult(outcome, prior, mutated=mutated, reason_token=token)


async def _persist_open(guild_id, user_id, prior, q_status, action_id, token, action_class, response_outcome, mutated):
    async with session_scope() as session:
        await arm_enforce_session(session)
        session.add(
            SecurityQuarantine(
                guild_id=guild_id,
                user_id=user_id,
                status=q_status,
                prior_role_ids=prior,
            )
        )
        session.add(
            SecurityResponseAction(
                id=action_id,
                guild_id=guild_id,
                subject_id=user_id,
                idempotency_key=f"quarantine:{guild_id}:{user_id}:{action_id}",
                outcome=response_outcome,
                effective_mode="ENFORCE",
                discord_mutation=mutated,
                ledger_action_class=action_class,
                reason_token=token,
            )
        )


async def _finish(guild_id, user_id, action_id, outcome, removed, blocked, error, mutated):
    async with session_scope() as session:
        await arm_enforce_session(session)
        row = await _open_row(session, guild_id, user_id)
        if row is not None:
            row.status = outcome
            row.removed_role_ids = removed
            row.residual = {"blocked": [int(role.id) for role in blocked], "error": error}
        action = (
            await session.execute(select(SecurityResponseAction).where(SecurityResponseAction.id == action_id))
        ).scalar_one()
        action.outcome = outcome
        action.discord_mutation = mutated
        action.discord_error = error


async def _record(guild_id, user_id, outcome, action_class, mutated, mode, token):
    async with session_scope() as session:
        session.add(
            SecurityResponseAction(
                guild_id=guild_id,
                subject_id=user_id,
                idempotency_key=f"skip:{guild_id}:{user_id}:{outcome}:{uuid.uuid4()}",
                outcome=outcome,
                effective_mode=mode,
                discord_mutation=mutated,
                ledger_action_class=action_class,
                reason_token=token,
                explanation=outcome,
            )
        )
