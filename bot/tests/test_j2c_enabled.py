"""Disabling Join to Create must not be treated as armed."""

import unittest

from utils.j2c_state import j2c_should_arm


class J2CArmTests(unittest.TestCase):
    def test_disabled_keeps_channels_but_does_not_arm(self):
        self.assertFalse(j2c_should_arm(False, 1234567890123456789, 2234567890123456789))
        self.assertFalse(j2c_should_arm(0, 1, 2))

    def test_enabled_requires_both_channels(self):
        self.assertTrue(j2c_should_arm(True, 11, 22))
        self.assertFalse(j2c_should_arm(True, 11, None))
        self.assertFalse(j2c_should_arm(True, None, 22))

    def test_missing_flag_does_not_arm(self):
        self.assertFalse(j2c_should_arm(None, 11, 22))


if __name__ == "__main__":
    unittest.main()
