"""Cog setup must publish module health where the system health report reads it."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest
from unittest import mock

BOT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_ROOT)

from tests.import_utils import load_utils_module


def _load_cogs_setup(health):
    core = types.ModuleType("core")
    core.zyrox = object
    cog_loader = types.ModuleType("cogs.cog_loader")

    async def load_all_cogs(bot):
        return health

    cog_loader.load_all_cogs = load_all_cogs
    config = types.ModuleType("utils.config")
    config.BotName = "CLS"
    stubs = {"core": core, "cogs.cog_loader": cog_loader, "utils.config": config}

    path = os.path.join(BOT_ROOT, "cogs", "__init__.py")
    spec = importlib.util.spec_from_file_location("_cls_cogs_setup_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, stubs):
        spec.loader.exec_module(mod)
    return mod.setup


class TestModuleHealthWiring(unittest.IsolatedAsyncioTestCase):
    async def test_setup_health_is_visible_to_report(self):
        mh_mod = load_utils_module("module_health")
        health = mh_mod.ModuleHealth()
        health.record_ok("Logging", True)
        health.record_fail("Moderation", True, ImportError("simulated"))

        bot = types.SimpleNamespace()
        with mock.patch("builtins.print"):
            await _load_cogs_setup(health)(bot)

        report = mh_mod.required_modules_report(bot)
        self.assertEqual(report["required_ok"], ["Logging"])
        self.assertEqual([f["name"] for f in report["required_failed"]], ["Moderation"])
        self.assertFalse(report["healthy"])


if __name__ == "__main__":
    unittest.main()
