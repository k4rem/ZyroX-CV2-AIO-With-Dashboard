"""Lazy per-module cog loading (Phase 0 module health isolation)."""

from __future__ import annotations

import importlib
from typing import NamedTuple

from utils.module_health import ModuleHealth, add_cog_safe


class CogSpec(NamedTuple):
    module: str
    class_name: str
    required: bool = False
    skip: bool = False
    skip_reason: str = ""


def _import_cog_class(module_path: str, class_name: str):
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


async def _load_one(bot, health: ModuleHealth, spec: CogSpec) -> None:
    label = spec.class_name
    if spec.skip:
        health.record_skipped(label, spec.skip_reason or "disabled")
        return
    try:
        cog_cls = _import_cog_class(spec.module, spec.class_name)
    except Exception as exc:
        health.record_fail(label, spec.required, exc)
        return
    await add_cog_safe(
        bot,
        cog_cls,
        health,
        required=spec.required,
    )


def _cog_specs() -> list[CogSpec]:
    """Load order preserved from legacy setup(); imports happen lazily per entry."""
    O = False
    R = True
    specs: list[CogSpec] = [
        CogSpec("cogs.commands.help", "Help", O),
        CogSpec("cogs.commands.general", "General", O),
        CogSpec("cogs.commands.music", "Music", O, skip=True, skip_reason="Out of scope. Music is not part of CLS OS."),
        CogSpec("cogs.automod_v2", "AutomodV2", O),
        CogSpec("cogs.commands.automod", "Automod", O),
        CogSpec("cogs.commands.welcome", "Welcomer", R),
        CogSpec("cogs.commands.fun", "Fun", O, skip=True, skip_reason="Out of scope. Novelty commands are not part of CLS OS."),
        CogSpec(
            "cogs.commands.tracking",
            "Tracking",
            False,
            skip=True,
            skip_reason="Retired. Invites V2 records joins, leaves, and the log channel.",
        ),
        CogSpec("cogs.commands.Games", "Games", O, skip=True, skip_reason="Out of scope. Games are not part of CLS OS."),
        CogSpec("cogs.commands.extra", "Extra", O),
        CogSpec("cogs.commands.voice", "Voice", O),
        CogSpec("cogs.commands.owner", "Owner", O),
        CogSpec("cogs.commands.customrole", "Customrole", O),
        CogSpec("cogs.commands.afk", "afk", O),
        CogSpec("cogs.commands.Embed", "Embed", O),
        CogSpec("cogs.commands.Media", "Media", O),
        CogSpec("cogs.commands.ignore", "Ignore", O),
        CogSpec("cogs.commands.Invc", "Invcrole", O),
        CogSpec(
            "cogs.commands.giveaway",
            "Giveaway",
            False,
            skip=True,
            skip_reason="Retired. Giveaways V2 publishes and closes giveaways.",
        ),
        CogSpec("cogs.commands.steal", "Steal", O),
        CogSpec("cogs.commands.booster", "Booster", O),
        CogSpec("cogs.commands.timer", "Timer", O),
        CogSpec("cogs.commands.blacklist", "Blacklist", O),
        CogSpec("cogs.commands.block", "Block", O),
        CogSpec("cogs.commands.nightmode", "Nightmode", O),
        CogSpec("cogs.commands.owner", "Badges", O),
        # Legacy antinuke configuration commands retired in 2A.5. Trust is Dashboard-only.
        CogSpec("cogs.commands.slots", "Slots", O, skip=True, skip_reason="Out of scope. Games are not part of CLS OS."),
        CogSpec("cogs.commands.blackjack", "Blackjack", O, skip=True, skip_reason="Out of scope. Games are not part of CLS OS."),
        CogSpec("cogs.commands.stats", "Stats", O),
        CogSpec("cogs.commands.emergency", "Emergency", O),
        CogSpec("cogs.commands.status", "Status", O),
        CogSpec("cogs.commands.np", "NoPrefix", O),
        CogSpec("cogs.commands.filters", "FilterCog", O, skip=True, skip_reason="Out of scope. Voice filters depend on music."),
        CogSpec("cogs.commands.owner2", "Global", O),
        CogSpec(
            "cogs.commands.ticket",
            "TicketCog",
            False,
            skip=True,
            skip_reason="Retired. Tickets V2 is the operational ticket system.",
        ),
        CogSpec(
            "cogs.commands.logging",
            "Logging",
            False,
            skip=True,
            skip_reason="Retired. Logging V2 is the only logging pipeline.",
        ),
        CogSpec("cogs.commands.qr", "QR", O),
        CogSpec("cogs.commands.vanityroles", "VanityRoles", O),
        CogSpec(
            "cogs.commands.reactionroles",
            "ReactionRoles",
            False,
            skip=True,
            skip_reason="Retired. Role menus are the reaction, button, and select role system.",
        ),
        CogSpec("cogs.commands.messages", "Messages", O),
        CogSpec("cogs.commands.translate", "TranslateCog", O, skip=True, skip_reason="Out of scope. Translation is not part of CLS OS."),
        CogSpec("cogs.commands.fastgreet", "FastGreet", O, skip=True, skip_reason="Retired. Welcome V2 is the only join welcome."),
        CogSpec("cogs.commands.jail", "Jail", O),
        CogSpec("cogs.commands.j2c", "JoinToCreate", R),
        CogSpec("cogs.commands.ai", "AI", O, skip=True, skip_reason="Out of scope. AI chat toys are not part of CLS OS."),
        CogSpec("cogs.commands.dms", "StaffDMCog", O),
        CogSpec("cogs.commands.leveling", "Leveling", O),
        CogSpec("cogs.commands.stickymessage", "StickyMessage", O),
        CogSpec("cogs.commands.verification", "Verification", O),
        CogSpec("cogs.commands.minecraft", "Minecraft", O, skip=True, skip_reason="Out of scope. Minecraft lookups are not part of CLS OS."),
        CogSpec("cogs.commands.encryption", "encryption", O),
        CogSpec("cogs.commands.calc", "calculator", O),
        CogSpec("cogs.commands.joindm", "joindm", O),
        CogSpec("cogs.commands.Birthday", "Birthdays", O),
        CogSpec("cogs.commands.nitro", "Nitro", O, skip=True, skip_reason="Out of scope. Fake nitro is not part of CLS OS."),
        CogSpec("cogs.commands.image", "ImageCommands", O, skip=True, skip_reason="Out of scope. Image toys are not part of CLS OS."),
        CogSpec("cogs.commands.youtube", "Youtube", O, skip=True, skip_reason="Out of scope. Lookup toys are not part of CLS OS."),
        # Legacy help cog for antinuke commands retired in 2A.5.
        CogSpec("cogs.zyrox.extra", "_extra", O),
        CogSpec("cogs.zyrox.general", "_general", O),
        CogSpec("cogs.zyrox.automod", "_automod", O),
        CogSpec("cogs.zyrox.moderation", "_moderation", O),
        CogSpec("cogs.zyrox.music", "_music", O, skip=True, skip_reason="Out of scope. Music is not part of CLS OS."),
        CogSpec("cogs.zyrox.fun", "_fun", O, skip=True, skip_reason="Out of scope. Toy commands are not part of CLS OS."),
        CogSpec("cogs.zyrox.games", "_games", O, skip=True, skip_reason="Out of scope. Games are not part of CLS OS."),
        CogSpec("cogs.zyrox.ignore", "_ignore", O),
        CogSpec("cogs.zyrox.server", "_server", O),
        CogSpec("cogs.zyrox.voice", "_voice", O),
        CogSpec("cogs.zyrox.welcome", "_welcome", O),
        CogSpec(
            "cogs.zyrox.giveaway",
            "_giveaway",
            False,
            skip=True,
            skip_reason="Retired. Giveaways V2 publishes and closes giveaways.",
        ),
        CogSpec("cogs.zyrox.ticket", "_ticket", O),
        CogSpec("cogs.zyrox.logging", "_logging", O),
        CogSpec("cogs.zyrox.vanity", "_vanity", O),
        CogSpec("cogs.zyrox.inviteTracker", "inviteTracker", O),
        CogSpec("cogs.commands.counting", "Counting", O),
        CogSpec("cogs.zyrox.counting", "_Counting", O),
        CogSpec("cogs.zyrox.j2c", "_J2C", O),
        CogSpec("cogs.zyrox.ai", "_ai", O, skip=True, skip_reason="Out of scope. AI chat toys are not part of CLS OS."),
        CogSpec("cogs.zyrox.booster", "__boost", O),
        CogSpec("cogs.zyrox.leveling", "_leveling", O),
        CogSpec("cogs.zyrox.sticky", "_sticky", O),
        CogSpec("cogs.zyrox.verify", "_verify", O),
        CogSpec("cogs.zyrox.encryption", "_encrypt", O),
        CogSpec("cogs.zyrox.mc", "_mc", O, skip=True, skip_reason="Out of scope. Minecraft lookups are not part of CLS OS."),
        CogSpec("cogs.zyrox.joindm", "_joindm", O),
        CogSpec("cogs.zyrox.birth", "_birth", O),
        CogSpec("cogs.events.on_guild", "Guild", O),
        CogSpec("cogs.events.Errors", "Errors", O),
        CogSpec(
            "cogs.events.autorole",
            "Autorole2",
            False,
            skip=True,
            skip_reason="Retired. Role automation assigns join roles.",
        ),
        CogSpec("cogs.events.auto", "Autorole", O),
        CogSpec("cogs.events.greet2", "greet", O),
        CogSpec("cogs.commands.autoresponder", "AutoResponder", O),
        CogSpec("cogs.events.mention", "Mention", O),
        CogSpec("cogs.commands.autorole", "AutoRole", O),
        CogSpec("cogs.events.react", "React", O),
        CogSpec(
            "cogs.commands.autoreact",
            "AutoReaction",
            False,
            skip=True,
            skip_reason="Retired. Auto react rules apply reactions.",
        ),
        CogSpec(
            "cogs.events.autoreact",
            "AutoReactListener",
            False,
            skip=True,
            skip_reason="Retired. Auto react rules apply reactions.",
        ),
        CogSpec("cogs.autoreact_v2", "AutoReactV2", O),
        CogSpec("cogs.commands.notify", "NotifCommands", O),
        CogSpec("cogs.events.stickymessage", "StickyMessageListener", O),
        CogSpec("cogs.events.ai", "AIResponses", O, skip=True, skip_reason="Out of scope. AI chat toys are not part of CLS OS."),
        # The 17 legacy antinuke listeners are unloaded. SecurityProtection is the runtime.
        CogSpec("cogs.security.protection", "SecurityProtection", O),
        CogSpec("cogs.security.center_runtime", "SecurityCenterRuntime", O),
        CogSpec("cogs.verification_v2", "VerificationV2", O),
        CogSpec("cogs.tickets_v2", "TicketsV2", O),
        CogSpec("cogs.role_menus", "RoleMenus", O),
        CogSpec("cogs.role_automation", "RoleAutomation", O),
        CogSpec("cogs.logging_v2", "LoggingV2", R),
        CogSpec("cogs.growth_v2", "GrowthV2", O),
        CogSpec("cogs.automod.antispam", "AntiSpam", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.automod.anticaps", "AntiCaps", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.automod.anti_invites", "AntiInvite", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.automod.antilink", "AntiLink", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.automod.anti_mass_mention", "AntiMassMention", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.automod.anti_emoji_spam", "AntiEmojiSpam", O, skip=True, skip_reason="Retired. Automod V2 is the only enforcement pipeline."),
        CogSpec("cogs.moderation.ban", "Ban", O),
        CogSpec("cogs.moderation.unban", "Unban", O),
        CogSpec("cogs.moderation.timeout", "Mute", O),
        CogSpec("cogs.moderation.unmute", "Unmute", O),
        CogSpec("cogs.moderation.lock", "Lock", O),
        CogSpec("cogs.moderation.unlock", "Unlock", O),
        CogSpec("cogs.moderation.hide", "Hide", O),
        CogSpec("cogs.moderation.unhide", "Unhide", O),
        CogSpec("cogs.moderation.kick", "Kick", O),
        CogSpec("cogs.moderation.warn", "Warn", O),
        CogSpec("cogs.moderation.role", "Role", O),
        CogSpec("cogs.moderation.message", "Message", O),
        CogSpec("cogs.moderation.moderation", "Moderation", R),
        CogSpec("cogs.moderation.topcheck", "TopCheck", O),
        CogSpec("cogs.moderation.snipe", "Snipe", O),
    ]
    return specs


async def load_all_cogs(bot) -> ModuleHealth:
    health = ModuleHealth()
    for spec in _cog_specs():
        await _load_one(bot, health, spec)
    return health
