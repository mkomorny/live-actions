"""Tests for shell_bridge (UiBus, Ticker, ShellApi) and the model <-> BridgeClient <-> UiBus
chain over REAL UDP loopback against shell_dev.mock_live.MockLive.

The window is a fake that records evaluate_js calls (and which thread made them), so all of
this runs without pywebview or a display.

Run from app\\:  python -m unittest test_shell_bridge
"""

from __future__ import annotations

import inspect
import json
import threading
import time
import unittest
from unittest import mock

import bridge_client
import shell_bridge
import shell_model
from shell_bridge import ShellApi, Ticker, UiBus
from shell_dev.mock_live import MockLive
from shell_model import SessionModel

LISTEN, BRIDGE = 23925, 23924   # loopback ports for these tests only


class FakeWindow:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.threads: set[str] = set()
        self.dialog_result = None

    def evaluate_js(self, js: str):
        self.calls.append(js)
        self.threads.add(threading.current_thread().name)

    def events(self) -> list[dict]:
        prefix = "window.__uiBusRecv && window.__uiBusRecv("
        return [json.loads(c[len(prefix):-1]) for c in self.calls if c.startswith(prefix)]

    def create_file_dialog(self, *_a, **_k):
        return self.dialog_result


def wait_until(fn, timeout=3.0, step=0.02):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(step)
    return False


class UiBusTests(unittest.TestCase):
    def test_events_wait_for_the_gate_and_arrive_in_order_on_one_thread(self):
        win = FakeWindow()
        bus = UiBus(win.evaluate_js)
        bus.start()
        for i in range(5):
            bus.push({"type": "log", "line": ["t", "•", "before %d" % i]})
        time.sleep(0.15)
        self.assertEqual(win.calls, [])                      # gate closed: nothing delivered yet
        bus.open_gate()                                      # the snapshot already contains those five
        for i in range(50):
            bus.push({"type": "log", "line": ["t", "•", "after %d" % i]})
        self.assertTrue(wait_until(lambda: len(win.events()) == 50))
        bus.stop()
        lines = [e["line"][2] for e in win.events()]
        self.assertEqual(lines, ["after %d" % i for i in range(50)])
        self.assertEqual([e["seq"] for e in win.events()], list(range(1, 51)))
        self.assertEqual(win.threads, {"ui-bus-pusher"})     # evaluate_js only ever from the pusher

    def test_concurrent_producers_never_interleave_or_drop(self):
        win = FakeWindow()
        bus = UiBus(win.evaluate_js)
        bus.start()
        bus.open_gate()

        def produce(tag):
            for i in range(100):
                bus.push({"type": "log", "line": ["t", tag, str(i)]})

        threads = [threading.Thread(target=produce, args=(t,)) for t in "abcd"]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertTrue(wait_until(lambda: len(win.events()) == 400))
        bus.stop()
        ev = win.events()
        self.assertEqual([e["seq"] for e in ev], list(range(1, 401)))
        for tag in "abcd":                                    # per-producer order preserved
            self.assertEqual([int(e["line"][2]) for e in ev if e["line"][1] == tag], list(range(100)))

    def test_a_failing_window_never_kills_the_pump(self):
        calls = []

        def flaky(js):
            calls.append(js)
            if len(calls) == 2:
                raise RuntimeError("window gone")

        bus = UiBus(flaky)
        bus.start()
        bus.open_gate()
        for i in range(5):
            bus.push({"type": "log", "line": ["t", "•", str(i)]})
        self.assertTrue(wait_until(lambda: len(calls) == 5))
        bus.stop()
        self.assertEqual(len(bus._errors), 1)

    def test_stop_is_prompt_and_idempotent_when_never_started(self):
        bus = UiBus(FakeWindow().evaluate_js)
        t0 = time.time()
        bus.stop()
        self.assertLess(time.time() - t0, 0.5)


class TickerTests(unittest.TestCase):
    def test_ticks_repeatedly_survives_errors_and_stops(self):
        n = []

        def tick():
            n.append(1)
            if len(n) == 1:
                raise RuntimeError("boom")

        t = Ticker(tick, every=0.02)
        t.start()
        self.assertTrue(wait_until(lambda: len(n) >= 4))
        t.stop()
        count = len(n)
        time.sleep(0.1)
        self.assertEqual(len(n), count)


class ShellApiRules(unittest.TestCase):
    """Spike B rule 2: pywebview walks every PUBLIC attribute of the js_api object."""

    def bound(self):
        api = ShellApi()
        model = SessionModel({"listen_port": 1, "bridge_port": 2}, [])
        bus = UiBus(FakeWindow().evaluate_js)
        api._bind(model=model, bus=bus, window=FakeWindow(), quit_cb=lambda: None)
        return api

    def test_every_public_attribute_is_a_plain_method(self):
        api = self.bound()
        public = [n for n in dir(api) if not n.startswith("_")]
        self.assertTrue(public)
        for name in public:
            self.assertTrue(inspect.ismethod(getattr(api, name)), "%s is public and not a method -- pywebview would recurse into it" % name)

    def test_live_references_are_private(self):
        api = self.bound()
        for name in ("_model", "_bus", "_window", "_quit_cb"):
            self.assertIn(name, vars(api))
        self.assertEqual([n for n in vars(api) if not n.startswith("_")], [])

    def test_window_and_bridge_objects_are_not_reachable_through_public_names(self):
        api = self.bound()
        reachable = {id(getattr(api, n)) for n in dir(api) if not n.startswith("_")}
        for name in ("_model", "_bus", "_window"):
            self.assertNotIn(id(getattr(api, name)), reachable)

    def test_public_surface_is_exactly_the_documented_one(self):
        api = self.bound()
        self.assertEqual(
            sorted(n for n in dir(api) if not n.startswith("_")),
            sorted(["get_state", "log_text", "toggle_track", "select_all", "select_none",
                    "use_live_selection", "run_tool", "pick_file", "ping", "request_status", "request_tracks",
                    "reset_bridge", "place_answer", "confirm_answer", "genius_send", "genius_stop", "genius_clear", "genius_set_agent", "prefs", "pick_folder", "quit"]),
        )

    def test_get_state_opens_the_gate_and_drops_pre_snapshot_events(self):
        win = FakeWindow()
        api = ShellApi()
        bus = UiBus(win.evaluate_js)
        model = SessionModel({"listen_port": 1, "bridge_port": 2}, [], emit=bus.push)
        api._bind(model=model, bus=bus, window=win)
        bus.start()
        model.log("before snapshot")
        snap = api.get_state()
        self.assertEqual(snap["log"][-1][2], "before snapshot")     # ...it is in the snapshot,
        model.log("after snapshot")
        self.assertTrue(wait_until(lambda: len(win.events()) == 1))
        time.sleep(0.1)
        bus.stop()
        self.assertEqual([e["line"][2] for e in win.events()], ["after snapshot"])   # ...and delivered exactly once

    def test_state_and_events_carry_no_secrets(self):
        model = SessionModel({"api_key": "xai-SECRET", "listen_port": 1, "bridge_port": 2}, [])
        api = ShellApi()
        api._bind(model=model, bus=UiBus(FakeWindow().evaluate_js))
        self.assertNotIn("SECRET", json.dumps(api.get_state()))

    def test_pick_file_returns_empty_when_cancelled_or_windowless(self):
        api = self.bound()
        self.assertEqual(api.pick_file("", None), "")
        api._window.dialog_result = None
        self.assertEqual(api.pick_file("C:/x/y.wav", [["Audio", "*.wav"]]), "")
        api._window.dialog_result = ("C:/picked.wav",)
        self.assertEqual(api.pick_file("C:/x/y.wav", [["Audio", "*.wav"]]), "C:/picked.wav")
        blank = ShellApi()
        blank._bind(model=SessionModel({"listen_port": 1, "bridge_port": 2}, []), bus=UiBus(FakeWindow().evaluate_js))
        self.assertEqual(blank.pick_file("", None), "")

    def test_place_answer_reaches_the_pending_slot_question_and_refuses_a_stale_one(self):
        api = self.bound()
        self.assertTrue(api.place_answer(1, 0, False)["stale"])                      # nothing is pending
        box = {}
        slots = [{"index": 0, "n": 1, "has": True, "name": "Kick"}, {"index": 1, "n": 2, "has": False, "name": ""}]
        t = threading.Thread(target=lambda: box.update(slot=api._model.placement.ask("Tone", {"name": "Vox"}, slots)), daemon=True)
        t.start()
        self.assertTrue(wait_until(lambda: api._model.placement.snapshot() is not None))
        qid = api._model.placement.snapshot()["id"]
        self.assertTrue(api.place_answer(qid, 0)["needsConfirm"])                     # occupied: the second click is required
        self.assertEqual(api.place_answer(qid, 0, True), {"ok": True})
        t.join(2)
        self.assertEqual(box["slot"], 0)

    def test_confirm_answer_reaches_the_pending_approval_and_refuses_a_stale_one(self):
        api = self.bound()
        self.assertTrue(api.confirm_answer(1, True)["stale"])                        # nothing is pending
        box = {}
        detail = {"title": "Generate a TTS vocal?", "rows": [("Text", "Hello from the studio")]}
        t = threading.Thread(target=lambda: box.update(ok=api._model.confirm.ask("tts_spend", detail)), daemon=True)
        t.start()
        self.assertTrue(wait_until(lambda: api._model.confirm.snapshot() is not None))
        qid = api._model.confirm.snapshot()["id"]
        self.assertEqual(api.confirm_answer(qid, True, False), {"ok": True, "approved": True})
        t.join(2)
        self.assertTrue(box["ok"])
        self.assertFalse(api._model.confirm.suppressed("tts_spend"))                 # remember was not ticked

    def test_quit_runs_the_callback_off_the_calling_thread(self):
        seen = []
        api = ShellApi()
        api._bind(model=SessionModel({"listen_port": 1, "bridge_port": 2}, []), bus=UiBus(FakeWindow().evaluate_js),
                 quit_cb=lambda: seen.append(threading.current_thread().name))
        api.quit()
        self.assertTrue(wait_until(lambda: seen))
        self.assertNotEqual(seen[0], threading.current_thread().name)


class EndToEndOverUdp(unittest.TestCase):
    """SessionModel + real BridgeClient + UiBus against MockLive on loopback."""

    TOOLS = [
        {"id": "detect-key", "name": "Detect Key", "scope": "set", "fields": [{"id": "scope", "type": "text", "default": "clip"}]},
        {"id": "clip-namer", "name": "Clip Namer", "scope": "track", "fields": []},
    ]

    def setUp(self):
        self.mock = MockLive(listen_port=BRIDGE, reply_port=LISTEN).start()
        self.win = FakeWindow()
        self.bus = UiBus(self.win.evaluate_js)
        self.saved = []
        self.model = SessionModel({"listen_port": LISTEN, "bridge_port": BRIDGE, "tool_prefs": {}}, self.TOOLS,
                                  emit=self.bus.push, save_settings=self.saved.append)
        self.client = bridge_client.BridgeClient(LISTEN, BRIDGE, self.model.handle_osc)
        self.model.attach_bridge(self.client)
        self.api = ShellApi()
        self.api._bind(model=self.model, bus=self.bus, window=self.win)
        self.bus.start()
        self.client.start()
        self.api.get_state()                      # what the page does on load: snapshot + open the gate
        self.ticker = Ticker(self.model.tick, every=0.1)
        self.ticker.start()

    def tearDown(self):
        self.ticker.stop()
        self.client.close()
        self.bus.stop()
        self.mock.stop()

    def patches(self, key):
        return [e["patch"][key] for e in self.win.events() if e["type"] == "patch" and key in e["patch"]]

    def test_pip_goes_online_and_set_and_tracks_arrive_via_the_bus(self):
        self.assertTrue(wait_until(lambda: self.patches("connected") == [True]))
        self.assertTrue(wait_until(lambda: self.patches("set")))
        self.assertEqual(self.patches("set")[-1]["name"], "Neon Nights 128.als")
        self.assertTrue(wait_until(lambda: self.patches("tracks")))
        tracks = self.patches("tracks")[-1]
        self.assertEqual(len(tracks), 10)
        self.assertEqual(self.patches("targets")[-1], ["midi:1"])             # Bass was selected in Live
        self.assertIn("ui-bus-pusher", self.win.threads)
        self.assertEqual(self.win.threads, {"ui-bus-pusher"})

    def test_live_sel_and_run_send_only_ticked_tracks_and_result_comes_back(self):
        self.assertTrue(wait_until(lambda: self.model.snapshot()["tracks"]))
        self.api.select_none()
        self.api.toggle_track("midi:0")
        self.api.toggle_track("audio:4")
        self.assertEqual(self.api.run_tool("clip-namer", {"pattern": "x"})["ok"], True)
        self.assertTrue(wait_until(lambda: self.mock.runs))
        tool_id, payload = self.mock.runs[0]
        self.assertEqual(tool_id, "clip-namer")
        self.assertEqual([t["key"] for t in payload["tracks"]], ["midi:0", "audio:4"])
        self.assertEqual(payload["fields"], {"pattern": "x"})
        self.assertTrue(wait_until(lambda: any(r["clip-namer"]["state"] == "done" for r in self.patches("runs"))))
        self.api.use_live_selection()
        self.assertEqual(self.model.target_keys(), ["midi:1"])

    def test_a_tool_error_from_the_bridge_reaches_the_page_as_an_error(self):
        self.assertTrue(wait_until(lambda: self.model.snapshot()["tracks"]))
        self.mock.fail_runs = True
        self.api.run_tool("detect-key", {})
        self.assertTrue(wait_until(lambda: any(r.get("detect-key", {}).get("state") == "error" for r in self.patches("runs"))))

    def test_set_scope_run_works_with_nothing_ticked(self):
        self.assertTrue(wait_until(lambda: self.model.snapshot()["tracks"]))
        self.api.select_none()
        self.assertTrue(self.api.run_tool("detect-key", {"scope": "set"})["ok"])
        self.assertTrue(wait_until(lambda: self.mock.runs and self.mock.runs[0][1]["tracks"] == []))

    def test_silent_bridge_flips_offline_and_a_run_then_warns(self):
        with mock.patch.object(shell_model, "OFFLINE_AFTER_S", 0.4):
            self.assertTrue(wait_until(lambda: self.patches("connected") == [True]))
            self.mock.muted = True
            self.assertTrue(wait_until(lambda: self.patches("connected")[-1:] == [False], timeout=3))
        self.assertFalse(self.api.run_tool("detect-key", {})["ok"])
        self.mock.muted = False
        self.assertTrue(wait_until(lambda: self.patches("connected")[-1:] == [True]))      # recovers by itself

    def test_a_run_the_bridge_never_answers_ends_with_a_warning_not_a_hang(self):
        self.assertTrue(wait_until(lambda: self.model.snapshot()["tracks"]))
        self.mock.silent_runs = True
        with mock.patch.object(shell_model, "RESULT_WAIT_S", 0.2):
            self.api.run_tool("detect-key", {})
            self.assertTrue(wait_until(lambda: any(r.get("detect-key", {}).get("state") == "error" for r in self.patches("runs")), timeout=3))

    def test_reset_bridge_rebuilds_the_socket_and_the_device_hears_it(self):
        self.assertTrue(wait_until(lambda: self.patches("connected") == [True]))
        self.assertTrue(self.api.reset_bridge()["ok"])
        self.assertTrue(wait_until(lambda: self.mock.resets == 1))
        # the rebuilt listener still receives: a fresh sync must produce a new tracks patch
        before = len(self.patches("tracks"))
        self.api.request_tracks()
        self.assertTrue(wait_until(lambda: len(self.patches("tracks")) > before))

    def test_malformed_datagram_is_reported_in_the_log_and_the_link_survives(self):
        import socket
        raw = bridge_client.osc_string("/live-actions/reply") + bridge_client.osc_string(",i") + b"\x00\x01"
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(raw, (bridge_client.BRIDGE_HOST, LISTEN))
        s.close()
        self.assertTrue(wait_until(lambda: any("Bridge transport" in e["line"][2] for e in self.win.events() if e["type"] == "log")))
        before = len(self.patches("tracks"))
        self.api.request_tracks()
        self.assertTrue(wait_until(lambda: len(self.patches("tracks")) > before))


if __name__ == "__main__":
    unittest.main()
