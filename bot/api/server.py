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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import time
import json
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from utils.config import *


from api.routes import bot, guilds, admin, internal_sessions, access, system, security, snapshots, tickets_v2, logging_v2, commands_v2, growth_v2, messages, welcome, role_menus, role_automation
from api.dependencies import limiter
from api.auth.middleware import register_dashboard_auth_middleware
from api.db_manager import db_manager

# Configure logging
logger = logging.getLogger("api_request_logs")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_manager.close_all()

def create_app() -> FastAPI:
    """
    Initializes the FastAPI application for the CodeX Bot Dashboard.
    The bot instance will be attached to app.state.bot in CodeX.py at runtime.
    """
    app = FastAPI(
        title=f"{BRAND_NAME} Bot API",
        description=f"REST API to manage the {BRAND_NAME} Discord Bot features",
        version="1.0",
        lifespan=lifespan
    )

    register_dashboard_auth_middleware(app)

    # Structured Logging Middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info(json.dumps(log_data))
        return response

    # Attach limiter and handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    _cors = os.getenv("CORS_ORIGINS", "").strip()
    if _cors:
        _allowed_origins = [o.strip() for o in _cors.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(internal_sessions.router, prefix="/api/internal/v1", tags=["Internal"])
    app.include_router(bot.router, prefix="/api/v1/bot", tags=["Bot"])
    app.include_router(guilds.router, prefix="/api/v1/guilds", tags=["Guilds"])
    app.include_router(security.router, prefix="/api/v1/guilds", tags=["Security"])
    app.include_router(snapshots.router, prefix="/api/v1/guilds", tags=["Snapshots"])
    app.include_router(tickets_v2.router, prefix="/api/v1/guilds", tags=["Tickets V2"])
    app.include_router(role_menus.router, prefix="/api/v1/guilds", tags=["Role Menus"])
    app.include_router(role_automation.router, prefix="/api/v1/guilds", tags=["Role Automation"])
    app.include_router(logging_v2.router, prefix="/api/v1/guilds", tags=["Logging V2"])
    app.include_router(messages.router, prefix="/api/v1/guilds", tags=["Messages"])
    app.include_router(welcome.router, prefix="/api/v1/guilds", tags=["Welcome"])
    app.include_router(commands_v2.router, prefix="/api/v1/guilds", tags=["Commands"])
    app.include_router(growth_v2.router, prefix="/api/v1/guilds", tags=["Growth"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(access.router, prefix="/api/v1/access", tags=["Access"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])

    @app.get("/", summary="API Root", description="Returns basic API information and online status.")
    async def root():
        return {
            "status": "online",
            "bot_name": {BRAND_NAME},
            "api_version": "1.0"
        }

    @app.get("/health", summary="Health Check", description="Performs a health check for container orchestration and uptime monitoring.")
    async def health():
        return {"status": "ok"}

    return app
