"""Tests for shell_model.SessionModel -- the pure-logic state behind the WebView2 shell.

No sockets, no window: `send` and `emit` are recording fakes and the clock is
injected, so connection/offline timing is deterministic.

Run from app\\:  python -m unittest test_shell_model
"""

from __future__ import annotations

import json
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import host_tools
import shell_model
import tool_manifests
from shell_model import SessionModel

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"


class FakeBridge:
    def __init__(self) -> None:
        self.last_pong = 0.0
        self.pending = False
        self.restarted = 0

    def has_pending_calls(self) -> bool:
        return self.pending

    def restart(self) -> None:
        self.restarted += 1


def tracks_json(selected: int | None = 1, n: int = 4) -> str:
    kinds = ["midi", "midi", "audio", "return"]
    return json.dumps({"ok": True, "tracks": [
        {"key": "%s:%d" % (kinds[i], i), "index": i, "name": "T%d" % i, "kind": kinds[i],
         "path": "live_set tracks %d" % i, "devices": ["Dev"], "selected_in_live": i == selected}
        for i in range(n)
    ]})


def make(tools=None, settings=None, **kw):
    sent: list[tuple] = []
    events: list[dict] = []
    bridge = FakeBridge()
    clock = kw.pop("clock", None) or (lambda: 1000.0)
    m = SessionModel(
        settings if settings is not None else {"listen_port": 11925, "bridge_port": 11924, "tool_prefs": {}},
        tools if tools is not None else [],
        send=lambda *a: sent.append(a), emit=events.append, bridge=bridge,
        save_settings=kw.pop("save_settings", lambda s: None), clock=clock, **kw,
    )
    return m, sent, events, bridge


def go_online(m):
    m.handle_osc("/live-actions/pong", [json.dumps({"on_track": True, "track": "Bridge"})])
    m.handle_osc("/live-actions/tracks", [tracks_json()])


class CatalogTests(unittest.TestCase):
    def test_real_manifests_load_and_resolve(self):
        cat = shell_model.build_catalog(tool_manifests.load_tools(TOOLS_DIR), {})
        ids = {t["id"] for t in cat}
        self.assertGreaterEqual(len(cat), 13)
        self.assertTrue({"detect-key", "audio-sample", "fill-forge", "song-mapper"} <= ids)
        by = {t["id"]: t for t in cat}
        self.assertEqual(by["detect-key"]["scope"], "set")
        self.assertEqual([f["id"] for f in by["detect-key"]["fields"]], ["scope", "profile", "results"])
        self.assertEqual(by["fill-forge"]["ui"], "webview")
        # the real audio-sample tool has far more than the preview's 8 fields -- none may be dropped
        self.assertGreater(len(by["audio-sample"]["fields"]), 8)
        self.assertEqual(by["audio-sample"]["fieldCount"], len(by["audio-sample"]["fields"]))

    def test_select_coercion_and_stored_prefs(self):
        tools = [{"id": "t", "name": "T", "fields": [
            {"id": "a", "type": "select", "options": ["x", "y"], "default": "nope"},
            {"id": "b", "type": "select", "options": [], "default": "d"},
            {"id": "c", "type": "text", "default": "manifest"},
        ]}]
        cat = shell_model.build_catalog(tools, {"tool_prefs": {"t": {"c": "saved", "a": "y"}}})
        f = {x["id"]: x for x in cat[0]["fields"]}
        self.assertEqual(f["a"]["default"], "y")          # stored pref wins
        self.assertEqual(f["b"]["type"], "text")           # empty select degrades to text
        self.assertEqual(f["c"]["default"], "saved")

    def test_options_source_tts_profiles_and_show_if_survive(self):
        tools = [{"id": "t", "name": "T", "fields": [
            {"id": "p", "type": "select", "optionsSource": "tts_profiles"},
            {"id": "q", "type": "text", "showIf": {"field": "p", "in": ["A"]}},
        ]}]
        cat = shell_model.build_catalog(tools, {"tts_profiles": [{"name": "A"}, {"name": "B"}]})
        f = {x["id"]: x for x in cat[0]["fields"]}
        self.assertEqual(f["p"]["options"], ["A", "B"])
        self.assertEqual(f["p"]["default"], "A")
        self.assertEqual(f["q"]["showIf"], {"field": "p", "in": ["A"]})

    def test_disabled_tool_hidden(self):
        cat = shell_model.build_catalog([{"id": "a", "enabled": False}, {"id": "b"}], {})
        self.assertEqual([t["id"] for t in cat], ["b"])

    def test_a_saved_tts_profile_reaches_the_tool_form_at_once(self):
        """Found by the v1.0.64 TTS e2e: the Profile dropdown was built once at start-up, so a profile added in Preferences
        did not appear (the field stayed a plain text box) until the app was restarted."""
        tools = [{"id": "tts", "name": "T", "fields": [{"id": "profile", "type": "select", "optionsSource": "tts_profiles"}]}]
        m, _, events, _ = make(tools=tools)
        field = lambda: m.snapshot()["tools"][0]["fields"][0]
        self.assertEqual((field()["type"], field()["options"]), ("text", None))
        events.clear()
        r = m.prefs.call("save_tts", {"profiles": [{"src": -1, "name": "Narrator", "provider": "cartesia", "key_mode": "typed", "api_key": "k"}]})
        self.assertTrue(r["ok"], r)
        self.assertEqual((field()["type"], field()["options"], field()["default"]), ("select", ["Narrator"], "Narrator"))
        pushed = [e for e in events if e.get("type") == "patch" and "tools" in e["patch"]]
        self.assertEqual(len(pushed), 1, "the page is sent the new catalog exactly once")
        self.assertEqual(pushed[0]["patch"]["tools"][0]["fields"][0]["options"], ["Narrator"])
        m.prefs.call("save_tts", {"profiles": []})
        self.assertEqual((field()["type"], field()["options"]), ("text", None))

    def test_a_refused_tts_save_does_not_refresh_or_change_the_catalog(self):
        tools = [{"id": "tts", "name": "T", "fields": [{"id": "profile", "type": "select", "optionsSource": "tts_profiles"}]}]
        m, _, events, _ = make(tools=tools)
        events.clear()
        r = m.prefs.call("save_tts", {"profiles": [{"src": -1, "name": "X", "provider": "nope", "key_mode": "typed", "api_key": "k"}]})
        self.assertFalse(r["ok"])
        self.assertEqual([e for e in events if e.get("type") == "patch" and "tools" in e["patch"]], [])
        self.assertEqual(m.snapshot()["tools"][0]["fields"][0]["type"], "text")

    def test_refresh_catalog_does_not_reread_manifests_or_log(self):
        m, _, _, _ = make(tools=[{"id": "a", "name": "A", "fields": []}])
        before = m.log_text()
        with mock.patch.object(tool_manifests, "load_tools", side_effect=AssertionError("must not reload manifests")):
            m.refresh_catalog()
        self.assertEqual(m.log_text(), before)


class TracksAndTargets(unittest.TestCase):
    def test_first_sync_ticks_live_selection_only(self):
        m, _s, ev, _b = make()
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=1)])
        self.assertEqual(m.target_keys(), ["midi:1"])
        snap = m.snapshot()
        self.assertEqual([t["kind"] for t in snap["tracks"]], ["MIDI", "MIDI", "AUD", "RET"])
        self.assertEqual([t["n"] for t in snap["tracks"]], [1, 2, 3, 4])

    def test_resync_keeps_user_ticks_and_prunes_removed(self):
        m, *_ = make()
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=1)])
        m.set_all(True)
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=0, n=3)])
        self.assertEqual(m.target_keys(), ["midi:0", "midi:1", "audio:2"])   # return:3 gone, Live's new selection not forced on

    def test_new_track_not_ticked_when_others_ticked(self):
        m, *_ = make()
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=1, n=3)])
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=3, n=4)])
        self.assertEqual(m.target_keys(), ["midi:1"])

    def test_toggle_all_none_live_sel(self):
        m, sent, ev, _b = make()
        m.handle_osc("/live-actions/tracks", [tracks_json(selected=2)])
        m.set_all(False)
        self.assertEqual(m.target_keys(), [])
        m.toggle_track("midi:0")
        m.toggle_track("nonexistent")
        self.assertEqual(m.target_keys(), ["midi:0"])
        m.use_live_selection()
        self.assertEqual(m.target_keys(), ["audio:2"])
        self.assertEqual(ev[-1], {"type": "patch", "patch": {"targets": ["audio:2"]}})

    def test_live_sel_with_no_tracks_requests_them(self):
        m, sent, *_ = make()
        m.use_live_selection()
        self.assertIn(("/live-actions/tracks",), sent)


class ConnectionTests(unittest.TestCase):
    def test_pong_connects_and_requests_status_and_tracks(self):
        m, sent, ev, _b = make()
        m.handle_osc("/live-actions/pong", [json.dumps({"on_track": True, "track": "Bridge"})])
        self.assertTrue(m.snapshot()["connected"])
        self.assertEqual(m.snapshot()["hostTrack"], "Bridge")
        self.assertIn(("/live-actions/status",), sent)
        self.assertIn(("/live-actions/tracks",), sent)
        self.assertTrue(any(e["type"] == "patch" and e["patch"].get("connected") is True for e in ev))

    def test_status_formats_set(self):
        m, *_ = make()
        go_online(m)
        m.handle_osc("/live-actions/status", [json.dumps({"ok": True, "name": "S.als", "tempo": 128, "tracks": 10, "time_signature": "3/4"})])
        self.assertEqual(m.snapshot()["set"], {"name": "S.als", "bpm": "128.00", "sig": "3/4", "tracks": 10})

    def test_status_error_and_bad_json_are_tolerated(self):
        m, *_ = make()
        m.handle_osc("/live-actions/status", [json.dumps({"ok": False, "error": "Live API not ready"})])
        self.assertEqual(m.snapshot()["set"]["name"], "Live API not ready")
        m.handle_osc("/live-actions/status", ["{not json"])
        m.handle_osc("/live-actions/tracks", ["{not json"])
        m.handle_osc("/live-actions/pong", [])

    def test_offline_after_silence_and_recovers(self):
        now = [1000.0]
        m, sent, ev, bridge = make(clock=lambda: now[0])
        bridge.last_pong = now[0]
        go_online(m)
        now[0] += shell_model.OFFLINE_AFTER_S - 0.5
        m.tick()
        self.assertTrue(m.snapshot()["connected"])
        now[0] += 1.0
        m.tick()
        snap = m.snapshot()
        self.assertFalse(snap["connected"])
        self.assertEqual(snap["set"]["name"], "(Waiting for Live Set...)")
        self.assertEqual(snap["ticker"], shell_model.OFFLINE_TICKER)
        self.assertIn(("/live-actions/ping",), sent)
        m.handle_osc("/live-actions/pong", [json.dumps({"on_track": True, "track": "Bridge"})])
        self.assertTrue(m.snapshot()["connected"])

    def test_pending_call_suppresses_offline(self):
        now = [1000.0]
        m, _s, _e, bridge = make(clock=lambda: now[0])
        go_online(m)
        bridge.last_pong = 0.0
        bridge.pending = True
        m.tick()
        self.assertTrue(m.snapshot()["connected"])

    def test_transport_error_is_logged_not_fatal(self):
        m, *_ = make()
        m.handle_osc("__error__", ["oversized or malformed packet dropped (x)"])
        self.assertIn("Bridge transport", m.log_text())

    def test_reset_bridge_restarts_and_notifies(self):
        m, sent, _e, bridge = make()
        self.assertTrue(m.reset_bridge()["ok"])
        self.assertEqual(bridge.restarted, 1)
        self.assertIn(("/live-actions/reset",), sent)

    def test_reset_bridge_reports_socket_failure(self):
        m, sent, _e, bridge = make()
        bridge.restart = mock.Mock(side_effect=OSError("port in use"))
        r = m.reset_bridge()
        self.assertFalse(r["ok"])
        self.assertNotIn(("/live-actions/reset",), sent)


class RunTests(unittest.TestCase):
    TOOLS = [
        {"id": "sel", "name": "Sel", "scope": "track", "fields": [{"id": "x", "type": "text", "default": "1"}]},
        {"id": "setwide", "name": "Wide", "scope": "set", "fields": []},
        {"id": "dlg", "name": "Dlg", "ui": "webview"},
        {"id": "hosty", "name": "Hosty", "runtime": "host", "fields": []},
    ]

    def test_offline_blocks_bridge_run(self):
        m, sent, *_ = make(self.TOOLS)
        r = m.run_tool("sel", {"x": "1"})
        self.assertFalse(r["ok"])
        self.assertIn("offline", r["message"])
        self.assertEqual(m.snapshot()["runs"]["sel"]["state"], "error")
        self.assertFalse([s for s in sent if s[0] == "/live-actions/run"])

    def test_track_scope_needs_ticked_tracks(self):
        m, sent, *_ = make(self.TOOLS)
        go_online(m)
        m.set_all(False)
        r = m.run_tool("sel", {})
        self.assertFalse(r["ok"])
        self.assertIn("No tracks selected", r["message"])

    def test_run_sends_only_ticked_tracks_and_all_fields(self):
        saved = []
        m, sent, ev, _b = make(self.TOOLS, save_settings=saved.append)
        go_online(m)
        m.set_all(False)
        m.toggle_track("midi:0")
        m.toggle_track("audio:2")
        r = m.run_tool("sel", {"x": "42", "hidden": "kept"})
        self.assertTrue(r["ok"])
        run = [s for s in sent if s[0] == "/live-actions/run"][0]
        self.assertEqual(run[1], "sel")
        payload = json.loads(run[2])
        self.assertEqual([t["key"] for t in payload["tracks"]], ["midi:0", "audio:2"])
        self.assertEqual(payload["tracks"][0]["path"], "live_set tracks 0")
        self.assertEqual(payload["fields"], {"x": "42", "hidden": "kept"})
        self.assertEqual(saved[-1]["tool_prefs"]["sel"], {"x": "42", "hidden": "kept"})
        self.assertEqual(m.snapshot()["runs"]["sel"]["state"], "running")

    def test_set_scope_runs_with_no_tracks(self):
        m, sent, *_ = make(self.TOOLS)
        go_online(m)
        m.set_all(False)
        self.assertTrue(m.run_tool("setwide", {})["ok"])
        self.assertEqual(json.loads([s for s in sent if s[0] == "/live-actions/run"][0][2])["tracks"], [])

    def test_result_finishes_the_run(self):
        m, *_ = make(self.TOOLS)
        go_online(m)
        m.run_tool("setwide", {})
        m.handle_osc("/live-actions/result", ["ok", "key C minor"])
        run = m.snapshot()["runs"]["setwide"]
        self.assertEqual(run["state"], "done")
        self.assertNotIn("ok key", run["message"])          # the status word is not part of the message
        self.assertIn("key C minor", run["message"])
        self.assertIn("Action completed", m.snapshot()["ticker"])

    def test_error_result_is_reported_as_an_error_not_as_done(self):
        m, *_ = make(self.TOOLS)
        go_online(m)
        m.run_tool("setwide", {})
        m.handle_osc("/live-actions/result", ["error", "Bad tool payload"])
        run = m.snapshot()["runs"]["setwide"]
        self.assertEqual(run["state"], "error")
        self.assertIn("Bad tool payload", run["message"])
        self.assertNotIn("Done", run["message"])
        self.assertIn("failed", m.snapshot()["ticker"])
        self.assertIn("Failed: Bad tool payload", m.log_text())

    def test_silent_bridge_times_out_with_a_warning(self):
        with mock.patch.object(shell_model, "RESULT_WAIT_S", 0.05):
            m, *_ = make(self.TOOLS)
            go_online(m)
            m.run_tool("setwide", {})
            deadline = time.time() + 2
            while time.time() < deadline and m.snapshot()["runs"]["setwide"]["state"] == "running":
                time.sleep(0.02)
        run = m.snapshot()["runs"]["setwide"]
        self.assertEqual(run["state"], "error")
        self.assertIn("No reply from Live", run["message"])

    def test_late_result_after_a_newer_run_does_not_warn_for_the_old_one(self):
        with mock.patch.object(shell_model, "RESULT_WAIT_S", 0.15):
            m, *_ = make(self.TOOLS)
            go_online(m)
            m.run_tool("setwide", {})
            m.run_tool("sel", {})          # bumps the wait id; first timer must go quiet
            m.handle_osc("/live-actions/result", ["ok"])
            time.sleep(0.4)
        self.assertEqual(m.snapshot()["runs"]["setwide"]["state"], "idle")     # closed out, not stuck "running"
        self.assertEqual(m.snapshot()["runs"]["setwide"]["message"], "Superseded by a newer run.")
        self.assertEqual(m.snapshot()["runs"]["sel"]["state"], "done")

    def test_webview_tool_without_a_dialog_host_says_so_instead_of_running(self):
        m, sent, *_ = make(self.TOOLS)
        go_online(m)
        r = m.run_tool("dlg", {})
        self.assertFalse(r["ok"])
        self.assertIn("not available", r["message"])
        self.assertEqual(m.snapshot()["runs"]["dlg"]["state"], "error")
        self.assertFalse([s for s in sent if s[0] == "/live-actions/run"])

    def test_unknown_tool(self):
        m, *_ = make(self.TOOLS)
        self.assertFalse(m.run_tool("nope", {})["ok"])

    def test_host_tool_runs_on_a_worker_and_reports_path(self):
        done = threading.Event()

        def handler(fields, settings):
            done.wait(2)
            return {"ok": True, "message": "made it", "path": "C:/out.wav"}

        with mock.patch.dict(host_tools.HOST_TOOLS, {"hosty": handler}):
            m, sent, *_ = make(self.TOOLS)
            r = m.run_tool("hosty", {})
            self.assertTrue(r["ok"])                                   # returned before the handler finished
            self.assertEqual(m.snapshot()["runs"]["hosty"]["state"], "running")
            self.assertFalse(m.run_tool("hosty", {})["ok"])            # second click while running is refused
            done.set()
            deadline = time.time() + 2
            while time.time() < deadline and m.snapshot()["runs"]["hosty"]["state"] == "running":
                time.sleep(0.02)
        run = m.snapshot()["runs"]["hosty"]
        self.assertEqual(run["state"], "done")
        self.assertIn("C:/out.wav", run["message"])
        self.assertFalse([s for s in sent if s[0] == "/live-actions/run"])   # host tools never touch OSC

    def test_host_tool_exception_becomes_an_error_result(self):
        with mock.patch.dict(host_tools.HOST_TOOLS, {"hosty": lambda f, s: 1 / 0}):
            m, *_ = make(self.TOOLS)
            m.run_tool("hosty", {})
            deadline = time.time() + 2
            while time.time() < deadline and m.snapshot()["runs"]["hosty"]["state"] == "running":
                time.sleep(0.02)
        self.assertEqual(m.snapshot()["runs"]["hosty"]["state"], "error")
        self.assertFalse(m._host_running)

    def test_host_tool_without_handler(self):
        with mock.patch.dict(host_tools.HOST_TOOLS, clear=True):
            m, *_ = make(self.TOOLS)
            self.assertFalse(m.run_tool("hosty", {})["ok"])


class MiscTests(unittest.TestCase):
    def test_log_is_capped_and_ordered(self):
        m, _s, ev, _b = make()
        for i in range(shell_model.LOG_LIMIT + 25):
            m.log("line %d" % i)
        snap = m.snapshot()
        self.assertEqual(len(snap["log"]), shell_model.LOG_LIMIT)
        self.assertEqual(snap["log"][-1][2], "line %d" % (shell_model.LOG_LIMIT + 24))

    def test_snapshot_and_runs_callback_atomically(self):
        m, _s, ev, _b = make()
        seen = []
        m.snapshot_and(lambda: seen.append(len(ev)))
        self.assertEqual(seen, [0])

    def test_snapshot_never_contains_secrets(self):
        m, *_ = make(settings={"api_key": "sk-SECRET", "api_keys": [{"key": "sk-SECRET"}], "listen_port": 1, "bridge_port": 2})
        self.assertNotIn("SECRET", json.dumps(m.snapshot()))

    def test_demo_state_matches_the_preview_mock(self):
        m, *_ = make()
        shell_model.load_demo_state(m)
        snap = m.snapshot()
        self.assertEqual(snap["set"]["name"], "Neon Nights 128.als")
        self.assertEqual(len(snap["tracks"]), 10)
        self.assertEqual([t["n"] for t in snap["tracks"] if t["key"] in snap["targets"]], [2, 3, 4])
        self.assertTrue(snap["connected"])


if __name__ == "__main__":
    unittest.main()
