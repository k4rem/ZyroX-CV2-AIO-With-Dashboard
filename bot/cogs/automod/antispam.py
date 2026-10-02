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
from discord.ext import commands
import aiosqlite
import asyncio

from cls_platform.automod_compat import enforce, rule_action

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_threshold = 5
        self.mute_duration = 12 * 60
        self.recent_messages = {}

    async def is_automod_enabled(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT enabled FROM automod WHERE guild_id = ?", (guild_id,))
            result = await cursor.fetchone()
            return result is not None and result[0] == 1

    async def is_anti_spam_enabled(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT punishment FROM automod_punishments WHERE guild_id = ? AND event = 'Anti spam'", (guild_id,))
            result = await cursor.fetchone()
            return result is not None
            

    async def get_ignored_channels(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT id FROM automod_ignored WHERE guild_id = ? AND type = 'channel'", (guild_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def get_ignored_roles(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT id FROM automod_ignored WHERE guild_id = ? AND type = 'role'", (guild_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def get_punishment(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT punishment FROM automod_punishments WHERE guild_id = ? AND event = 'Anti spam'", (guild_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def log_action(self, guild, user, channel, action, reason):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT log_channel FROM automod_logging WHERE guild_id = ?", (guild.id,))
            log_channel_id = await cursor.fetchone()

        if log_channel_id and log_channel_id[0]:
            log_channel = guild.get_channel(log_channel_id[0])
            if log_channel:
                embed = discord.Embed(title="Automod Log: Anti-Spam", color=0xFF0000)
                embed.add_field(name="User", value=user.mention, inline=False)
                embed.add_field(name="Action", value=action, inline=False)
                embed.add_field(name="Channel", value=channel.mention, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"User ID: {user.id}")
                avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
                embed.set_thumbnail(url=avatar_url)
                embed.timestamp=discord.utils.utcnow()
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        user = message.author
        channel = message.channel
        guild_id = guild.id

        action = await rule_action(guild_id, "anti_spam")
        if not await self.is_automod_enabled(guild_id) or not action:
            return

        if user == guild.owner or user == self.bot.user:
            return

        ignored_channels = await self.get_ignored_channels(guild_id)
        if channel.id in ignored_channels:
            return

        ignored_roles = await self.get_ignored_roles(guild_id)
        if any(role.id in ignored_roles for role in user.roles):
            return

        current_time = message.created_at.timestamp()
        key = (guild_id, user.id)
        user_messages = self.recent_messages.get(key, [])
        user_messages = [item for item in user_messages if current_time - item[0] < 10]
        user_messages.append((current_time, message))
        self.recent_messages[key] = user_messages

        if len(user_messages) > self.spam_threshold:
            burst = [item[1] for item in user_messages] if action == "delete" else []
            result = await enforce(
                self.bot,
                message,
                rule="anti_spam",
                action=action,
                reason="Spamming",
                messages=burst,
            )
            if result.get("ok"):
                self.recent_messages.pop(key, None)

    @commands.Cog.listener()
    async def on_rate_limit(self, message):
        await asyncio.sleep(10)

