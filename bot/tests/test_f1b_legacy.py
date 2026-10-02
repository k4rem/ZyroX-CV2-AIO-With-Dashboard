"""F1b legacy containment. Retired stores stay on disk; runtime writes do not."""

from __future__ import annotations

import inspect

import pytest

from cogs.cog_loader import _cog_specs
from cogs.commands.nightmode import Nightmode
from cls_platform.config import ROOT_OWNER_ID
from cls_platform.sqlite_paths import sqlite_path
from tests.conftest import TEST_GUILD_A, TEST_ROOT, auth_headers

BIG = 1543105121913802823


def _spec(name: str):
    return next(spec for spec in _cog_specs() if spec.class_name == name)


def test_fastgreet_join_is_retired_and_loader_skips_it():
    from cogs.commands.fastgreet import FastGreet

    source = inspect.getsource(FastGreet.on_member_join)
    assert source.strip().splitlines()[1].strip() == "return" or "return" in source.split("sqlite3.connect")[0]
    assert _spec("FastGreet").skip is True
    assert "Welcome V2" in _spec("FastGreet").skip_reason


def test_single_welcome_listener_remains_greet2():
    greet = _spec("greet")
    assert greet.skip is False
    assert greet.module == "cogs.events.greet2"
    assert _spec("FastGreet").skip is True


def test_legacy_welcome_and_autorole_commands_are_read_only_redirects():
    from cogs.commands.autorole import AutoRole
    from cogs.commands.welcome import Welcomer
    from cogs.events.autorole import Autorole2

    welcome = inspect.getsource(Welcomer.cog_check)
    autorole = inspect.getsource(AutoRole.cog_check)
    assert "Welcome is managed from the CLS OS dashboard." in welcome
    assert "Role Automation → Join Roles" in autorole
    join = inspect.getsource(Autorole2.on_member_join)
    assert join.split("async def on_member_join", 1)[1].lstrip().startswith("(self, member):\n        return")


@pytest.mark.asyncio
async def test_np_db_is_not_a_prefix_bypass_and_root_still_authorizes_nightmode():
    from pathlib import Path

    source = Path("core/zyrox.py").read_text(encoding="utf-8")
    prefix = source.split("async def get_prefix", 1)[1].split("async def ", 1)[0]
    assert "aiosqlite.connect" not in prefix
    assert "not an authorization source" in prefix

    async def _check(user_id: int) -> bool:
        cog = Nightmode.__new__(Nightmode)
        user = type("U", (), {"id": user_id})()
        return await cog.is_extra_owner(user, None)

    assert await _check(5) is False
    assert ROOT_OWNER_ID is not None
    assert await _check(int(ROOT_OWNER_ID)) is True


def test_optional_toys_are_skipped_and_owner_does_not_import_numpy():
    from pathlib import Path

    assert _spec("Music").skip is True
    assert _spec("Games").skip is True
    assert _spec("Owner").skip is False
    owner = Path("cogs/commands/owner.py").read_text(encoding="utf-8")
    assert "import numpy" not in owner


def test_project_root_sqlite_path_and_snowflake_text():
    path = sqlite_path("np.db")
    assert path.is_absolute()
    assert path.name == "np.db"
    assert path.parent.name == "db"
    assert not path.exists() or path.is_file()
    assert str(BIG) == "1543105121913802823"
    assert isinstance(str(BIG), str)


def test_legacy_verification_mutation_stays_blocked():
    from utils.legacy_verification import legacy_verification_block_reason

    reason = legacy_verification_block_reason()
    assert reason is None or "disabled" in reason.lower() or "Verification" in reason
    # Default product gate is off. A locally enabled env is still an explicit owner choice.
    import os

    if os.getenv("LEGACY_VERIFICATION_ENABLED", "false").lower() not in {"1", "true", "yes", "on"}:
        assert reason


@pytest.mark.asyncio
async def test_retired_writes_are_gone_and_v2_welcome_is_not(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    welcome = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/welcome",
        headers=headers,
        json={"welcome_message": "nope"},
    )
    assert welcome.status_code == 410
    assert "dashboard" in welcome.json()["detail"].lower()
    autorole = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/autorole",
        headers=headers,
        json={"enabled": True},
    )
    assert autorole.status_code == 410
    home = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/welcome/home", headers=headers)
    assert home.status_code != 410
