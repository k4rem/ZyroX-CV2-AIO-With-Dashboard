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

import discord
from utils.emoji import BLOBPART
from discord.ext import commands
import json
from utils.cv2 import CV2

class joindm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.joindm_messages = {}
        self.load_joindm_messages()

    def load_joindm_messages(self):
        # Load the join DM messages from file
        try:
            with open('jsondb/joindm_messages.json', 'r') as f:
                self.joindm_messages = json.load(f)
        except FileNotFoundError:
            self.joindm_messages = {}

    def save_joindm_messages(self):
        # Save the join DM messages to file
        with open('jsondb/joindm_messages.json', 'w') as f:
            json.dump(self.joindm_messages, f)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def joindm(self, ctx):
        # Display the current join DM message
        from cls_platform.welcome.store import read_dm

        record = read_dm(ctx.guild.id)
        if record["enabled"]:
            text = record["payload"].get("content") or "Embed message"
            await ctx.send(view=CV2("✅ Join DM Status", f"The current join DM message is:\n`{text}`"))
        else:
            await ctx.send(view=CV2("❌ Error", "No custom join DM message has been set for this server."))

    @joindm.command()
    @commands.has_permissions(administrator=True)
    async def message(self, ctx, *, message=None):
        # Set the custom join DM message
        if message is None:
            await ctx.send(view=CV2("❌ Error", "Please provide a custom join DM message."))
        else:
            from cls_platform.welcome.store import EMPTY_PAYLOAD, write_dm

            payload = {**EMPTY_PAYLOAD, "content": message, "embeds": []}
            write_dm(ctx.guild.id, enabled=True, payload=payload)
            await ctx.send(view=CV2("✅ Success", "Custom join DM message set successfully."))

    @joindm.command()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx):
        # Enable the join DM module
        from cls_platform.welcome.store import read_dm, write_dm

        record = read_dm(ctx.guild.id)
        write_dm(ctx.guild.id, enabled=True, payload=record["payload"])
        await ctx.send(view=CV2("✅ Success", "Join DM module enabled. Custom DM will be sent to new members."))

    @joindm.command()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        # Disable the join DM module
        from cls_platform.welcome.store import read_dm, write_dm

        record = read_dm(ctx.guild.id)
        write_dm(ctx.guild.id, enabled=False, payload=record["payload"])
        await ctx.send(view=CV2("✅ Success", "Join DM module disabled. Custom DM will not be sent to new members."))

    @joindm.command()
    async def test(self, ctx):
        # Send a test join DM to the author of the command
        from cls_platform.welcome.runtime import send_rendered
        from cls_platform.welcome.store import WELCOME_VARIABLES, member_values, read_dm

        record = read_dm(ctx.guild.id)
        if record["enabled"]:
            await ctx.send(view=CV2("✅ Test Sent", "Test Join DM Sent To Your Dm"))
            await ctx.message.add_reaction(BLOBPART)
            await send_rendered(ctx.author, ctx.guild.id, record["payload"], member_values(ctx.author, ctx.guild), WELCOME_VARIABLES)
        else:
            await ctx.send(view=CV2("❌ Error", "No custom join DM message has been set for this server."))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Channel welcome sends the DM as well. This listener covers restarts
        # where only this cog is loaded, and skips work when greet already ran.
        if self.bot.get_cog("greet") is not None:
            return
        from cls_platform.welcome.runtime import send_direct_welcome

        try:
            await send_direct_welcome(member)
        except Exception:
            return

async def setup(bot):
    await bot.add_cog(joindm(bot))
