"""Join roles and automation rules. Legacy Autorole2 stays unloaded."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands

from cls_platform.logging.store import record_event
from cls_platform.role_automation.logic import allow_fire, conditions_match, should_assign_now
from cls_platform.role_automation.store import get_join, get_rule, migrate_legacy, rules_for
from cls_platform.role_menus.logic import role_block
from cls_platform.services.scheduler import enqueue_job

log = logging.getLogger("cls.role_automation")


class RoleAutomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.caused: dict[tuple[int, int, int, str], tuple[list[str], float]] = {}

    async def cog_load(self):
        from cls_platform.services.scheduler import register_job_handler

        register_job_handler("role_automation", self.handle_job)
        path = Path("db/autorole.db")
        if path.exists():
            try:
                count = await migrate_legacy(str(path))
                if count:
                    log.info("migrated %s join-role configs", count)
            except Exception:
                log.debug("join-role migration skipped", exc_info=True)

    async def _log(self, guild_id: int, event_type: str, member_id: int | None, summary: str):
        try:
            await record_event(
                guild_id=guild_id,
                category="bot_actions",
                event_type=event_type,
                actor_id=member_id,
                actor_confidence="certain" if member_id else "unknown",
                metadata={"summary": summary},
            )
        except Exception:
            log.debug("role automation log skipped", exc_info=True)

    def _block(self, guild, role_id: int) -> str | None:
        role = guild.get_role(int(role_id)) if guild else None
        me = guild.me if guild else None
        return role_block(
            exists=role is not None,
            managed=bool(getattr(role, "managed", False)),
            bot_can_manage=bool(me and me.guild_permissions.manage_roles),
            below_bot=bool(role and me and me.top_role and (role.position < me.top_role.position or (role.position == me.top_role.position and role.id < me.top_role.id))),
        )

    def _snapshot(self, member: discord.Member) -> dict:
        created = member.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = int((datetime.now(timezone.utc) - created).total_seconds())
        return {"is_bot": member.bot, "role_ids": {role.id for role in member.roles}, "account_age_seconds": max(0, age), "pending": bool(getattr(member, "pending", False))}

    def _parent(self, guild_id: int, member_id: int, role_id: int | None, action: str) -> list[str]:
        if role_id is None:
            return []
        row = self.caused.get((int(guild_id), int(member_id), int(role_id), action))
        if row is None or time.monotonic() - row[1] > 8:
            return []
        return list(row[0])

    def _note(self, guild_id: int, member_id: int, role_id: int, action: str, chain: list[str]) -> None:
        self.caused[(int(guild_id), int(member_id), int(role_id), action)] = (list(chain), time.monotonic())

    async def handle_job(self, job) -> None:
        payload = job.payload or {}
        guild = self.bot.get_guild(int(payload.get("guild_id") or 0))
        if guild is None:
            return
        try:
            member = guild.get_member(int(payload.get("member_id") or 0)) or await guild.fetch_member(int(payload["member_id"]))
        except discord.NotFound:
            return
        if payload.get("kind") == "join":
            await self.apply_join(member, force=True)
            return
        try:
            rule = await get_rule(guild.id, payload["rule_id"])
        except Exception:
            return
        if not rule["enabled"]:
            return
        await self.execute(member, rule, list(payload.get("chain") or []))

    async def apply_join(self, member: discord.Member, *, force: bool = False) -> None:
        config = await get_join(member.guild.id)
        pending = bool(getattr(member, "pending", False))
        if not force and not should_assign_now(pending=pending, screening=config["screening"]):
            return
        role_ids = config["bot_role_ids"] if member.bot else config["member_role_ids"]
        if not role_ids:
            return
        if not force and config["delay_seconds"]:
            await enqueue_job(
                "role_automation",
                datetime.now(timezone.utc) + timedelta(seconds=int(config["delay_seconds"])),
                {"kind": "join", "guild_id": member.guild.id, "member_id": member.id, "chain": []},
                dedupe_key=f"role-join:{member.guild.id}:{member.id}",
            )
            return
        await self._mutate(member, "add", [int(role_id) for role_id in role_ids], "Join roles", [])

    async def execute(self, member: discord.Member, rule: dict, parent: list[str] | None = None) -> None:
        chain = list(parent or [])
        reason = allow_fire(chain, rule["id"])
        if reason:
            await self._log(member.guild.id, "role_automation_stopped", member.id, f"{rule['name']}: {reason}")
            return
        snap = self._snapshot(member)
        if not conditions_match(is_bot=snap["is_bot"], role_ids=snap["role_ids"], account_age_seconds=snap["account_age_seconds"], conditions=rule["conditions"]):
            return
        chain.append(rule["id"])
        await self._mutate(member, rule["action"], [int(rule["action_role_id"])], rule["name"], chain)

    async def dispatch(self, member: discord.Member, trigger: str, role_id: int | None) -> None:
        rules = await rules_for(member.guild.id, trigger, role_id)
        snap = self._snapshot(member)
        action = "add" if trigger == "role_add" else "remove" if trigger == "role_remove" else ""
        parent = self._parent(member.guild.id, member.id, role_id, action)
        for rule in rules:
            if not conditions_match(is_bot=snap["is_bot"], role_ids=snap["role_ids"], account_age_seconds=snap["account_age_seconds"], conditions=rule["conditions"]):
                continue
            reason = allow_fire(parent, rule["id"])
            if reason:
                await self._log(member.guild.id, "role_automation_stopped", member.id, f"{rule['name']}: {reason}")
                continue
            if rule["delay_seconds"]:
                await enqueue_job(
                    "role_automation",
                    datetime.now(timezone.utc) + timedelta(seconds=int(rule["delay_seconds"])),
                    {"kind": "rule", "guild_id": member.guild.id, "member_id": member.id, "rule_id": rule["id"], "chain": parent},
                    dedupe_key=f"role-rule:{rule['id']}:{member.id}",
                )
                continue
            await self.execute(member, rule, parent)

    async def _mutate(self, member: discord.Member, action: str, role_ids: list[int], name: str, chain: list[str]) -> None:
        roles = []
        for role_id in role_ids:
            block = self._block(member.guild, role_id)
            if block:
                await self._log(member.guild.id, "role_automation_failed", member.id, f"{name}: {block}")
                continue
            role = member.guild.get_role(role_id)
            if role is not None:
                roles.append(role)
        if not roles:
            return
        for role in roles:
            self._note(member.guild.id, member.id, role.id, action, chain)
        try:
            if action == "add":
                await member.add_roles(*roles, reason=f"CLS role automation: {name}")
                verb = "Added"
            else:
                await member.remove_roles(*roles, reason=f"CLS role automation: {name}")
                verb = "Removed"
        except discord.Forbidden:
            await self._log(member.guild.id, "role_automation_failed", member.id, f"{name}: CLS cannot change that member's roles.")
            return
        summary = f"Role automation applied. Rule: {name}. Member: {member.display_name}. Action: {verb} {', '.join('@' + role.name for role in roles)}"
        await self._log(member.guild.id, "role_automation_applied", member.id, summary)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.apply_join(member)
        await self.dispatch(member, "join", None)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if getattr(before, "pending", False) and not getattr(after, "pending", False):
            await self.apply_join(after)
            await self.dispatch(after, "screening", None)
        added = {role.id for role in after.roles} - {role.id for role in before.roles}
        removed = {role.id for role in before.roles} - {role.id for role in after.roles}
        for role_id in added:
            await self.dispatch(after, "role_add", role_id)
        for role_id in removed:
            await self.dispatch(after, "role_remove", role_id)


async def setup(bot):
    await bot.add_cog(RoleAutomation(bot))
