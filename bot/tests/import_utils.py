"""Import utils submodules without loading utils/__init__.py (discord dependency)."""

from __future__ import annotations

import importlib.util
import os
import sys
import types  # noqa: F401 — used by load_bot_submodule

_UTILS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils")
_CACHE: dict[str, object] = {}


def _ensure_utils_package() -> None:
    if "utils" in sys.modules:
        return
    pkg = types.ModuleType("utils")
    pkg.__path__ = [_UTILS_DIR]  # type: ignore[attr-defined]
    sys.modules["utils"] = pkg


def load_bot_submodule(relative: str):
    """Load bot/cogs/*.py or bot/utils/*.py without utils/__init__.py side effects."""
    _ensure_utils_package()
    mh = load_utils_module("module_health")
    sys.modules["utils.module_health"] = mh
    rel_path = relative.replace(".", os.sep).replace("/", os.sep)
    path = os.path.join(os.path.dirname(_UTILS_DIR), rel_path + ".py")
    fq = relative.replace("/", ".")
    if fq.startswith("cogs."):
        if "cogs" not in sys.modules:
            cogs_pkg = types.ModuleType("cogs")
            cogs_pkg.__path__ = [os.path.join(os.path.dirname(_UTILS_DIR), "cogs")]
            sys.modules["cogs"] = cogs_pkg
    spec = importlib.util.spec_from_file_location(fq, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {relative} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fq] = mod
    spec.loader.exec_module(mod)
    return mod


def load_utils_module(module_name: str, *, reload: bool = False):
    if reload:
        _CACHE.pop(module_name, None)
        sys.modules.pop(f"utils.{module_name}", None)
    if module_name in _CACHE:
        return _CACHE[module_name]
    _ensure_utils_package()
    path = os.path.join(_UTILS_DIR, f"{module_name}.py")
    fq = f"utils.{module_name}"
    spec = importlib.util.spec_from_file_location(fq, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fq] = mod
    spec.loader.exec_module(mod)
    _CACHE[module_name] = mod
    return mod
