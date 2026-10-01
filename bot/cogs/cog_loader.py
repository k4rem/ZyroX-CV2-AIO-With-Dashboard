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
        CogSpec("cogs.commands.music", "Music", O),
        CogSpec("cogs.commands.automod", "Automod", O),
        CogSpec("cogs.commands.welcome", "Welcomer", R),
        CogSpec("cogs.commands.fun", "Fun", O),
        CogSpec("cogs.commands.tracking", "Tracking", O),
        CogSpec("cogs.commands.Games", "Games", O),
        CogSpec("cogs.commands.extra", "Extra", O),
        CogSpec("cogs.commands.voice", "Voice", O),
        CogSpec("cogs.commands.owner", "Owner", O),
        CogSpec("cogs.commands.customrole", "Customrole", O),
        CogSpec("cogs.commands.afk", "afk", O),
        CogSpec("cogs.commands.Embed", "Embed", O),
        CogSpec("cogs.commands.Media", "Media", O),
        CogSpec("cogs.commands.ignore", "Ignore", O),
        CogSpec("cogs.commands.Invc", "Invcrole", O),
        CogSpec("cogs.commands.giveaway", "Giveaway", O),
        CogSpec("cogs.commands.steal", "Steal", O),
        CogSpec("cogs.commands.booster", "Booster", O),
        CogSpec("cogs.commands.timer", "Timer", O),
        CogSpec("cogs.commands.blacklist", "Blacklist", O),
        CogSpec("cogs.commands.block", "Block", O),
        CogSpec("cogs.commands.nightmode", "Nightmode", O),
        CogSpec("cogs.commands.owner", "Badges", O),
        CogSpec("cogs.commands.antinuke", "Antinuke", R),
        CogSpec("cogs.commands.anti_wl", "Whitelist", O),
        CogSpec("cogs.commands.anti_unwl", "Unwhitelist", O),
        CogSpec("cogs.commands.extraown", "Extraowner", O),
        CogSpec("cogs.commands.slots", "Slots", O),
        CogSpec("cogs.commands.blackjack", "Blackjack", O),
        CogSpec("cogs.commands.stats", "Stats", O),
        CogSpec("cogs.commands.emergency", "Emergency", O),
        CogSpec("cogs.commands.status", "Status", O),
        CogSpec("cogs.commands.np", "NoPrefix", O),
        CogSpec("cogs.commands.filters", "FilterCog", O),
        CogSpec("cogs.commands.owner2", "Global", O),
        CogSpec("cogs.commands.ticket", "TicketCog", R),
        CogSpec("cogs.commands.logging", "Logging", R),
        CogSpec("cogs.commands.qr", "QR", O),
        CogSpec("cogs.commands.vanityroles", "VanityRoles", O),
        CogSpec("cogs.commands.reactionroles", "ReactionRoles", O),
        CogSpec("cogs.commands.messages", "Messages", O),
        CogSpec("cogs.commands.translate", "TranslateCog", O),
        CogSpec("cogs.commands.fastgreet", "FastGreet", O),
        CogSpec("cogs.commands.jail", "Jail", O),
        CogSpec("cogs.commands.j2c", "JoinToCreate", R),
        CogSpec("cogs.commands.ai", "AI", O),
        CogSpec("cogs.commands.dms", "StaffDMCog", O),
        CogSpec("cogs.commands.leveling", "Leveling", O),
        CogSpec("cogs.commands.stickymessage", "StickyMessage", O),
        CogSpec("cogs.commands.verification", "Verification", O),
        CogSpec("cogs.commands.minecraft", "Minecraft", O),
        CogSpec("cogs.commands.encryption", "encryption", O),
        CogSpec("cogs.commands.calc", "calculator", O),
        CogSpec("cogs.commands.joindm", "joindm", O),
        CogSpec("cogs.commands.Birthday", "Birthdays", O),
        CogSpec("cogs.commands.nitro", "Nitro", O),
        CogSpec("cogs.commands.image", "ImageCommands", O),
        CogSpec("cogs.commands.youtube", "Youtube", O),
        CogSpec("cogs.zyrox.antinuke", "_antinuke", O),
        CogSpec("cogs.zyrox.extra", "_extra", O),
        CogSpec("cogs.zyrox.general", "_general", O),
        CogSpec("cogs.zyrox.automod", "_automod", O),
        CogSpec("cogs.zyrox.moderation", "_moderation", O),
        CogSpec("cogs.zyrox.music", "_music", O),
        CogSpec("cogs.zyrox.fun", "_fun", O),
        CogSpec("cogs.zyrox.games", "_games", O),
        CogSpec("cogs.zyrox.ignore", "_ignore", O),
        CogSpec("cogs.zyrox.server", "_server", O),
        CogSpec("cogs.zyrox.voice", "_voice", O),
        CogSpec("cogs.zyrox.welcome", "_welcome", O),
        CogSpec("cogs.zyrox.giveaway", "_giveaway", O),
        CogSpec("cogs.zyrox.ticket", "_ticket", O),
        CogSpec("cogs.zyrox.logging", "_logging", O),
        CogSpec("cogs.zyrox.vanity", "_vanity", O),
        CogSpec("cogs.zyrox.inviteTracker", "inviteTracker", O),
        CogSpec("cogs.commands.counting", "Counting", O),
        CogSpec("cogs.zyrox.counting", "_Counting", O),
        CogSpec("cogs.zyrox.j2c", "_J2C", O),
        CogSpec("cogs.zyrox.ai", "_ai", O),
        CogSpec("cogs.zyrox.booster", "__boost", O),
        CogSpec("cogs.zyrox.leveling", "_leveling", O),
        CogSpec("cogs.zyrox.sticky", "_sticky", O),
        CogSpec("cogs.zyrox.verify", "_verify", O),
        CogSpec("cogs.zyrox.encryption", "_encrypt", O),
        CogSpec("cogs.zyrox.mc", "_mc", O),
        CogSpec("cogs.zyrox.joindm", "_joindm", O),
        CogSpec("cogs.zyrox.birth", "_birth", O),
        CogSpec("cogs.events.on_guild", "Guild", O),
        CogSpec("cogs.events.Errors", "Errors", O),
        CogSpec("cogs.events.autorole", "Autorole2", O),
        CogSpec("cogs.events.auto", "Autorole", O),
        CogSpec("cogs.events.greet2", "greet", O),
        CogSpec("cogs.commands.autoresponder", "AutoResponder", O),
        CogSpec("cogs.events.mention", "Mention", O),
        CogSpec("cogs.commands.autorole", "AutoRole", O),
        CogSpec("cogs.events.react", "React", O),
        CogSpec("cogs.commands.autoreact", "AutoReaction", O),
        CogSpec("cogs.events.autoreact", "AutoReactListener", O),
        CogSpec("cogs.commands.notify", "NotifCommands", O),
        CogSpec("cogs.events.stickymessage", "StickyMessageListener", O),
        CogSpec("cogs.events.ai", "AIResponses", O),
        CogSpec("cogs.antinuke.anti_member_update", "AntiMemberUpdate", O),
        CogSpec("cogs.antinuke.antiban", "AntiBan", O),
        CogSpec("cogs.antinuke.antibotadd", "AntiBotAdd", O),
        CogSpec("cogs.antinuke.antichcr", "AntiChannelCreate", O),
        CogSpec("cogs.antinuke.antichdl", "AntiChannelDelete", O),
        CogSpec("cogs.antinuke.antichup", "AntiChannelUpdate", O),
        CogSpec("cogs.antinuke.antieveryone", "AntiEveryone", O),
        CogSpec("cogs.antinuke.antiguild", "AntiGuildUpdate", O),
        CogSpec("cogs.antinuke.antiIntegration", "AntiIntegration", O),
        CogSpec("cogs.antinuke.antikick", "AntiKick", O),
        CogSpec("cogs.antinuke.antiprune", "AntiPrune", O),
        CogSpec("cogs.antinuke.antirlcr", "AntiRoleCreate", O),
        CogSpec("cogs.antinuke.antirldl", "AntiRoleDelete", O),
        CogSpec("cogs.antinuke.antirlup", "AntiRoleUpdate", O),
        CogSpec("cogs.antinuke.antiwebhook", "AntiWebhookUpdate", O),
        CogSpec("cogs.antinuke.antiwebhookcr", "AntiWebhookCreate", O),
        CogSpec("cogs.antinuke.antiwebhookdl", "AntiWebhookDelete", O),
        # V2 observation only. Legacy antinuke stays loaded until step 2A.5.
        CogSpec("cogs.security.protection", "SecurityProtection", O),
        CogSpec("cogs.automod.antispam", "AntiSpam", O),
        CogSpec("cogs.automod.anticaps", "AntiCaps", O),
        CogSpec("cogs.automod.anti_invites", "AntiInvite", O),
        CogSpec("cogs.automod.antilink", "AntiLink", O),
        CogSpec("cogs.automod.anti_mass_mention", "AntiMassMention", O),
        CogSpec("cogs.automod.anti_emoji_spam", "AntiEmojiSpam", O),
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
