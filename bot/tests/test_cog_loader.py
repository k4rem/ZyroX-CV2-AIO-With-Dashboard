"""Lazy cog loader isolation tests."""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

BOT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOT_ROOT)

from tests.import_utils import load_bot_submodule, load_utils_module


def _loader():
    return load_bot_submodule("cogs.cog_loader")


class TestCogLoaderSpecs(unittest.TestCase):
    def test_j2c_is_required(self):
        specs = _loader()._cog_specs()
        j2c = [s for s in specs if s.class_name == "JoinToCreate"]
        self.assertEqual(len(j2c), 1)
        self.assertTrue(j2c[0].required)

    def test_music_is_optional(self):
        specs = _loader()._cog_specs()
        music = [s for s in specs if s.class_name == "Music"]
        self.assertEqual(len(music), 1)
        self.assertFalse(music[0].required)


class TestCogLoaderIsolation(unittest.IsolatedAsyncioTestCase):
    async def test_optional_import_failure_does_not_fail_required_health(self):
        ModuleHealth = load_utils_module("module_health").ModuleHealth
        health = ModuleHealth()

        class FakeBot:
            async def add_cog(self, cog):
                return None

        bot = FakeBot()
        loader = _loader()
        CogSpec = loader.CogSpec
        bad = CogSpec("cogs.commands.__missing_module_phase0_test__", "X", False)
        good = CogSpec("cogs.commands.__missing_module_phase0_test2__", "Help", True)

        def fake_import(module_path, class_name):
            if "test2" in module_path:
                return type(
                    class_name,
                    (),
                    {"__init__": lambda self, bot: None},
                )
            raise ImportError("simulated optional import failure")

        with mock.patch.object(loader, "_import_cog_class", side_effect=fake_import):
            await loader._load_one(bot, health, bad)
            await loader._load_one(bot, health, good)

        self.assertEqual(len(health.optional_failed), 1)
        self.assertIn("Help", health.required_ok)
        self.assertTrue(health.healthy)

    async def test_required_import_failure_marks_unhealthy(self):
        ModuleHealth = load_utils_module("module_health").ModuleHealth
        health = ModuleHealth()
        loader = _loader()
        CogSpec = loader.CogSpec

        class FakeBot:
            async def add_cog(self, cog):
                return None

        bot = FakeBot()
        bad = CogSpec("cogs.commands.__missing_required_test__", "JoinToCreate", True)
        with mock.patch.object(
            loader, "_import_cog_class", side_effect=ImportError("simulated")
        ):
            await loader._load_one(bot, health, bad)
        self.assertFalse(health.healthy)
        self.assertEqual(len(health.required_failed), 1)


if __name__ == "__main__":
    unittest.main()
