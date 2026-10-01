"""FastAPI + platform lifecycle on the Discord bot event loop."""

from __future__ import annotations

import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI

from cls_platform.config import POSTGRES_ENABLED, root_owner_configured
from cls_platform.database import close_database, init_database
from cls_platform.services.scheduler import scheduler_worker_loop
from utils.api_bind import ApiBindConfig


class ApiLifecycle:
    def __init__(self) -> None:
        self._server: Optional[uvicorn.Server] = None
        self._serve_task: Optional[asyncio.Task] = None
        self._scheduler_stop: Optional[asyncio.Event] = None
        self._scheduler_task: Optional[asyncio.Task] = None

    async def startup(self, app: FastAPI, bot, api_cfg: ApiBindConfig) -> None:
        if POSTGRES_ENABLED:
            await init_database()
            if not root_owner_configured():
                print("\033[33m[*] ROOT_OWNER_ID is not set; root Dashboard operations fail closed.\033[0m")

        from cls_platform.scheduler_bootstrap import (
            ensure_recurring_security_jobs,
            register_scheduler_handlers,
        )

        register_scheduler_handlers(bot)
        if POSTGRES_ENABLED:
            await ensure_recurring_security_jobs()

        self._scheduler_stop = asyncio.Event()
        self._scheduler_task = asyncio.create_task(
            scheduler_worker_loop(self._scheduler_stop),
            name="cls-scheduler-worker",
        )

        if not api_cfg.enabled:
            print("\033[33m[*] API Server: Disabled via API_ENABLED=false\033[0m")
            return

        config = uvicorn.Config(
            app,
            host=api_cfg.host,
            port=api_cfg.port,
            log_level="warning",
            loop="asyncio",
        )
        self._server = uvicorn.Server(config)
        self._serve_task = asyncio.create_task(self._server.serve(), name="cls-uvicorn")
        print(f"\033[32m[*] API Server: Starting on {api_cfg.host}:{api_cfg.port} (bot loop)\033[0m")

    async def shutdown(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
            if self._serve_task:
                await self._serve_task
        if self._scheduler_stop is not None:
            self._scheduler_stop.set()
        if self._scheduler_task:
            await self._scheduler_task
        await close_database()


_api_lifecycle = ApiLifecycle()


def get_api_lifecycle() -> ApiLifecycle:
    return _api_lifecycle


def attach_bot_lifecycle(bot, app: FastAPI, api_cfg: ApiBindConfig) -> None:
    original_setup = bot.setup_hook

    async def setup_hook():
        await original_setup()
        from cls_platform.commands.policy import install_command_gate

        install_command_gate(bot)
        await _api_lifecycle.startup(app, bot, api_cfg)

    bot.setup_hook = setup_hook  # type: ignore[method-assign]

    original_close = bot.close

    async def close():
        await _api_lifecycle.shutdown()
        await original_close()

    bot.close = close  # type: ignore[method-assign]
