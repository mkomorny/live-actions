"""Tests for shell_dialog_tools.DialogTools -- Song Mapper and Fill Forge inside the shell.

Real tool manifests and the real, untouched dialog HTML; a fake window host (the "user" presses Insert by
calling the handler the host was given), a scripted fake bridge, and a scripted `confirm`. Workers run
inline (`spawn=lambda fn: fn()`) so every assertion is deterministic.

Run from app\\:  python -m unittest test_shell_dialog_tools
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import shell_dialogs
import shell_dialog_tools
import tool_manifests
from test_shell_model import FakeBridge, go_online, make, tracks_json

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
TOOLS = tool_manifests.load_tools(TOOLS_DIR)


class ScriptedBridge(FakeBridge):
    """`call_live(action, params)` answers from a script: {action: reply | callable(params)}."""

    def __init__(self, script=None):
        super().__init__()
        self.script = script or {}
        self.calls: list[tuple[str, dict]] = []

    def call_live(self, action, params=None, timeout=6.0):
        self.calls.append((action, params or {}))
        reply = self.script.get(action, {"ok": False, "error": "not scripted"})
        return reply(params) if callable(reply) else reply


class FakeHost:
    """Stands in for shell_dialogs.DialogHost: remembers what was opened and lets a test answer it."""

    def __init__(self):
        self.opened: list[tuple[str, str, str]] = []
        self.handlers: dict[str, object] = {}
        self.raised: list[str] = []
        self.closed_all = 0

    def is_open(self, tool_id=None):
        return bool(self.handlers) if tool_id is None else tool_id in self.handlers

    def open(self, tool_id, title, html, on_result):
        if tool_id in self.handlers:
            self.raised.append(tool_id)
            return "raised"
        self.opened.append((tool_id, title, html))
        self.handlers[tool_id] = on_result
        return "opened"

    def close_all(self):
        self.closed_all += 1

    def answer(self, tool_id, payload):
        """The dialog sends `payload` (already unwrapped from close_and_send) and closes."""
        self.handlers.pop(tool_id)(payload)


class Rig:
    def __init__(self, bridge_script=None, answers=None, settings=None):
        self.confirms: list[tuple[str, str]] = []
        self._answers = list(answers if answers is not None else [True] * 4)
        self.m, self.sent, self.events, _ = make(TOOLS, settings=settings)
        self.bridge = ScriptedBridge(bridge_script)
        self.m._bridge = self.bridge
        self.host = FakeHost()
        self.m.attach_dialogs(self.host, self._confirm, spawn=lambda fn: fn())
        go_online(self.m)
        self.m.handle_osc("/live-actions/status", [json.dumps({"ok": True, "name": "S", "tempo": 120.0, "time_signature": "3/4", "tracks": 4})])

    def _confirm(self, title, message):
        self.confirms.append((title, message))
        return self._answers.pop(0) if self._answers else False

    def run(self, tool_id):
        return self.m.run_tool(tool_id, {})

    def set_targets(self, keys):
        self.m._targets = set(keys)

    def state(self, tool_id):
        return self.m.snapshot()["runs"].get(tool_id, {})

    def runs_sent(self):
        return [s for s in self.sent if s[0] == "/live-actions/run"]

    def sent_payload(self, i=-1):
        s = self.runs_sent()[i]
        return s[1], json.loads(s[2])

    def html(self, tool_id):
        return [h for t, _n, h in self.host.opened if t == tool_id][-1]      # the most recent open

    def ctx(self, tool_id):
        html = self.html(tool_id)
        start = html.index("window.__CTX__ = ") + len("window.__CTX__ = ")
        return json.JSONDecoder().raw_decode(html, start)[0]


class OpeningTests(unittest.TestCase):
    def test_opening_loads_the_dialog_html_unchanged_except_the_context(self):
        r = Rig()
        res = r.run("fill-forge")
        self.assertTrue(res["ok"])
        original = (TOOLS_DIR / "fill-forge" / "ui" / "dialog.html").read_text(encoding="utf-8")
        ctx = r.ctx("fill-forge")
        self.assertEqual(r.html("fill-forge"), original.replace("__CTX_JSON__", shell_dialogs.embed_json(ctx)))
        self.assertNotIn("__CTX_JSON__", r.html("fill-forge"))
        self.assertEqual(r.host.opened[0][1], "Fill Forge")            # native window title = the tool's name

    def test_status_text_is_the_manifests_own(self):
        r = Rig()
        r.run("fill-forge")
        self.assertEqual(r.state("fill-forge")["state"], "running")
        self.assertIn("Audition writes nothing", r.state("fill-forge")["message"])

    def test_breakdowns_context_matches_the_tk_builder(self):
        r = Rig()
        r.run("fill-forge")
        c = r.ctx("fill-forge")
        self.assertEqual((c["source"], c["hasClip"], c["clipName"], c["beatsPerBar"], c["tempo"]), ("MidiTrack", True, "T1", 3, 120.0))
        self.assertEqual(c["spec"]["beatsPerBar"], 3)
        self.assertEqual(c["availableTargets"], ["newClip", "replace", "append", "newTrack", "playhead"])
        self.assertEqual(c["noteCount"], 0)

    def test_breakdowns_with_nothing_ticked_says_so_in_the_context(self):
        r = Rig()
        r.set_targets([])
        r.run("fill-forge")
        c = r.ctx("fill-forge")
        self.assertEqual((c["hasClip"], c["clipName"]), (False, "tick a MIDI track"))

    def test_a_track_named_like_a_script_end_tag_cannot_break_the_page(self):
        r = Rig()
        tracks = json.loads(tracks_json())
        tracks["tracks"][1]["name"] = "</script><img src=x onerror=alert(1)>"
        r.m.handle_osc("/live-actions/tracks", [json.dumps(tracks)])
        r.run("fill-forge")
        original = (TOOLS_DIR / "fill-forge" / "ui" / "dialog.html").read_text(encoding="utf-8")
        self.assertEqual(r.html("fill-forge").count("</script>"), original.count("</script>"))
        self.assertEqual(r.ctx("fill-forge")["clipName"], "</script><img src=x onerror=alert(1)>")   # value intact

    def test_opening_twice_raises_the_open_dialog_instead_of_opening_another(self):
        r = Rig()
        r.run("fill-forge")
        res = r.run("fill-forge")
        self.assertTrue(res["ok"])
        self.assertIn("already open", res["message"])
        self.assertEqual(len(r.host.opened), 1)
        self.assertEqual(r.host.raised, ["fill-forge"])

    def test_no_dialog_host_is_an_error_not_a_silent_no_op(self):
        m, *_ = make(TOOLS)
        go_online(m)
        self.assertFalse(m.run_tool("fill-forge", {})["ok"])

    def test_a_missing_dialog_file_is_reported(self):
        tool = dict(next(t for t in TOOLS if t["id"] == "fill-forge"), _path=tempfile.gettempdir(), dialog="nope.html")
        r = Rig()
        r.m._tools = [tool]
        r.run("fill-forge")
        self.assertEqual(r.state("fill-forge")["state"], "error")
        self.assertIn("Could not open", r.state("fill-forge")["message"])

    def test_closing_the_dialog_writes_nothing_and_frees_the_button(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", None)
        self.assertEqual(r.state("fill-forge")["state"], "idle")
        self.assertIn("nothing was written", r.state("fill-forge")["message"])
        self.assertEqual(r.runs_sent(), [])

    def test_close_dialogs_reaches_the_host(self):
        r = Rig()
        r.m.close_dialogs()
        self.assertEqual(r.host.closed_all, 1)

    def test_a_dialog_cancelled_by_shutdown_emits_nothing_into_the_closing_window(self):
        r = Rig()
        r.run("fill-forge")
        r.m.close_dialogs()
        before = len(r.events)
        r.host.answer("fill-forge", None)               # what DialogHost.close_all delivers
        self.assertEqual(len(r.events), before)
        self.assertEqual(r.state("fill-forge")["state"], "running")


class BreakdownsRunTests(unittest.TestCase):
    NOTES = [{"pitch": 36, "startTime": 0, "duration": 0.25, "velocity": 100}]

    def test_insert_sends_the_run_to_the_bridge_and_reports_its_result(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", {"notes": self.NOTES, "target": "append", "lengthBeats": 8, "name": "Fill A"})
        tool_id, payload = r.sent_payload()
        self.assertEqual(tool_id, "fill-forge")
        self.assertEqual(payload["fields"], {"target": "append", "lengthBeats": 8, "name": "Fill A", "notes": self.NOTES})
        self.assertEqual([t["key"] for t in payload["tracks"]], ["midi:1"])
        self.assertEqual(r.state("fill-forge")["state"], "running")
        r.m.handle_osc("/live-actions/result", ["ok", "1 clip"])
        self.assertEqual(r.state("fill-forge")["state"], "done")

    def test_defaults_match_tk(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", {"notes": self.NOTES})
        self.assertEqual(r.sent_payload()[1]["fields"], {"target": "newClip", "lengthBeats": 4, "name": "Fill Forge", "notes": self.NOTES})

    def test_json_string_payload_is_accepted(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", json.dumps({"notes": self.NOTES}))
        self.assertEqual(len(r.runs_sent()), 1)

    def test_no_notes_or_no_track_refuses_without_sending(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", {"notes": []})
        self.assertEqual(r.state("fill-forge")["state"], "error")
        self.assertIn("No notes", r.state("fill-forge")["message"])
        r.run("fill-forge")
        r.set_targets([])
        r.host.answer("fill-forge", {"notes": self.NOTES})
        self.assertIn("Select at least one track", r.state("fill-forge")["message"])
        self.assertEqual(r.runs_sent(), [])

    def test_invalid_payload_is_an_error_not_a_crash(self):
        r = Rig()
        r.run("fill-forge")
        r.host.answer("fill-forge", "{not json")
        self.assertEqual(r.state("fill-forge")["state"], "error")

    def test_a_handler_bug_never_leaves_the_tool_running(self):
        r = Rig()
        r.run("fill-forge")
        with mock.patch.object(r.m, "_dispatch_run", side_effect=RuntimeError("boom")):
            r.host.answer("fill-forge", {"notes": self.NOTES})
        self.assertEqual(r.state("fill-forge")["state"], "error")
        self.assertIn("boom", r.state("fill-forge")["message"])


class ArrangementHelperTests(unittest.TestCase):
    SCAN = {"ok": True, "isEditing": True, "sections": [{"id": 1, "name": "Intro"}], "scanCount": 3, "nextId": 4, "startBar": 9, "truncated": True}

    def rig(self, script=None, **kw):
        base = {"arrangement_scan": self.SCAN}
        base.update(script or {})
        return Rig(bridge_script=base, **kw)

    def test_offline_refuses_before_any_window(self):
        r = Rig()
        r.m._connected = False
        self.assertFalse(r.run("song-mapper")["ok"])
        self.assertEqual((r.host.opened, r.state("song-mapper")["state"]), ([], "error"))

    def test_scans_the_default_track_first_and_seeds_the_dialog_with_the_reply(self):
        r = self.rig()
        r.run("song-mapper")
        self.assertEqual(r.bridge.calls[0], ("arrangement_scan", {"trackPath": "live_set tracks 1"}))   # first ticked MIDI track
        c = r.ctx("song-mapper")
        self.assertEqual((c["isEditing"], c["scanCount"], c["nextId"], c["startBar"], c["truncated"]), (True, 3, 4, 9, True))
        self.assertEqual(c["sections"], [{"id": 1, "name": "Intro"}])
        self.assertEqual(c["lastSectionTrackPath"], "live_set tracks 1")
        self.assertEqual([t["ticked"] for t in c["tracks"]], [False, True, False, False])
        self.assertEqual((c["beatsPerBar"], c["tempo"]), (3, 120.0))

    def test_a_failed_scan_opens_in_create_mode(self):
        r = self.rig({"arrangement_scan": {"ok": False, "error": "nope"}})
        r.run("song-mapper")
        c = r.ctx("song-mapper")
        self.assertEqual((c["isEditing"], c["sections"], c["scanCount"]), (False, [], 0))
        self.assertTrue(any("scan failed" in l[2] for l in r.m.snapshot()["log"]))

    def test_the_scan_is_consumed_by_one_open_only(self):
        r = self.rig()
        r.run("song-mapper")
        r.host.answer("song-mapper", None)
        r.bridge.script["arrangement_scan"] = {"ok": False, "error": "gone"}
        r.run("song-mapper")
        self.assertFalse(r.ctx("song-mapper")["isEditing"])          # not the cached edit-mode data

    def test_default_track_rule_matches_the_dialog(self):
        pick = shell_dialog_tools.DialogTools._default_section_track
        tr = lambda *rows: {"tracks": [{"path": p, "name": n, "kind": k, "ticked": t} for p, n, k, t in rows]}
        self.assertEqual(pick(tr(("a", "Lead", "midi", True), ("b", "Arrangement", "midi", False))), "b")          # named beats ticked
        self.assertEqual(pick(dict(tr(("a", "Lead", "midi", True), ("b", "Bass", "midi", False)), lastSectionTrackPath="b")), "b")   # last wins
        self.assertEqual(pick(dict(tr(("a", "Lead", "midi", True)), lastSectionTrackPath="gone")), "a")
        self.assertEqual(pick(tr(("a", "Lead", "midi", False), ("b", "Bass", "midi", False))), "a")               # first MIDI
        self.assertEqual(pick(tr(("a", "Vox", "audio", True))), "")                                                # no MIDI track

    def request(self, **kw):
        return dict({"sectionTrackPath": "live_set tracks 1", "sections": [{"name": "A", "bars": 8}], "createLocators": True,
                     "remapAllTracks": False, "renameTrack": False, "scanCount": 3, "isEditing": True}, **kw)

    PLAN = {"ok": True, "writeCount": 12, "moved": 2, "sectionCount": 5, "undoStepCount": 14, "fingerprint": {"h": "abc"}, "remapTrackCount": 6}

    def test_plan_confirm_execute(self):
        r = self.rig({"arrangement_plan": self.PLAN})
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        call, params = r.bridge.calls[-1]
        self.assertEqual(call, "arrangement_plan")
        self.assertEqual((params["beatsPerBar"], params["tickedTrackPaths"], params["isEditing"]), (3, [], True))   # ticked = only the section track itself, excluded
        self.assertEqual(len(r.confirms), 1)
        self.assertIn("creates 5 section clip(s) and moves 2 existing clip(s)", r.confirms[0][1])
        self.assertIn("14 individual undo step(s)", r.confirms[0][1])
        tool_id, payload = r.sent_payload()
        self.assertEqual(tool_id, "song-mapper")
        self.assertEqual(payload["fields"]["fingerprint"], {"h": "abc"})
        self.assertEqual(payload["fields"]["sectionTrackPath"], "live_set tracks 1")
        self.assertEqual(r.state("song-mapper")["state"], "running")
        r.m.handle_osc("/live-actions/result", ["ok", "5 sections"])
        self.assertEqual(r.state("song-mapper")["state"], "done")

    def test_the_section_track_choice_is_remembered_for_next_time(self):
        saved = []
        r = self.rig({"arrangement_plan": self.PLAN}, settings={"tool_prefs": {}, "listen_port": 1, "bridge_port": 2})
        r.m._save_settings = lambda s: saved.append(json.loads(json.dumps(s)))
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request(sectionTrackPath="live_set tracks 0")))
        self.assertEqual(saved[-1]["tool_prefs"]["song-mapper"], {"sectionTrackPath": "live_set tracks 0"})

    def test_other_ticked_tracks_are_sent_as_targets(self):
        r = self.rig({"arrangement_plan": self.PLAN})
        r.set_targets(["midi:0", "midi:1", "audio:2"])
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertEqual(sorted(r.bridge.calls[-1][1]["tickedTrackPaths"]), ["live_set tracks 0", "live_set tracks 2"])

    def test_declining_writes_nothing(self):
        r = self.rig({"arrangement_plan": self.PLAN}, answers=[False])
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertEqual(r.runs_sent(), [])
        self.assertEqual(r.state("song-mapper")["state"], "idle")

    def test_whole_project_needs_a_second_yes(self):
        r = self.rig({"arrangement_plan": self.PLAN}, answers=[True, False])
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request(remapAllTracks=True)))
        self.assertEqual([c[0] for c in r.confirms], ["Song Mapper — Confirm", "Song Mapper — Whole Project"])
        self.assertIn("all 6 eligible track(s)", r.confirms[1][1])
        self.assertEqual(r.runs_sent(), [])
        r2 = self.rig({"arrangement_plan": self.PLAN}, answers=[True, True])
        r2.run("song-mapper")
        r2.host.answer("song-mapper", json.dumps(self.request(remapAllTracks=True)))
        self.assertEqual(len(r2.runs_sent()), 1)

    def test_over_the_safety_cap_is_refused_before_any_confirm(self):
        r = self.rig({"arrangement_plan": dict(self.PLAN, writeCount=shell_dialog_tools.AH_CAP + 1)})
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertEqual((r.confirms, r.runs_sent()), ([], []))
        self.assertIn("safety cap", r.state("song-mapper")["message"])
        self.assertEqual(r.state("song-mapper")["state"], "error")

    def test_at_the_cap_is_allowed(self):
        r = self.rig({"arrangement_plan": dict(self.PLAN, writeCount=shell_dialog_tools.AH_CAP)})
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertEqual(len(r.runs_sent()), 1)

    def test_a_refused_plan_is_shown(self):
        r = self.rig({"arrangement_plan": {"ok": False, "message": "overlapping sections"}})
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertIn("overlapping sections", r.state("song-mapper")["message"])
        self.assertEqual((r.confirms, r.runs_sent()), ([], []))

    def test_no_section_track_means_nothing_to_plan(self):
        r = self.rig()
        r.run("song-mapper")
        r.host.answer("song-mapper", json.dumps(self.request(sectionTrackPath="")))
        self.assertEqual(r.state("song-mapper")["state"], "idle")
        self.assertEqual([c for c in r.bridge.calls if c[0] == "arrangement_plan"], [])

    def test_the_result_wait_is_the_long_one(self):
        r = self.rig({"arrangement_plan": self.PLAN})
        r.run("song-mapper")
        with mock.patch("threading.Timer") as timer:
            r.host.answer("song-mapper", json.dumps(self.request()))
        self.assertEqual(timer.call_args.args[0], shell_dialog_tools.AH_WAIT_S)


if __name__ == "__main__":
    unittest.main()
