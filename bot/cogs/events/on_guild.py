# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 CodeX Devs — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.gg/codexdev                      ║
# ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
# ║   github   ──  https://github.com/RayExo                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging

from discord.ext import commands

logger = logging.getLogger("cls.guild_allowlist")


class Guild(commands.Cog):
    """Leaves a guild that is not on ALLOWED_GUILD_IDS as soon as it is joined."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        from cls_platform.config import OPS_GUILD_ID
        from cls_platform.security.allowlist_sweep import allowlist_config_status
        from utils.guild_allowlist import ALLOWLIST_ENFORCED, is_guild_allowed

        status = allowlist_config_status()
        if status != "ok":
            logger.error(
                "Guild allowlist config is %s. Refusing to leave guild %s on join.",
                status,
                getattr(guild, "id", None),
            )
            return
        if not ALLOWLIST_ENFORCED:
            return
        guild_id = int(guild.id)
        if is_guild_allowed(guild_id):
            return
        if OPS_GUILD_ID is not None and guild_id == int(OPS_GUILD_ID):
            logger.info("Kept Ops guild %s on join.", guild_id)
            return
        name = getattr(guild, "name", "")
        reason = "not on ALLOWED_GUILD_IDS"
        try:
            await guild.leave()
        except Exception:
            logger.exception(
                "Could not leave non-allowlisted guild %s (%s): %s",
                guild_id,
                name,
                reason,
            )
            print(f"[guild allowlist] Failed to leave non-allowlisted guild {guild_id} ({name}): {reason}.")
            return
        logger.warning("Left non-allowlisted guild %s (%s): %s", guild_id, name, reason)
        print(f"[guild allowlist] Left non-allowlisted guild {guild_id} ({name}): {reason}.")
