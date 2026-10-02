"""Tests for shell_placement (host-tool "Add to Live Set" / "Save to PC") and its wiring in the session model.

Fakes only: a scripted bridge, a recording emit, temp files. The modal itself is the page's job (e2e_shell drives it).

Run from app\\:  python -m unittest test_shell_placement
"""

from __future__ import annotations

import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import host_tools
import shell_placement as sp
from shell_placement import SlotPicker, offer_save_as, place_generated_file, save_dialog_args, slot_view
from test_shell_model import go_online, make


def wait_until(fn, timeout=3.0, what="condition"):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(0.01)
    raise AssertionError("timed out waiting for " + what)


class ScriptedLive:
    """call_live(action, params) -> canned reply; records every call."""

    def __init__(self, **replies) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.replies = replies

    def __call__(self, action, params):
        self.calls.append((action, params))
        r = self.replies.get(action, {"ok": True})
        return r(params) if callable(r) else r


SLOTS = [
    {"index": 0, "has_clip": True, "clip": {"name": "Kick loop"}},
    {"index": 1, "has_clip": False},
    {"index": 2, "has_clip": True, "clip": {}},
    {"index": 3, "has_clip": False},
]
VOX = {"key": "audio:4", "index": 4, "name": "Vox", "kind": "audio"}
DRUMS = {"key": "midi:0", "index": 0, "name": "Drums", "kind": "midi"}


def result(path="C:/out/tone.wav"):
    return {"ok": True, "message": "Tone made.", "path": path}


class PlaceGeneratedFileTests(unittest.TestCase):
    def place(self, res=None, targets=None, connected=True, live=None, choose=1):
        asked = []

        def ask(track, slots):
            asked.append((track, slots))
            return choose

        live = live or ScriptedLive(read_track={"ok": True, "session_clips": SLOTS})
        out = place_generated_file(res if res is not None else result(), [VOX] if targets is None else targets, connected, live, ask)
        return out, live, asked

    def test_a_result_without_a_file_is_untouched(self):
        out, live, asked = self.place(res={"ok": True, "message": "x"})
        self.assertEqual(out, {"ok": True, "message": "x"})
        self.assertEqual(live.calls, [])

    def test_offline_says_the_file_was_saved_and_asks_nothing(self):
        out, live, asked = self.place(connected=False)
        self.assertEqual(out["message"], "Tone made. Bridge offline — file saved, not placed in Live.")
        self.assertIs(out["placed"], False)
        self.assertEqual((live.calls, asked), ([], []))

    def test_no_ticked_audio_track(self):
        out, live, asked = self.place(targets=[DRUMS])
        self.assertIn("No ticked audio track", out["message"])
        self.assertEqual((live.calls, asked), ([], []))

    def test_unreadable_slots(self):
        out, live, asked = self.place(live=ScriptedLive(read_track={"ok": False, "error": "boom"}))
        self.assertEqual(out["message"], "Tone made. Could not read clip slots: boom")
        self.assertEqual(asked, [])

    def test_track_without_slots(self):
        out, live, asked = self.place(live=ScriptedLive(read_track={"ok": True, "session_clips": []}))
        self.assertIn("Track has no clip slots", out["message"])
        self.assertEqual(asked, [])

    def test_skipping_creates_nothing(self):
        out, live, asked = self.place(choose=None)
        self.assertEqual(out["message"], "Tone made. Placement skipped.")
        self.assertIs(out["placed"], False)
        self.assertEqual([a for a, _ in live.calls], ["read_track"])

    def test_the_question_gets_the_track_and_every_slot(self):
        out, live, asked = self.place()
        track, slots = asked[0]
        self.assertEqual(track["name"], "Vox")
        self.assertEqual(slots, [
            {"index": 0, "n": 1, "has": True, "name": "Kick loop"},
            {"index": 1, "n": 2, "has": False, "name": ""},
            {"index": 2, "n": 3, "has": True, "name": ""},
            {"index": 3, "n": 4, "has": False, "name": ""},
        ])

    def test_placing_sends_track_slot_and_file(self):
        out, live, asked = self.place(choose=3)
        self.assertEqual(live.calls[0], ("read_track", {"track_index": 4}))
        self.assertEqual(live.calls[1], ("create_clip", {"track_index": 4, "slot_index": 3, "sample_file": "C:/out/tone.wav"}))
        self.assertEqual(out["message"], "Tone made. Placed on Vox (slot 4).")
        self.assertIs(out["placed"], True)

    def test_a_failed_create_is_reported(self):
        out, live, _ = self.place(live=ScriptedLive(read_track={"ok": True, "session_clips": SLOTS}, create_clip={"ok": False, "error": "nope"}))
        self.assertEqual(out["message"], "Tone made. Placement failed: nope")
        self.assertIs(out["placed"], False)

    def test_the_first_audio_target_is_used_even_if_a_midi_track_is_ticked_first(self):
        other = dict(VOX, key="audio:5", index=5, name="Guitar DI")
        out, live, asked = self.place(targets=[DRUMS, VOX, other])
        self.assertEqual(asked[0][0]["name"], "Vox")
        self.assertEqual(live.calls[0][1], {"track_index": 4})

    def test_slot_entries_without_an_index_are_ignored(self):
        live = ScriptedLive(read_track={"ok": True, "session_clips": [{"has_clip": False}, {"index": 0, "has_clip": False}]})
        out, live, asked = self.place(live=live)
        self.assertEqual([s["index"] for s in asked[0][1]], [0])

    def test_slot_view_labels(self):
        self.assertEqual(slot_view({"index": 7, "has_clip": True, "clip": {"name": "Pad"}}), {"index": 7, "n": 8, "has": True, "name": "Pad"})
        self.assertEqual(slot_view({"index": 0, "has_clip": False, "clip": {"name": "stale"}})["name"], "")


class SlotPickerTests(unittest.TestCase):
    def setUp(self):
        self.patches: list[dict] = []
        self.picker = SlotPicker(threading.RLock(), lambda **kw: self.patches.append(kw))
        self.box: dict = {}
        self.threads: list[threading.Thread] = []

    def tearDown(self):
        self.picker.cancel(quiet=True)
        for t in self.threads:
            t.join(2)

    def ask(self, key="r", slots=None):
        def run():
            self.box[key] = self.picker.ask("Tone", VOX, slots or [slot_view(s) for s in SLOTS])

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.threads.append(t)
        wait_until(lambda: self.picker.snapshot() is not None, what="the question")
        return self.picker.snapshot()

    def test_the_question_is_pushed_and_in_the_snapshot(self):
        view = self.ask()
        self.assertEqual(self.patches[-1], {"placement": view})
        self.assertEqual((view["tool"], view["track"], len(view["slots"])), ("Tone", "Vox", 4))

    def test_an_answer_wakes_the_worker_and_clears_the_question(self):
        view = self.ask()
        self.assertEqual(self.picker.answer(view["id"], 1), {"ok": True})
        self.threads[0].join(2)
        self.assertEqual(self.box["r"], 1)
        self.assertIsNone(self.picker.snapshot())
        self.assertEqual(self.patches[-1], {"placement": None})

    def test_an_occupied_slot_needs_a_second_confirmed_answer(self):
        view = self.ask()
        r = self.picker.answer(view["id"], 0, False)
        self.assertEqual((r["ok"], r["needsConfirm"]), (False, True))
        self.assertIn("click Place again", r["message"])
        self.assertIsNotNone(self.picker.snapshot())               # still open: nothing was chosen
        self.assertNotIn("r", self.box)
        self.assertEqual(self.picker.answer(view["id"], 0, True), {"ok": True})
        self.threads[0].join(2)
        self.assertEqual(self.box["r"], 0)

    def test_an_empty_slot_needs_no_confirmation(self):
        view = self.ask()
        self.assertTrue(self.picker.answer(view["id"], 3, False)["ok"])

    def test_slots_that_were_not_offered_are_refused(self):
        view = self.ask()
        for bad in (99, -1, True, "1", 1.0, [1]):
            r = self.picker.answer(view["id"], bad, True)
            self.assertFalse(r["ok"], repr(bad))
        self.assertIsNotNone(self.picker.snapshot())

    def test_a_stale_or_wrong_id_is_refused(self):
        view = self.ask()
        self.assertTrue(self.picker.answer(view["id"] + 1, 1)["stale"])
        self.assertIsNotNone(self.picker.snapshot())
        self.picker.answer(view["id"], 1)
        self.threads[0].join(2)
        self.assertTrue(self.picker.answer(view["id"], 3)["stale"])             # already answered

    def test_cancel_answers_none(self):
        view = self.ask()
        self.assertEqual(self.picker.answer(view["id"], None), {"ok": True, "cancelled": True})
        self.threads[0].join(2)
        self.assertIsNone(self.box["r"])

    def test_quiet_cancel_wakes_the_worker_without_pushing(self):
        self.ask()
        before = len(self.patches)
        self.picker.cancel(quiet=True)
        self.threads[0].join(2)
        self.assertIsNone(self.box["r"])
        self.assertEqual(len(self.patches), before)

    def test_ids_increase_per_question(self):
        first = self.ask("a")
        self.picker.answer(first["id"], 1)
        self.threads[0].join(2)
        second = self.ask("b")
        self.assertGreater(second["id"], first["id"])

    def test_a_second_question_releases_the_first_worker(self):
        self.ask("a")
        second = self.ask_second()
        self.threads[0].join(2)
        self.assertIsNone(self.box["a"])
        self.picker.answer(second["id"], 3)

    def ask_second(self):
        first_id = self.picker.snapshot()["id"]

        def run():
            self.box["b"] = self.picker.ask("Tone", VOX, [slot_view(s) for s in SLOTS])

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.threads.append(t)
        wait_until(lambda: (self.picker.snapshot() or {}).get("id", first_id) != first_id, what="the second question")
        return self.picker.snapshot()


class SaveAsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="la-saveas-"))
        self.src = self.tmp / "tone.wav"
        self.src.write_bytes(b"RIFFdata")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def offer(self, picked, copy=shutil.copyfile):
        seen = {}

        def pick(**kw):
            seen.update(kw)
            return picked

        return offer_save_as(str(self.src), "TTS Vocal", pick, copy), seen

    def test_dialog_starts_in_the_files_folder_with_its_name_and_type(self):
        args = save_dialog_args(str(self.src), "TTS Vocal")
        self.assertEqual(args["title"], "Save TTS Vocal As")
        self.assertEqual((args["directory"], args["filename"]), (str(self.tmp), "tone.wav"))
        self.assertEqual(args["file_types"], ("WAV audio (*.wav)", "All files (*.*)"))

    def test_unknown_types_get_a_generic_label_and_every_filter_is_valid_for_pywebview(self):
        try:
            from webview.util import parse_file_type
        except ImportError:
            self.skipTest("pywebview not installed")
        for name in ("a.wav", "a.aif", "a.aiff", "a.mp3", "a.flac", "a.ogg", "a.xyz", "noext"):
            for spec in save_dialog_args(name)["file_types"]:
                parse_file_type(spec)                                   # raises ValueError on a bad filter
        self.assertEqual(save_dialog_args("a.xyz")["file_types"][0], "XYZ file (*.xyz)")
        self.assertEqual(save_dialog_args("a.ogg")["file_types"][0], "Ogg Vorbis (*.ogg)")

    def test_pick_receives_the_dialog_arguments(self):
        _, seen = self.offer("")
        self.assertEqual(set(seen), {"title", "directory", "filename", "file_types"})

    def test_cancel_copies_nothing(self):
        copy = mock.Mock()
        res, _ = self.offer("", copy)
        self.assertEqual(res["status"], "cancelled")
        copy.assert_not_called()

    def test_a_new_location_gets_a_copy(self):
        dest = self.tmp / "sub" / "kept.wav"
        dest.parent.mkdir()
        res, _ = self.offer(str(dest))
        self.assertEqual((res["status"], res["dest"]), ("saved", str(dest)))
        self.assertEqual(dest.read_bytes(), b"RIFFdata")
        self.assertTrue(self.src.exists())                              # a copy, not a move

    def test_saving_over_itself_does_not_copy(self):
        copy = mock.Mock()
        res, _ = self.offer(str(self.src), copy)
        self.assertEqual(res["status"], "same")
        copy.assert_not_called()

    def test_a_name_typed_without_an_extension_gets_the_files(self):
        res, _ = self.offer(str(self.tmp / "renamed"))
        self.assertEqual(Path(res["dest"]).name, "renamed.wav")
        self.assertTrue((self.tmp / "renamed.wav").exists())

    def test_a_failed_copy_is_reported_not_raised(self):
        def boom(a, b):
            raise PermissionError("denied")

        res, _ = self.offer(str(self.tmp / "x.wav"), boom)
        self.assertEqual(res["status"], "error")
        self.assertIn("denied", res["error"])


# ── the model's wiring ────────────────────────────────────────────────────────

TOOLS = [{"id": "hosty", "name": "Hosty", "runtime": "host", "fields": [
    {"id": "destination", "type": "select", "options": ["Leave in output folder", "Save to PC", "Add to Live Set"], "default": "Leave in output folder"}]}]


class HostWiringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="la-host-"))
        self.out = self.tmp / "tone.wav"
        self.out.write_bytes(b"RIFFdata")
        self.handler_calls = 0

        def handler(fields, settings):
            self.handler_calls += 1
            return {"ok": True, "message": "Tone made.", "path": str(self.out)}

        self.patcher = mock.patch.dict(host_tools.HOST_TOOLS, {"hosty": handler})
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def model(self, online=True, tick_audio=True):
        m, sent, events, _ = make(TOOLS)
        self.live = ScriptedLive(read_track={"ok": True, "session_clips": SLOTS})
        m._bridge = mock.Mock(call_live=self.live)
        if online:
            go_online(m)
        if tick_audio:
            m.set_all(False)
            m.toggle_track("audio:2")
        return m, events

    def run_state(self, m):
        return m.snapshot()["runs"]["hosty"]

    def finished(self, m):
        wait_until(lambda: self.run_state(m)["state"] in ("done", "error") and not m._host_running, what="run to finish")
        return self.run_state(m)

    def log_text(self, m):
        return m.log_text()

    # -- Add to Live Set
    def test_add_to_live_set_waits_for_the_page_then_places(self):
        m, events = self.model()
        self.assertTrue(m.run_tool("hosty", {"destination": "Add to Live Set"})["ok"])
        wait_until(lambda: m.placement.snapshot() is not None, what="the slot question")
        q = m.snapshot()["placement"]
        self.assertEqual((q["tool"], q["track"]), ("Hosty", "T2"))          # go_online's third track is the audio one
        self.assertEqual(self.run_state(m)["state"], "running")
        self.assertIn("choose a clip slot on “T2”", self.run_state(m)["message"])
        self.assertTrue(m.placement.answer(q["id"], 3)["ok"])
        run = self.finished(m)
        self.assertEqual(run["state"], "done")
        self.assertIn("Placed on T2 (slot 4).", run["message"])
        self.assertIn(("create_clip", {"track_index": 2, "slot_index": 3, "sample_file": str(self.out)}), self.live.calls)
        self.assertIsNone(m.snapshot()["placement"])

    def test_skipping_leaves_a_done_run_that_says_so(self):
        m, _ = self.model()
        m.run_tool("hosty", {"destination": "Add to Live Set"})
        wait_until(lambda: m.placement.snapshot() is not None)
        m.placement.answer(m.placement.snapshot()["id"], None)
        run = self.finished(m)
        self.assertEqual(run["state"], "done")
        self.assertIn("Placement skipped.", run["message"])
        self.assertNotIn("create_clip", [a for a, _ in self.live.calls])

    def test_offline_never_asks(self):
        m, _ = self.model(online=False, tick_audio=False)
        m.run_tool("hosty", {"destination": "Add to Live Set"})
        run = self.finished(m)
        self.assertIn("Bridge offline — file saved, not placed in Live.", run["message"])
        self.assertIsNone(m.placement.snapshot())

    def test_no_audio_track_ticked_never_asks(self):
        m, _ = self.model()
        m.set_all(False)
        m.toggle_track("midi:0")
        m.run_tool("hosty", {"destination": "Add to Live Set"})
        self.assertIn("No ticked audio track", self.finished(m)["message"])

    def test_quitting_with_the_question_open_ends_the_worker_quietly(self):
        m, events = self.model()
        m.run_tool("hosty", {"destination": "Add to Live Set"})
        wait_until(lambda: m.placement.snapshot() is not None)
        seen = len(events)
        m.close_dialogs()
        wait_until(lambda: not m._host_running, what="worker to end")
        time.sleep(0.05)
        self.assertEqual(len(events), seen)                                # nothing pushed into a window being closed

    # -- Save to PC
    def test_save_to_pc_copies_where_the_user_chose(self):
        m, _ = self.model(tick_audio=False)
        dest = self.tmp / "kept.wav"
        seen = {}

        def pick(**kw):
            seen.update(kw)
            return str(dest)

        m.attach_save_dialog(pick)
        m.run_tool("hosty", {"destination": "Save to PC"})
        wait_until(lambda: dest.exists(), what="the copy")
        wait_until(lambda: str(dest) in self.run_state(m)["message"], what="result box update")
        self.assertEqual(self.run_state(m)["state"], "done")
        self.assertEqual(seen["filename"], "tone.wav")
        self.assertIn("Saved copy to: %s" % dest, self.log_text(m))

    def test_save_to_pc_cancel_keeps_the_original_and_says_so(self):
        m, _ = self.model(tick_audio=False)
        m.attach_save_dialog(lambda **kw: "")
        m.run_tool("hosty", {"destination": "Save to PC"})
        wait_until(lambda: "Save As canceled" in self.log_text(m), what="cancel log")
        self.assertIn(str(self.out), self.run_state(m)["message"])

    def test_save_to_pc_copy_failure_is_shown_in_the_result_box(self):
        m, _ = self.model(tick_audio=False)
        target = self.tmp / "missing-folder" / "x.wav"                    # the folder does not exist -> copyfile raises OSError
        m.attach_save_dialog(lambda **kw: str(target))
        m.run_tool("hosty", {"destination": "Save to PC"})
        wait_until(lambda: "Could not save a copy" in self.run_state(m)["message"], what="error line")
        self.assertEqual(self.run_state(m)["state"], "done")               # the file was still generated

    def test_save_to_pc_without_a_dialog_says_so(self):
        m, _ = self.model(tick_audio=False)
        m.run_tool("hosty", {"destination": "Save to PC"})
        wait_until(lambda: "Save As is not available" in self.log_text(m), what="log")

    def test_the_run_is_done_before_the_save_dialog_opens(self):
        m, _ = self.model(tick_audio=False)
        state_when_asked = []
        m.attach_save_dialog(lambda **kw: (state_when_asked.append(self.run_state(m)["state"]), "")[1])
        m.run_tool("hosty", {"destination": "Save to PC"})
        wait_until(lambda: state_when_asked, what="dialog")
        self.assertEqual(state_when_asked, ["done"])

    # -- the default
    def test_leave_in_output_folder_does_neither(self):
        m, _ = self.model()
        pick = mock.Mock(return_value="")
        m.attach_save_dialog(pick)
        m.run_tool("hosty", {"destination": "Leave in output folder"})
        run = self.finished(m)
        self.assertEqual(run["state"], "done")
        pick.assert_not_called()
        self.assertEqual(self.live.calls, [])

    def test_a_failed_tool_is_never_placed_or_saved(self):
        with mock.patch.dict(host_tools.HOST_TOOLS, {"hosty": lambda f, s: {"ok": False, "message": "ffmpeg missing"}}):
            m, _ = self.model()
            pick = mock.Mock(return_value="")
            m.attach_save_dialog(pick)
            m.run_tool("hosty", {"destination": "Add to Live Set"})
            self.assertEqual(self.finished(m)["state"], "error")
            self.assertEqual(self.live.calls, [])
            pick.assert_not_called()


if __name__ == "__main__":
    unittest.main()
