"""Phase 0 offline security tests."""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

# bot/ as import root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.import_utils import load_utils_module


class TestSafeOutbound(unittest.TestCase):
    def test_allow_public_https(self):
        validate_http_url = load_utils_module("safe_outbound").validate_http_url

        self.assertEqual(
            validate_http_url("https://example.com/image.png"),
            "https://example.com/image.png",
        )

    def test_reject_private_and_bad_schemes(self):
        mod = load_utils_module("safe_outbound")
        UnsafeURLError = mod.UnsafeURLError
        validate_http_url = mod.validate_http_url

        bad = [
            "http://3232235777",
            "http://[::ffff:127.0.0.1]",
            "http://127.0.0.1",
            "http://localhost",
            "http://169.254.169.254",
            "http://10.0.0.1",
            "http://172.16.0.1",
            "http://192.168.1.1",
            "http://[::1]",
            "file:///etc/passwd",
            "ftp://example.com/x",
            "http://user:pass@example.com",
        ]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(UnsafeURLError):
                    validate_http_url(url)


class TestEnvParse(unittest.TestCase):
    def test_bool_strict(self):
        env_parse = load_utils_module("env_parse")

        with mock.patch.dict(os.environ, {"API_ENABLED": "maybe"}, clear=False):
            with self.assertRaises(SystemExit):
                env_parse.parse_env_bool("API_ENABLED", "false")

    def test_guild_ids_invalid(self):
        env_parse = load_utils_module("env_parse")

        with mock.patch.dict(os.environ, {"ALLOWED_GUILD_IDS": "abc"}, clear=False):
            with self.assertRaises(SystemExit):
                env_parse.parse_discord_snowflake_list("ALLOWED_GUILD_IDS")

    def test_guild_ids_valid(self):
        env_parse = load_utils_module("env_parse")

        gid = "1448947999123308687"
        with mock.patch.dict(os.environ, {"ALLOWED_GUILD_IDS": gid}, clear=False):
            ids = env_parse.parse_discord_snowflake_list("ALLOWED_GUILD_IDS")
            self.assertIn(int(gid), ids)


class TestApiBind(unittest.TestCase):
    def test_api_disabled_unsafe_host_allowed(self):
        api_bind = load_utils_module("api_bind")
        ApiBindConfig = api_bind.ApiBindConfig
        validate_api_bind_or_exit = api_bind.validate_api_bind_or_exit

        cfg = ApiBindConfig(
            enabled=False, host="0.0.0.0", port=8000, allow_public_bind=False
        )
        validate_api_bind_or_exit(cfg)

    def test_api_enabled_unsafe_host_opt_in_allowed(self):
        api_bind = load_utils_module("api_bind")
        ApiBindConfig = api_bind.ApiBindConfig
        validate_api_bind_or_exit = api_bind.validate_api_bind_or_exit

        cfg = ApiBindConfig(
            enabled=True, host="0.0.0.0", port=8000, allow_public_bind=True
        )
        validate_api_bind_or_exit(cfg)

    def test_public_bind_blocked_without_opt_in(self):
        api_bind = load_utils_module("api_bind")
        ApiBindConfig = api_bind.ApiBindConfig
        validate_api_bind_or_exit = api_bind.validate_api_bind_or_exit

        cfg = ApiBindConfig(
            enabled=True, host="0.0.0.0", port=8000, allow_public_bind=False
        )
        with self.assertRaises(SystemExit):
            validate_api_bind_or_exit(cfg)

    def test_loopback_allowed(self):
        api_bind = load_utils_module("api_bind")
        ApiBindConfig = api_bind.ApiBindConfig
        validate_api_bind_or_exit = api_bind.validate_api_bind_or_exit

        cfg = ApiBindConfig(
            enabled=True, host="127.0.0.1", port=8000, allow_public_bind=False
        )
        validate_api_bind_or_exit(cfg)


class TestLegacyVerification(unittest.TestCase):
    def test_default_disabled(self):
        with mock.patch.dict(
            os.environ, {"LEGACY_VERIFICATION_ENABLED": "false"}, clear=False
        ):
            lv = load_utils_module("legacy_verification")
            self.assertFalse(lv.legacy_verification_mutations_allowed())


class TestGuildAllowlistConfig(unittest.TestCase):
    def test_empty_allowlist_fails_without_dev_override(self):
        with mock.patch.dict(
            os.environ,
            {
                "ALLOWED_GUILD_IDS": "",
                "ALLOW_EMPTY_GUILD_ALLOWLIST": "false",
            },
            clear=False,
        ):
            with self.assertRaises(SystemExit):
                load_utils_module("guild_allowlist", reload=True)

    def test_empty_allowlist_allowed_with_dev_override(self):
        with mock.patch.dict(
            os.environ,
            {
                "ALLOWED_GUILD_IDS": "",
                "ALLOW_EMPTY_GUILD_ALLOWLIST": "true",
            },
            clear=False,
        ):
            ga = load_utils_module("guild_allowlist", reload=True)
            self.assertTrue(ga.DEV_UNRESTRICTED_GUILDS)
            self.assertTrue(ga.is_guild_allowed(123456789012345678))


class TestModuleHealth(unittest.TestCase):
    def test_required_failure_marks_unhealthy(self):
        ModuleHealth = load_utils_module("module_health").ModuleHealth

        h = ModuleHealth()
        h.record_ok("Tickets", True)
        h.record_fail("Moderation", True, RuntimeError("boom"))
        self.assertFalse(h.healthy)


if __name__ == "__main__":
    unittest.main()
