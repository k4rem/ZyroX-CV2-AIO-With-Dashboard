"""Module loader isolation tests (static)."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.import_utils import load_utils_module

ModuleHealth = load_utils_module("module_health").ModuleHealth


class TestModuleLoaderFoundation(unittest.TestCase):
    def test_optional_failure_does_not_clear_required_ok(self):
        health = ModuleHealth()
        health.record_ok("Tickets", True)
        health.record_ok("JoinToCreate", True)
        health.record_fail("Music", False, RuntimeError("lavalink down"))
        self.assertTrue(health.healthy)
        self.assertEqual(len(health.required_ok), 2)
        self.assertEqual(len(health.optional_failed), 1)

    def test_required_failure_unhealthy(self):
        health = ModuleHealth()
        health.record_fail("JoinToCreate", True, RuntimeError("missing"))
        self.assertFalse(health.healthy)


if __name__ == "__main__":
    unittest.main()
