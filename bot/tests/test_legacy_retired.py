"""Legacy antinuke runtime is unloaded and its API is retired."""

from fastapi import HTTPException
import pytest

from api.routes.guilds import get_guild_antinuke, patch_guild_antinuke
from cogs.cog_loader import _cog_specs


def test_legacy_listeners_are_unloaded_and_v2_listener_remains():
    modules = [spec.module for spec in _cog_specs()]
    legacy = [name for name in modules if name.startswith("cogs.antinuke.")]
    assert legacy == []
    assert "cogs.commands.antinuke" not in modules
    assert "cogs.commands.extraown" not in modules
    assert "cogs.security.protection" in modules


async def test_antinuke_routes_are_gone():
    with pytest.raises(HTTPException) as got:
        await get_guild_antinuke(1)
    assert got.value.status_code == 410
    with pytest.raises(HTTPException) as patched:
        await patch_guild_antinuke(1, None)
    assert patched.value.status_code == 410
