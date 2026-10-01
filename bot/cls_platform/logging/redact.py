"""Strip secrets from stored log payloads."""

from __future__ import annotations

import re

_SECRET_KEYS = {
    "token",
    "secret",
    "password",
    "authorization",
    "cookie",
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
}
_TOKEN = re.compile(r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{5,}\.[A-Za-z0-9_\-]{20,}")


def redact(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if str(key).lower() in _SECRET_KEYS:
                cleaned[key] = "[redacted]"
            else:
                cleaned[key] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _TOKEN.sub("[redacted]", value)
    return value
