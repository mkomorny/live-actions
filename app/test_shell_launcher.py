"""Tests for shell_launcher (start-up preflight) and shell.parse_args.

No process is ever started and no registry is read: every OS touch is a fake.
"""

from __future__ import annotations

import unittest
from unittest import mock

import shell
import shell_launcher


class PreflightTests(unittest.TestCase):
    def test_everything_present_is_no_problems(self):
        self.assertEqual(shell_launcher.preflight(lambda name: object(), lambda: "153.0.4234.48"), [])

    def test_a_missing_module_names_the_package_and_the_fix(self):
        def imp(name):
            if name == "webview":
                raise ImportError(name)
            return object()
        problems = shell_launcher.preflight(imp, lambda: "1.0")
        self.assertEqual(len(problems), 1)
        self.assertIn("pywebview", problems[0])
        self.assertIn("pip install -r requirements.txt", shell_launcher.preflight_message(problems))

    def test_a_native_load_failure_counts_as_missing_too(self):
        def imp(name):
            if name == "clr":
                raise OSError("Python.Runtime.dll")
            return object()
        self.assertIn("pythonnet", shell_launcher.preflight(imp, lambda: "1.0")[0])

    def test_a_missing_runtime_is_reported_without_the_pip_hint(self):
        problems = shell_launcher.preflight(lambda name: object(), lambda: "")
        self.assertEqual(len(problems), 1)
        self.assertIn("WebView2", problems[0])
        self.assertNotIn("pip install", shell_launcher.preflight_message(problems))

    def test_every_problem_is_listed(self):
        def imp(name):
            raise ImportError(name)
        self.assertEqual(len(shell_launcher.preflight(imp, lambda: "")), 3)

    def test_the_registry_probe_returns_a_string_and_never_raises(self):
        self.assertIsInstance(shell_launcher.webview2_version(), str)


class ParseArgsTests(unittest.TestCase):
    def test_the_protocol_handler_argument_is_ignored(self):
        # `pythonw shell.py "liveactions://open"` is what Windows runs for the Max device's "Open desktop host".
        args = shell.parse_args(["liveactions://open"])
        self.assertFalse(args.demo_state)

    def test_real_flags_still_parse_next_to_the_url(self):
        args = shell.parse_args(["--demo-state", "--size", "1000x700", "liveactions://open"])
        self.assertTrue(args.demo_state)
        self.assertEqual(args.size, "1000x700")

    def test_an_unknown_flag_is_still_an_error(self):
        with self.assertRaises(SystemExit) as cm, mock.patch("sys.stderr"):
            shell.parse_args(["--bogus"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
