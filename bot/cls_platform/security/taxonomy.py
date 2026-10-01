"""Protected action taxonomy for Phase 2A.

Only ``required`` classes are active. Optional, later, and out-of-scope classes
stay classified and inactive.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionSpec:
    action_class: str
    severity: str
    phase_status: str  # required | optional | later | out_of_scope
    comparable_target: bool
    gateway_visible: bool
    discord_actions: tuple[str, ...]

    @property
    def active(self) -> bool:
        return self.phase_status == "required"


_SPECS: tuple[ActionSpec, ...] = (
    ActionSpec("channel.delete", "H", "required", True, True, ("channel_delete",)),
    ActionSpec("role.delete", "H", "required", True, True, ("role_delete",)),
    ActionSpec("member.ban", "H", "required", True, True, ("ban",)),
    ActionSpec("member.kick", "H", "required", True, False, ("kick",)),
    ActionSpec("member.prune", "C", "required", False, False, ("member_prune",)),
    ActionSpec(
        "role.permission_escalation",
        "H",
        "required",
        True,
        True,
        ("role_update", "role_create"),
    ),
    ActionSpec(
        "member.privileged_role_grant",
        "H",
        "required",
        True,
        True,
        ("member_role_update",),
    ),
    ActionSpec("bot.add", "M", "required", True, True, ("bot_add",)),
    ActionSpec(
        "bot.privilege_change",
        "H",
        "required",
        True,
        True,
        ("member_role_update", "role_update"),
    ),
    ActionSpec("webhook.create", "M", "required", True, False, ("webhook_create",)),
    ActionSpec("cls.impairment", "C", "required", True, True, ("member_role_update", "kick", "ban")),
    ActionSpec(
        "channel.overwrite_escalation",
        "H",
        "optional",
        True,
        False,
        ("overwrite_create", "overwrite_update"),
    ),
    ActionSpec("channel.create", "M", "optional", True, True, ("channel_create",)),
    ActionSpec("webhook.delete", "M", "optional", True, False, ("webhook_delete",)),
    ActionSpec("webhook.update", "M", "optional", True, False, ("webhook_update",)),
    ActionSpec("guild.update", "M", "optional", False, False, ("guild_update",)),
    ActionSpec("integration.create", "M", "optional", True, False, ("integration_create",)),
    ActionSpec("automod.rule_change", "L", "later", True, False, ("automod_rule_create",)),
    ActionSpec("member.unban", "L", "later", True, False, ("unban",)),
    ActionSpec("mention.spam", "L", "out_of_scope", False, False, ()),
    ActionSpec("message.delete", "L", "out_of_scope", False, False, ()),
    ActionSpec("voice.move", "L", "out_of_scope", False, False, ()),
)

ACTION_SPECS: dict[str, ActionSpec] = {spec.action_class: spec for spec in _SPECS}

_BY_DISCORD_ACTION: dict[str, tuple[str, ...]] = {}
for _spec in _SPECS:
    for _name in _spec.discord_actions:
        _BY_DISCORD_ACTION.setdefault(_name, tuple())
        if _spec.action_class not in _BY_DISCORD_ACTION[_name]:
            _BY_DISCORD_ACTION[_name] = _BY_DISCORD_ACTION[_name] + (_spec.action_class,)


def action_spec(action_class: str) -> ActionSpec:
    try:
        return ACTION_SPECS[action_class]
    except KeyError as exc:
        raise KeyError(f"Unknown action class {action_class}") from exc


def active_action_classes() -> tuple[str, ...]:
    return tuple(spec.action_class for spec in _SPECS if spec.active)


def classes_for_discord_action(discord_action: str) -> tuple[str, ...]:
    return tuple(
        name for name in _BY_DISCORD_ACTION.get(discord_action, ()) if ACTION_SPECS[name].active
    )
