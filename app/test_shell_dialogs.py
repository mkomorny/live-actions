"""Tests for shell_dialogs.DialogHost -- the native dialog windows of the three webview tools.

A fake window factory stands in for pywebview, so "the user pressed Insert" (api.receive) and "the user
closed the window" (on_closed) are just calls.

Run from app\\:  python -m unittest test_shell_dialogs
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import shell_dialogs
from shell_dialogs import DialogHost, embed_json, payload_from_raw


class FakeWindow:
    def __init__(self, title, url, api, on_closed):
        self.title, self.url, self.api, self.on_closed = title, url, api, on_closed
        self.destroyed = 0
        self.raised = 0
        self.html_at_open = Path(url.replace("file:///", "")).read_text(encoding="utf-8") if url.startswith("file:///") else None

    def destroy(self):
        self.destroyed += 1

    def raise_(self):
        self.raised += 1


class Harness:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.windows: list[FakeWindow] = []
        self.logs: list[str] = []
        self.host = DialogHost(self._open, temp_dir=self.tmp.name, log=self.logs.append)

    def _open(self, title, url, api, on_closed):
        w = FakeWindow(title, url, api, on_closed)
        self.windows.append(w)
        return w

    def files(self):
        return os.listdir(self.tmp.name)


class PayloadTests(unittest.TestCase):
    def test_close_and_send_is_unwrapped(self):
        raw = json.dumps({"method": "close_and_send", "params": [{"notes": [1]}]})
        self.assertEqual(payload_from_raw(raw), {"notes": [1]})

    def test_null_payload_and_empty_params_mean_cancel(self):
        self.assertIsNone(payload_from_raw(json.dumps({"method": "close_and_send", "params": [None]})))
        self.assertIsNone(payload_from_raw(json.dumps({"method": "close_and_send", "params": []})))

    def test_arrangement_helper_sends_a_json_string_inside_params(self):
        inner = json.dumps({"sectionTrackPath": "p"})
        self.assertEqual(payload_from_raw(json.dumps({"method": "close_and_send", "params": [inner]})), inner)

    def test_other_json_and_plain_text_pass_through(self):
        self.assertEqual(payload_from_raw('{"a": 1}'), {"a": 1})
        self.assertEqual(payload_from_raw("not json"), "not json")

    def test_embed_json_cannot_close_the_script_block(self):
        ctx = {"tracks": [{"name": "</script><script>alert(1)</script>"}], "sep": "a b"}
        text = embed_json(ctx)
        self.assertNotIn("<", text)
        self.assertNotIn(" ", text)
        self.assertEqual(json.loads(text), ctx)          # the dialog reads back the identical value


class HostTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.addCleanup(self.h.tmp.cleanup)
        self.results: list = []

    def open(self, tool="fill-forge", html="<html>x</html>"):
        return self.h.host.open(tool, "Title " + tool, html, self.results.append)

    def test_html_is_written_verbatim_and_loaded_by_file_url(self):
        self.assertEqual(self.open(html="<html>ctx</html>"), "opened")
        w = self.h.windows[0]
        self.assertTrue(w.url.startswith("file:///"))
        self.assertEqual(w.html_at_open, "<html>ctx</html>")
        self.assertEqual(w.title, "Title fill-forge")
        self.assertTrue(self.h.host.is_open("fill-forge"))
        self.assertFalse(self.h.host.is_open("song-mapper"))

    def test_the_api_the_page_can_reach_is_exactly_receive(self):
        self.open()
        api = self.h.windows[0].api
        public = [n for n in dir(api) if not n.startswith("_")]
        self.assertEqual(public, ["receive"])

    def test_receive_delivers_once_closes_the_window_and_removes_the_file(self):
        self.open()
        w = self.h.windows[0]
        w.api.receive(json.dumps({"method": "close_and_send", "params": [{"target": "newClip"}]}))
        self.assertEqual(self.results, [{"target": "newClip"}])
        self.assertEqual(w.destroyed, 1)
        self.assertEqual(self.h.files(), [])
        self.assertFalse(self.h.host.is_open())
        w.api.receive("{}")                               # a second send (double-click) is ignored
        w.on_closed()                                     # ...and so is the closed event that follows the destroy
        self.assertEqual(len(self.results), 1)

    def test_closing_the_window_without_sending_is_a_cancel(self):
        self.open()
        self.h.windows[0].on_closed()
        self.assertEqual(self.results, [None])
        self.assertEqual(self.h.files(), [])

    def test_same_tool_again_raises_and_opens_nothing(self):
        self.open()
        self.assertEqual(self.open(), "raised")
        self.assertEqual(len(self.h.windows), 1)
        self.assertEqual(self.h.windows[0].raised, 1)
        self.assertEqual(self.results, [])

    def test_a_different_tool_replaces_the_open_one_and_cancels_it(self):
        self.open("fill-forge")
        got: list = []
        self.assertEqual(self.h.host.open("song-mapper", "Song Mapper", "<b/>", got.append), "replaced")
        self.assertEqual(self.results, [None])            # the old dialog's handler was told it was cancelled
        self.assertEqual(self.h.windows[0].destroyed, 1)
        self.assertEqual(len(self.h.windows), 2)
        self.assertTrue(self.h.host.is_open("song-mapper"))
        self.assertEqual(len(self.h.files()), 1)

    def test_close_all_cancels_and_cleans_up(self):
        self.open()
        self.h.host.close_all()
        self.assertEqual(self.results, [None])
        self.assertEqual(self.h.files(), [])
        self.h.host.close_all()                           # idempotent
        self.assertEqual(self.results, [None])

    def test_a_window_that_fails_to_open_leaves_nothing_behind(self):
        def boom(*_a):
            raise RuntimeError("no webview2")
        host = DialogHost(boom, temp_dir=self.h.tmp.name)
        with self.assertRaises(RuntimeError):
            host.open("fill-forge", "T", "<x/>", self.results.append)
        self.assertEqual(self.h.files(), [])
        self.assertFalse(host.is_open())

    def test_a_result_handler_that_raises_does_not_wedge_the_host(self):
        def bad(_p):
            raise ValueError("handler bug")
        self.h.host.open("fill-forge", "T", "<x/>", bad)
        self.h.windows[0].on_closed()                     # must not raise into the GUI thread
        self.assertTrue(any("handler failed" in l for l in self.h.logs))
        self.assertEqual(self.open("song-mapper"), "opened")  # and the next dialog still opens

    def test_a_window_that_is_already_gone_when_destroyed_is_fine(self):
        self.open()
        w = self.h.windows[0]

        def gone():
            raise RuntimeError("already closed")
        w.destroy = gone
        w.api.receive(json.dumps({"method": "close_and_send", "params": [{"a": 1}]}))
        self.assertEqual(self.results, [{"a": 1}])


class ShimTests(unittest.TestCase):
    def test_shim_defines_a_separate_property_not_chrome_webview(self):
        self.assertIn("window.liveActionsSend", shell_dialogs.SEND_SHIM)
        self.assertNotIn("chrome.webview", shell_dialogs.SEND_SHIM)


if __name__ == "__main__":
    unittest.main()
