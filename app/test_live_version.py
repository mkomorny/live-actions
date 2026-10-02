"""Tests for live_version.py -- the running Live version as a fact, not a guess."""

from __future__ import annotations

import unittest

import live_version


class RecordAndParseTests(unittest.TestCase):
    def setUp(self):
        live_version.reset()

    def test_bare_major_minor_patch(self):
        live_version.record("12.5.15")
        self.assertEqual(live_version.current(), {"raw": "12.5.15", "major": 12, "minor": 5, "patch": 15, "known": True})

    def test_beta_suffix_ignored(self):
        live_version.record("12.5.15.1b")
        cur = live_version.current()
        self.assertEqual((cur["major"], cur["minor"], cur["patch"]), (12, 5, 15))

    def test_live_prefix_and_beta_suffix(self):
        live_version.record("Live 12.4.14.1b")
        cur = live_version.current()
        self.assertEqual((cur["major"], cur["minor"], cur["patch"]), (12, 4, 14))

    def test_major_only(self):
        live_version.record("12")
        cur = live_version.current()
        self.assertEqual((cur["major"], cur["minor"], cur["patch"]), (12, 0, 0))
        self.assertTrue(cur["known"])

    def test_unparseable_does_not_clobber_known_good_reading(self):
        live_version.record("12.4.14")
        live_version.record("")
        live_version.record("not a version")
        cur = live_version.current()
        self.assertEqual((cur["major"], cur["minor"], cur["patch"]), (12, 4, 14))

    def test_initial_state_is_unknown(self):
        cur = live_version.current()
        self.assertFalse(cur["known"])
        self.assertIsNone(cur["major"])


class AtLeastTests(unittest.TestCase):
    def setUp(self):
        live_version.reset()

    def test_unknown_is_none_not_false(self):
        self.assertIsNone(live_version.at_least(12, 4))

    def test_exactly_the_gate_is_true(self):
        live_version.record("12.4.14.1b")
        self.assertTrue(live_version.at_least(12, 4))

    def test_newer_minor_is_true(self):
        live_version.record("12.5.15.1b")
        self.assertTrue(live_version.at_least(12, 4))

    def test_older_minor_is_false(self):
        live_version.record("12.3.6")
        self.assertFalse(live_version.at_least(12, 4))

    def test_older_major_is_false(self):
        live_version.record("11.3.25")
        self.assertFalse(live_version.at_least(12, 4))

    def test_newer_major_is_true_regardless_of_minor(self):
        live_version.record("13.0.0")
        self.assertTrue(live_version.at_least(12, 4))


class DescribeTests(unittest.TestCase):
    def setUp(self):
        live_version.reset()

    def test_unknown(self):
        self.assertEqual(live_version.describe(), "not read yet")

    def test_known(self):
        live_version.record("12.5.15.1b")
        self.assertEqual(live_version.describe(), "Ableton Live 12.5.15")


if __name__ == "__main__":
    unittest.main()
