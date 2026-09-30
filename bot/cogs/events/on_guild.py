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

from core import zyrox, Cog
from utils.guild_allowlist import ALLOWLIST_ENFORCED, is_guild_allowed

client = zyrox()


class Guild(Cog):
    def __init__(self, client: zyrox):
        self.client = client

    @Cog.listener()
    async def on_guild_join(self, guild):
        if not ALLOWLIST_ENFORCED:
            return
        if is_guild_allowed(guild.id):
            return
        try:
            await guild.leave()
        except Exception:
            pass
        print(
            f"[guild allowlist] Left non-allowlisted guild {guild.id} ({guild.name})."
        )


# client.add_cog(Guild(client))
