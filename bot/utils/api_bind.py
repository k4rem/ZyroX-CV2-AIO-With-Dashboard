"""FastAPI bind host validation (Phase 0 — loopback by default)."""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from typing import Optional

from .env_parse import parse_env_bool


def _normalize_host(host: str) -> str:
    h = host.strip()
    if h in ("localhost",):
        return "127.0.0.1"
    return h


def _is_loopback_bind(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_loopback:
            return True
    return False


@dataclass(frozen=True)
class ApiBindConfig:
    enabled: bool
    host: str
    port: int
    allow_public_bind: bool


def load_api_bind_config() -> ApiBindConfig:
    enabled = parse_env_bool("API_ENABLED", "false")
    allow_public = parse_env_bool("API_ALLOW_PUBLIC_BIND", "false")
    host = _normalize_host(os.getenv("API_HOST", "127.0.0.1"))
    port_raw = os.getenv("API_PORT", "8000").strip()
    if not port_raw.isdigit():
        raise SystemExit(
            f"Startup stopped: API_PORT must be a positive integer. Got {port_raw!r}."
        )
    port = int(port_raw)
    if port < 1 or port > 65535:
        raise SystemExit(f"Startup stopped: API_PORT out of range: {port}")
    return ApiBindConfig(
        enabled=enabled,
        host=host,
        port=port,
        allow_public_bind=allow_public,
    )


def validate_api_bind_or_exit(cfg: ApiBindConfig) -> None:
    if not cfg.enabled:
        return
    if _is_loopback_bind(cfg.host):
        return
    if cfg.allow_public_bind:
        return
    raise SystemExit(
        "Startup stopped: API bind "
        f"{cfg.host!r} is not loopback. "
        "Set API_HOST=127.0.0.1 or explicitly opt in with API_ALLOW_PUBLIC_BIND=true."
    )
