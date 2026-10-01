"""Pure OBSERVE policy evaluation. No Discord I/O.

would_contain decisions are evidence. They are never replayed as containment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cls_platform.security.config import DEFAULT_POLICIES
from cls_platform.security.constants import SecurityMode
from cls_platform.security.tiers import CONTAINMENT_SIGNAL_TIERS

DESTRUCTIVE_CLASSES = frozenset(
    {"channel.delete", "role.delete", "member.ban", "member.kick", "webhook.create"}
)


@dataclass(frozen=True)
class Subject:
    guild_id: int
    user_id: int
    is_bot: bool = False
    is_guild_owner: bool = False
    is_root: bool = False
    owner_known: bool = True


@dataclass(frozen=True)
class PolicyObservation:
    id: str
    guild_id: int
    action_class: str
    audit_entry_id: int | None
    target_id: int | None
    actor_id: int | None
    attribution_state: str
    late: bool
    at: datetime
    permission_tier: str | None = None
    everyone_grant: bool = False


@dataclass(frozen=True)
class TrustSnapshot:
    trusted: bool = False
    scopes: tuple[str, ...] = ()


@dataclass
class Decision:
    rule_id: str
    explanation: str
    matched_observation_ids: list[str]
    severity: str
    containment_eligible: bool
    effective_mode: str
    would_contain: bool
    late_excluded: bool
    suppression_reason: str | None = None
    replayable: bool = False
    development_proposal: bool = True
    matched_audit_ids: list[int] = field(default_factory=list)


def effective_mode(configured: str, *, maintenance_active: bool) -> str:
    if configured == SecurityMode.OFF.value:
        return SecurityMode.OFF.value
    if maintenance_active:
        return SecurityMode.OBSERVE.value
    if configured == SecurityMode.ENFORCE.value:
        from cls_platform.security.enforce_lock import enforce_unlocked

        if enforce_unlocked():
            return SecurityMode.ENFORCE.value
    return SecurityMode.OBSERVE.value


def evaluate(
    subject: Subject,
    observations: list[PolicyObservation],
    config: dict | None,
    trust_snapshot: TrustSnapshot,
    now: datetime,
    *,
    configured_mode: str = "OBSERVE",
    maintenance_active: bool = False,
) -> list[Decision]:
    """Return explainable decisions. Late evidence never produces would_contain."""
    mode = effective_mode(configured_mode, maintenance_active=maintenance_active)
    policies = {row["action_class"]: row for row in DEFAULT_POLICIES}
    if config:
        policies.update(config)
    own = [
        item
        for item in observations
        if item.guild_id == subject.guild_id
        and (
            item.actor_id == subject.user_id
            or (subject.is_bot and item.action_class == "bot.add" and item.target_id == subject.user_id)
        )
    ]
    decisions: list[Decision] = []
    decisions.extend(_rate_rules(subject, own, policies, trust_snapshot, now, mode))
    decisions.extend(_single_rules(subject, own, policies, trust_snapshot, mode))
    decisions.extend(_sequence_rules(subject, own, policies, trust_snapshot, now, mode))
    if subject.is_bot:
        decisions.extend(_bot_rules(subject, own, trust_snapshot, mode))
    return [item for item in decisions if item.explanation]


def _eligible(item: PolicyObservation, subject: Subject) -> bool:
    if item.late or item.attribution_state != "CONFIRMED" or item.audit_entry_id is None:
        return False
    if item.permission_tier in {None, "ELEVATED", "OBSERVABILITY"} and item.action_class.endswith("permission"):
        return False
    if item.permission_tier == "OBSERVABILITY":
        return False
    if item.permission_tier == "ELEVATED":
        return False
    if not subject.is_bot and item.action_class == "bot.add":
        return False
    return True


def _window(items: list[PolicyObservation], now: datetime, seconds: int) -> list[PolicyObservation]:
    if seconds <= 0:
        return items
    start = now - timedelta(seconds=seconds)
    return [item for item in items if item.at >= start]


def _distinct(items: list[PolicyObservation], by_target: bool) -> list[PolicyObservation]:
    seen: set = set()
    chosen = []
    for item in items:
        key = item.target_id if by_target else item.audit_entry_id
        if key in seen:
            continue
        seen.add(key)
        chosen.append(item)
    return chosen


def _finish(
    *,
    rule_id: str,
    explanation: str,
    matched: list[PolicyObservation],
    severity: str,
    eligible_flag: bool,
    mode: str,
    subject: Subject,
    trust_snapshot: TrustSnapshot,
    late_present: bool,
) -> Decision:
    suppression = _suppression(subject, trust_snapshot, rule_id)
    would = bool(eligible_flag and matched and suppression is None and mode == SecurityMode.OBSERVE.value)
    if mode != SecurityMode.OBSERVE.value:
        would = False
    return Decision(
        rule_id=rule_id,
        explanation=explanation + " Development proposal, not a production threshold.",
        matched_observation_ids=[item.id for item in matched],
        matched_audit_ids=[int(item.audit_entry_id) for item in matched if item.audit_entry_id],
        severity=severity,
        containment_eligible=eligible_flag and suppression is None,
        effective_mode=mode,
        would_contain=would,
        late_excluded=late_present,
        suppression_reason=suppression,
        replayable=False,
    )


def rule_action_classes(rule_id: str) -> frozenset[str]:
    if rule_id == "member.ban_or_kick":
        return frozenset({"member.ban", "member.kick"})
    if rule_id == "aggregate.destructive":
        return DESTRUCTIVE_CLASSES
    if rule_id == "sequence.self_escalation":
        return frozenset({"role.permission_escalation", "member.privileged_role_grant"}) | DESTRUCTIVE_CLASSES
    if rule_id == "sequence.cls_impairment":
        return frozenset({"cls.impairment"}) | DESTRUCTIVE_CLASSES
    if rule_id in {
        "single.everyone_critical_control",
        "single.critical_control_grant",
        "tier.elevated",
        "tier.observability",
    }:
        return frozenset({"role.permission_escalation", "member.privileged_role_grant"})
    if rule_id == "bot.add":
        return frozenset({"bot.add"})
    if rule_id == "bot.privilege_change":
        return frozenset({"bot.privilege_change"})
    if rule_id == "member.prune":
        return frozenset({"member.prune"})
    return frozenset({rule_id})


def trust_covers(scopes: tuple[str, ...] | list[str], rule_id: str) -> bool:
    """Scopes are action classes. Empty is not a wildcard. '*' is the only wildcard."""
    if "*" in scopes:
        return True
    if not scopes:
        return False
    return rule_action_classes(rule_id).issubset(set(scopes))


def _suppression(subject: Subject, trust_snapshot: TrustSnapshot, rule_id: str) -> str | None:
    if subject.is_root:
        return "root"
    if subject.is_guild_owner:
        return "guild_owner"
    if not subject.owner_known:
        return "owner_unknown"
    if trust_snapshot.trusted and trust_covers(trust_snapshot.scopes, rule_id):
        return "trusted"
    return None


def _policy_active(policies: dict, rule_id: str) -> dict | None:
    policy = policies.get(rule_id)
    if not policy or not policy.get("enabled", True):
        return None
    return policy


def _rate_rules(subject, observations, policies, trust_snapshot, now, mode) -> list[Decision]:
    found = []
    specs = [
        ("channel.delete", "H"),
        ("role.delete", "H"),
        ("member.ban_or_kick", "H"),
        ("webhook.create", "M"),
        ("aggregate.destructive", "H"),
    ]
    for rule_id, severity in specs:
        policy = _policy_active(policies, rule_id)
        if policy is None:
            continue
        pool = observations
        if rule_id == "member.ban_or_kick":
            pool = [item for item in observations if item.action_class in {"member.ban", "member.kick"}]
        elif rule_id == "aggregate.destructive":
            pool = [item for item in observations if item.action_class in DESTRUCTIVE_CLASSES]
        elif rule_id != "aggregate.destructive":
            pool = [item for item in observations if item.action_class == rule_id]
        late_present = any(item.late for item in pool)
        eligible = [item for item in pool if _eligible(item, subject)]
        eligible = _distinct(_window(eligible, now, int(policy["window_s"])), policy.get("distinct_targets", False))
        if len(eligible) < int(policy["threshold"]):
            dropped = [item for item in pool if item.late or item.attribution_state != "CONFIRMED"]
            if dropped and len(eligible) + len(dropped) >= int(policy["threshold"]):
                found.append(
                    Decision(
                        rule_id=rule_id,
                        explanation=(
                            f"{rule_id} would meet the development proposal only by including "
                            "late or non-CONFIRMED evidence, which is excluded."
                        ),
                        matched_observation_ids=[item.id for item in eligible],
                        severity=severity,
                        containment_eligible=False,
                        effective_mode=mode,
                        would_contain=False,
                        late_excluded=True,
                        replayable=False,
                    )
                )
            continue
        found.append(
            _finish(
                rule_id=rule_id,
                explanation=(
                    f"{rule_id} reached {len(eligible)} distinct audit entries "
                    f"in {policy['window_s']}s (proposal threshold {policy['threshold']})."
                ),
                matched=eligible,
                severity=severity,
                eligible_flag=bool(policy["containment_eligible"]),
                mode=mode,
                subject=subject,
                trust_snapshot=trust_snapshot,
                late_present=late_present,
            )
        )
    return found


def _single_rules(subject, observations, policies, trust_snapshot, mode) -> list[Decision]:
    found = []
    everyone = [
        item
        for item in observations
        if item.everyone_grant and item.permission_tier == "CRITICAL_CONTROL" and _eligible(item, subject)
    ]
    if everyone and _policy_active(policies, "single.everyone_critical_control"):
        policy = policies["single.everyone_critical_control"]
        found.append(
            _finish(
                rule_id="single.everyone_critical_control",
                explanation="CONFIRMED CRITICAL_CONTROL bits were added to @everyone.",
                matched=everyone[: int(policy["threshold"])],
                severity="C",
                eligible_flag=True,
                mode=mode,
                subject=subject,
                trust_snapshot=trust_snapshot,
                late_present=any(item.late and item.everyone_grant for item in observations),
            )
        )
    grants = [
        item
        for item in observations
        if item.action_class in {"role.permission_escalation", "member.privileged_role_grant"}
        and item.permission_tier == "CRITICAL_CONTROL"
        and not item.everyone_grant
        and _eligible(item, subject)
    ]
    if grants:
        found.append(
            _finish(
                rule_id="single.critical_control_grant",
                explanation="CRITICAL_CONTROL was granted outside @everyone. Alert only.",
                matched=grants[:1],
                severity="C",
                eligible_flag=False,
                mode=mode,
                subject=subject,
                trust_snapshot=trust_snapshot,
                late_present=False,
            )
        )
    prunes = [
        item
        for item in observations
        if item.action_class == "member.prune"
        and item.actor_id is not None
        and item.attribution_state in {"CONFIRMED", "PROBABLE"}
        and not item.late
    ]
    if prunes:
        found.append(
            _finish(
                rule_id="member.prune",
                explanation="A member prune is a critical alert only.",
                matched=prunes[:1],
                severity="C",
                eligible_flag=False,
                mode=mode,
                subject=subject,
                trust_snapshot=trust_snapshot,
                late_present=any(item.late and item.action_class == "member.prune" for item in observations),
            )
        )
    elevated = [item for item in observations if item.permission_tier == "ELEVATED" and not item.late]
    if elevated:
        found.append(
            Decision(
                rule_id="tier.elevated",
                explanation="ELEVATED permission changes are alert-only and never containment-eligible.",
                matched_observation_ids=[item.id for item in elevated],
                severity="M",
                containment_eligible=False,
                effective_mode=mode,
                would_contain=False,
                late_excluded=False,
                replayable=False,
            )
        )
    impaired = [
        item
        for item in observations
        if item.action_class == "cls.impairment" and item.actor_id is not None and not item.late
    ]
    if impaired:
        found.append(
            Decision(
                rule_id="cls.impairment",
                explanation="CLS permissions or position were reduced. Critical alert only until a later destructive action.",
                matched_observation_ids=[item.id for item in impaired[:1]],
                severity="C",
                containment_eligible=False,
                effective_mode=mode,
                would_contain=False,
                late_excluded=False,
                replayable=False,
            )
        )
    observed = [item for item in observations if item.permission_tier == "OBSERVABILITY"]
    if observed:
        found.append(
            Decision(
                rule_id="tier.observability",
                explanation="View Audit Log is recorded for health and is not a policy trigger.",
                matched_observation_ids=[item.id for item in observed],
                severity="L",
                containment_eligible=False,
                effective_mode=mode,
                would_contain=False,
                late_excluded=False,
                replayable=False,
            )
        )
    return found


def _sequence_rules(subject, observations, policies, trust_snapshot, now, mode) -> list[Decision]:
    found = []
    escalation = [
        item
        for item in observations
        if _eligible(item, subject)
        and item.permission_tier in CONTAINMENT_SIGNAL_TIERS
        and item.action_class in {"role.permission_escalation", "member.privileged_role_grant"}
    ]
    destructive = [
        item
        for item in observations
        if _eligible(item, subject) and item.action_class in DESTRUCTIVE_CLASSES
    ]
    window = int(policies["sequence.self_escalation"]["window_s"])
    for grant in escalation:
        follow = [item for item in destructive if grant.at <= item.at <= grant.at + timedelta(seconds=window)]
        if follow:
            found.append(
                _finish(
                    rule_id="sequence.self_escalation",
                    explanation="The actor gained a containment-signal permission and then took a destructive action.",
                    matched=[grant, *follow[:1]],
                    severity="H",
                    eligible_flag=True,
                    mode=mode,
                    subject=subject,
                    trust_snapshot=trust_snapshot,
                    late_present=any(item.late for item in observations),
                )
            )
            break
    impair = [item for item in observations if item.action_class == "cls.impairment" and _eligible(item, subject)]
    impair_policy = _policy_active(policies, "sequence.cls_impairment")
    impair_window = int(impair_policy["window_s"]) if impair_policy else 0
    for item in impair:
        follow = [hit for hit in destructive if item.at <= hit.at <= item.at + timedelta(seconds=impair_window)]
        if follow and impair_policy:
            found.append(
                _finish(
                    rule_id="sequence.cls_impairment",
                    explanation="CLS was impaired and the same actor then took a destructive action.",
                    matched=[item, *follow[:1]],
                    severity="C",
                    eligible_flag=True,
                    mode=mode,
                    subject=subject,
                    trust_snapshot=trust_snapshot,
                    late_present=any(obs.late for obs in observations),
                )
            )
            break
    return found


def _bot_rules(subject, observations, trust_snapshot, mode) -> list[Decision]:
    adds = [item for item in observations if item.action_class == "bot.add" and item.target_id == subject.user_id]
    decisions = []
    if adds and not trust_snapshot.trusted:
        severity = "C" if any(item.permission_tier == "CRITICAL_CONTROL" for item in adds) else "M"
        if any(item.permission_tier == "DESTRUCTIVE" for item in adds):
            severity = "H" if severity != "C" else severity
        decisions.append(
            Decision(
                rule_id="bot.add",
                explanation="An untrusted bot was added. Record and alert only; the inviter is not punished.",
                matched_observation_ids=[item.id for item in adds],
                severity=severity,
                containment_eligible=False,
                effective_mode=mode,
                would_contain=False,
                late_excluded=False,
                replayable=False,
            )
        )
    changes = [item for item in observations if item.action_class == "bot.privilege_change" and not item.late]
    if changes:
        severity = "C" if any(item.permission_tier == "CRITICAL_CONTROL" for item in changes) else "H"
        decisions.append(
            Decision(
                rule_id="bot.privilege_change",
                explanation="A bot gained tiered permissions. Record and alert only.",
                matched_observation_ids=[item.id for item in changes[:1]],
                severity=severity,
                containment_eligible=False,
                effective_mode=mode,
                would_contain=False,
                late_excluded=False,
                replayable=False,
            )
        )
    return decisions


def executable_decisions(decisions: list[Decision]) -> list[Decision]:
    """OBSERVE would_contain rows are never executable, including after a later ENFORCE switch."""
    return [
        item
        for item in decisions
        if item.replayable and item.effective_mode == SecurityMode.ENFORCE.value and not item.would_contain
    ]
