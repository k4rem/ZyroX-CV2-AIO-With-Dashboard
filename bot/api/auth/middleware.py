"""HTTP middleware: internal service auth + dashboard identity JWT."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from api.auth.identity import resolve_auth_from_token
from api.auth.policy import (
    INTERNAL_PREFIX,
    PUBLIC_PATHS,
    apply_request_auth,
)
from api.dependencies import get_bot
from cls_platform.config import INTERNAL_SERVICE_KEY


def _extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()


def verify_internal_service_key(request: Request) -> None:
    if not INTERNAL_SERVICE_KEY:
        raise HTTPException(status_code=503, detail="Internal service auth not configured")
    provided = request.headers.get("x-internal-service-key") or request.headers.get(
        "X-Internal-Service-Key"
    )
    if not provided or provided != INTERNAL_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal service credentials")


def register_dashboard_auth_middleware(app) -> None:
    @app.middleware("http")
    async def dashboard_auth_middleware(request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        if path.startswith(INTERNAL_PREFIX):
            try:
                verify_internal_service_key(request)
            except HTTPException as exc:
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
            return await call_next(request)

        token = _extract_bearer(request)
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        try:
            auth = await resolve_auth_from_token(token)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        request.state.dashboard_auth = auth
        bot = request.app.state.bot
        if bot is None:
            return JSONResponse(status_code=503, content={"detail": "Bot not ready"})
        try:
            await apply_request_auth(request, auth, bot)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        return await call_next(request)
