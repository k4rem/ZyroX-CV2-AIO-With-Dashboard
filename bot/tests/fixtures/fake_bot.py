"""Minimal bot double for FastAPI integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakeRole:
    id: int
    name: str = "role"
    position: int = 1


@dataclass
class FakeChannel:
    id: int
    name: str = "channel"


@dataclass
class FakeGuild:
    id: int
    name: str = "Test Guild"
    roles: list[FakeRole] = field(default_factory=list)
    channels: list[FakeChannel] = field(default_factory=list)
    member_count: int = 10
    owner_id: int = 1
    icon: object = None

    def get_role(self, role_id: int) -> Optional[FakeRole]:
        for r in self.roles:
            if r.id == role_id:
                return r
        return None

    def get_channel(self, channel_id: int) -> Optional[FakeChannel]:
        for c in self.channels:
            if c.id == channel_id:
                return c
        return None


class FakeBot:
    def __init__(self, guilds: list[FakeGuild]):
        self.guilds = guilds
        self.commands: list[object] = []
        self.cogs: dict[str, object] = {}
        self.user = type("U", (), {"id": 999, "name": "Bot"})()
        self.latency = 0.05

    def get_guild(self, guild_id: int) -> Optional[FakeGuild]:
        for g in self.guilds:
            if g.id == guild_id:
                return g
        return None
