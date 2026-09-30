"""Local filesystem storage abstraction (Phase 1)."""

from __future__ import annotations

import os
from pathlib import Path

from cls_platform.config import STORAGE_ROOT


class StorageError(Exception):
    pass


def _safe_path(namespace: str, key: str) -> Path:
    if not namespace or ".." in namespace or "/" in namespace or "\\" in namespace:
        raise StorageError("Invalid namespace")
    if not key or ".." in key:
        raise StorageError("Invalid key")
    root = Path(STORAGE_ROOT).resolve()
    full = (root / namespace / key).resolve()
    if not str(full).startswith(str(root)):
        raise StorageError("Path traversal blocked")
    return full


async def put(namespace: str, key: str, data: bytes) -> None:
    path = _safe_path(namespace, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


async def get(namespace: str, key: str) -> bytes | None:
    path = _safe_path(namespace, key)
    if not path.is_file():
        return None
    return path.read_bytes()


async def delete(namespace: str, key: str) -> bool:
    path = _safe_path(namespace, key)
    if not path.is_file():
        return False
    os.remove(path)
    return True


async def exists(namespace: str, key: str) -> bool:
    return _safe_path(namespace, key).is_file()
