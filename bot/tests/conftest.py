"""Phase 1 integration test fixtures (disposable Postgres + FastAPI app)."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# bot/ on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("ALLOW_EMPTY_GUILD_ALLOWLIST", "true")
os.environ.setdefault("ALLOWED_GUILD_IDS", "100000000000000100,100000000000000200")
os.environ["POSTGRES_ENABLED"] = "true"
os.environ["INTERNAL_IDENTITY_SIGNING_KEY"] = "phase1-test-signing-key-32bytes!!"
os.environ["INTERNAL_IDENTITY_AUDIENCE"] = "cls-fastapi"
os.environ["INTERNAL_SERVICE_KEY"] = "phase1-internal-service-key"
os.environ["ROOT_OWNER_ID"] = "900000000000000001"
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:cls@127.0.0.1:5433/cls_discord_test",
)

TEST_GUILD_A = 100000000000000100
TEST_GUILD_B = 100000000000000200
TEST_USER = 800000000000000001
TEST_ROOT = 900000000000000001
TEST_ROLE_A = 100001
TEST_ROLE_B = 200001
TEST_CHANNEL_A = 100002


def _postgres_reachable() -> bool:
    try:
        import asyncio
        import asyncpg

        async def ping():
            conn = await asyncpg.connect(
                host="127.0.0.1", port=5433, user="postgres", password="cls", database="postgres"
            )
            await conn.close()

        asyncio.run(ping())
        return True
    except Exception:
        return False


def _ensure_test_db():
    import asyncio
    import asyncpg

    async def setup():
        conn = await asyncpg.connect(
            host="127.0.0.1", port=5433, user="postgres", password="cls", database="postgres"
        )
        await conn.execute("SELECT 1 FROM pg_database WHERE datname='cls_discord_test'")
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", "cls_discord_test"
        )
        if not exists:
            await conn.execute('CREATE DATABASE cls_discord_test')
        await conn.close()

    asyncio.run(setup())


def _run_alembic_upgrade():
    bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=bot_dir,
        env=env,
        check=True,
        capture_output=True,
    )


def _assert_disposable_database() -> None:
    """``db_reset`` TRUNCATEs platform tables. Never let it touch a non-test database (e.g. the local preview DB)."""
    from urllib.parse import urlparse

    name = urlparse(os.environ.get("DATABASE_URL", "")).path.lstrip("/")
    if not name.endswith("_test"):
        pytest.exit(
            f"Refusing to run DB integration tests against database {name!r}: "
            "DATABASE_URL must point at a disposable database whose name ends with '_test'.",
            returncode=2,
        )


@pytest.fixture(scope="session")
def postgres_ready():
    _assert_disposable_database()
    if not _postgres_reachable():
        pytest.skip("Local PostgreSQL not reachable (start docker compose postgres)")
    _ensure_test_db()
    _run_alembic_upgrade()
    return True


@pytest_asyncio.fixture
async def db_reset(postgres_ready):
    from cls_platform.database import close_database, init_database
    from sqlalchemy import text
    from cls_platform.database import get_session_factory

    await close_database()
    await init_database()
    factory = get_session_factory()
    async with factory() as session:
        for table in (
            "dashboard_grants",
            "audit_events",
            "scheduler_jobs",
            "dashboard_sessions",
            "snapshot_metadata",
        ):
            await session.execute(text(f"TRUNCATE {table} RESTART IDENTITY CASCADE"))
        await session.commit()
    yield
    await close_database()


@pytest_asyncio.fixture
async def fake_bot():
    from tests.fixtures.fake_bot import FakeBot, FakeChannel, FakeGuild, FakeRole

    guild_a = FakeGuild(
        id=TEST_GUILD_A,
        roles=[FakeRole(id=TEST_ROLE_A)],
        channels=[FakeChannel(id=TEST_CHANNEL_A)],
    )
    guild_b = FakeGuild(
        id=TEST_GUILD_B,
        roles=[FakeRole(id=TEST_ROLE_B)],
        channels=[FakeChannel(id=200002)],
    )
    return FakeBot([guild_a, guild_b])


def _ensure_real_utils_package() -> None:
    """Phase 0 tests stub ``utils`` via import_utils; allow API imports without full utils/__init__.py."""
    import importlib
    import sys

    utils = sys.modules.get("utils")
    if utils is not None and hasattr(utils, "getConfig"):
        return
    for key in list(sys.modules):
        if key.startswith("api.") or key == "core" or key.startswith("core."):
            del sys.modules[key]
    if utils is not None and not hasattr(utils, "getConfig"):
        del sys.modules["utils"]
    for key in list(sys.modules):
        if key == "utils.module_health" or key == "utils.api_bind":
            del sys.modules[key]
    importlib.import_module("utils.config")


@pytest_asyncio.fixture
async def api_client(db_reset, fake_bot):
    from api.auth import allowlist as allowlist_loader

    allowlist_loader.clear_allowlist_cache()
    _ensure_real_utils_package()
    from api.server import create_app

    from api.dependencies import set_bot

    app = create_app()
    set_bot(fake_bot)
    app.state.bot = fake_bot
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, app


def mint_identity_token(user_id: int, session_id: uuid.UUID, *, exp_seconds: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "aud": os.environ["INTERNAL_IDENTITY_AUDIENCE"],
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=exp_seconds)).timestamp()),
    }
    return jwt.encode(
        payload,
        os.environ["INTERNAL_IDENTITY_SIGNING_KEY"],
        algorithm="HS256",
    )


async def create_test_session(user_id: int) -> uuid.UUID:
    from cls_platform.services.sessions import create_session

    return await create_session(user_id, ttl_hours=24)


async def auth_headers(user_id: int) -> dict[str, str]:
    sid = await create_test_session(user_id)
    token = mint_identity_token(user_id, sid)
    return {"Authorization": f"Bearer {token}"}
