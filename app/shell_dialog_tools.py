"""The two webview-dialog tools in the shell: Song Mapper and Fill Forge.

Built on the original Tk window's dialog flow, with the Tk-only parts replaced:

  * the dialog is a native window opened through `shell_dialogs.DialogHost` (never edited or re-themed --
    the user's standing decision: Fill Forge keeps its design and its own theme picker);
  * messagebox.askyesno  -> `confirm(title, message)`, called on a worker thread with NO lock held;
  * messagebox errors    -> the tool's result box + the console (state "error").

Everything that blocks (the arrangement scan, plan calls, native confirms) runs on a
worker thread; the model lock is only ever held for short state reads and writes.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable

import shell_dialogs

DIALOG_TOOLS = ("song-mapper", "fill-forge")
AH_CAP = 80                    # matches the bridge's own check inside computeArrangementPlan
AH_WAIT_S = 20.0


def _spawn(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, daemon=True, name="dialog-tool").start()


def _beats(sig: str) -> int:
    if "/" in sig:
        try:
            return max(1, int(sig.split("/", 1)[0]))
        except ValueError:
            pass
    return 4


def _tempo(bpm: Any) -> float | None:
    try:
        return float(bpm)
    except (TypeError, ValueError):
        return None


class DialogTools:
    def __init__(
        self,
        model: Any,
        host: Any,
        confirm: Callable[[str, str], bool],
        spawn: Callable[[Callable[[], None]], None] = _spawn,
    ) -> None:
        self._m = model
        self._host = host
        self._confirm = confirm
        self._spawn = spawn
        self._scan: dict[str, Any] | None = None     # Song Mapper: consumed once by its context
        self._closing = False

    def shutdown(self) -> None:
        """The app is closing: close any open dialog, and let its "cancelled" result die quietly. Without
        this the result would emit page events into a window that is already being disposed."""
        self._closing = True
        if self._host is not None:
            self._host.close_all()

    # -- opening -------------------------------------------------------------------

    def open(self, tool: dict[str, Any], name: str) -> dict[str, Any]:
        """Start opening `tool`'s dialog. Returns at once; the window opens on a worker."""
        m = self._m
        tool_id = str(tool["id"])
        with m._lock:
            if tool_id == "song-mapper" and not m._connected:
                msg = "⚠  Bridge offline — start Live and drop the bridge device."
                m._finish_run(tool_id, "error", msg)
                return {"ok": False, "message": msg}
            if self._host is None:
                msg = "⚠  Dialog windows are not available here."
                m._finish_run(tool_id, "error", msg)
                return {"ok": False, "message": msg}
            if self._host.is_open(tool_id):
                self._host.open(tool_id, name, "", lambda _p: None)     # raises the one that is open
                return {"ok": True, "message": "%s is already open — brought to the front." % name}
            msg = "Opening %s…" % name
            m._finish_run(tool_id, "running", msg)
        self._spawn(lambda: self._open_worker(tool, name))
        return {"ok": True, "message": msg}

    def _open_worker(self, tool: dict[str, Any], name: str) -> None:
        m = self._m
        tool_id = str(tool["id"])
        try:
            if tool_id == "song-mapper":
                with m._lock:
                    m._finish_run(tool_id, "running", "Scanning the Set for an existing arrangement…")
                    candidate = self._default_section_track(self._ctx_arrangement(None))
                scan: dict[str, Any] = {}
                if candidate:
                    result = m._bridge.call_live("arrangement_scan", {"trackPath": candidate})
                    if result.get("ok"):
                        scan = result
                    else:
                        reason = str(result.get("message") or result.get("error") or "scan failed")
                        m.log("Song Mapper: scan failed (%s) -- opening in create mode." % reason)
                self._scan = {"trackPath": candidate, "scan": scan}
            html = self._html(tool)
            if not html:
                raise RuntimeError("Could not load the %s dialog HTML file." % name)
            with m._lock:
                m._finish_run(tool_id, "running", str(tool.get("dialogStatus") or "%s is open in its own dialog window." % name))
            self._host.open(tool_id, name, html, lambda payload: self._on_result(tool, name, payload))
            m.log("%s dialog opened." % name)
        except Exception as exc:
            with m._lock:
                m._finish_run(tool_id, "error", "⚠  Could not open the %s dialog: %s" % (name, exc))
            m.log("%s dialog error: %s" % (name, exc))

    def _html(self, tool: dict[str, Any]) -> str:
        path = Path(str(tool.get("_path") or "")) / str(tool.get("dialog") or "ui/dialog.html")
        if not path.is_file():
            return ""
        with self._m._lock:
            ctx = self._context(str(tool.get("id") or ""))
        return path.read_text(encoding="utf-8").replace("__CTX_JSON__", shell_dialogs.embed_json(ctx))

    # -- what each dialog is handed (__CTX_JSON__) -----------------------------------

    def _context(self, tool_id: str) -> dict[str, Any]:
        if tool_id == "fill-forge":
            return self._ctx_breakdowns()
        if tool_id == "song-mapper":
            return self._ctx_arrangement(self._scan)
        return {}

    def _time(self) -> tuple[int, float | None]:
        s = self._m._set
        return _beats(str(s.get("sig") or "4/4")), _tempo(s.get("bpm"))

    def _ctx_breakdowns(self) -> dict[str, Any]:
        m = self._m
        names = [str(t.get("name") or t.get("key") or "track") for t in m.selected_tracks()]
        beats, tempo = self._time()
        return {
            "source": "MidiTrack",
            "hasClip": bool(names),
            "clipName": ", ".join(names) if names else "tick a MIDI track",
            "beatsPerBar": beats,
            "tempo": tempo,
            "spec": {
                "genre": "melodicHouse", "technique": "ghostGroove", "context": "groove", "lengthBars": 1,
                "beatsPerBar": beats, "intensity": 0.6, "density": 0.6, "swing": 0,
                "humTiming": 0.3, "humVel": 0.3, "seed": 1,
            },
            "availableTargets": ["newClip", "replace", "append", "newTrack", "playhead"],
            "noteCount": 0,
        }

    def _ctx_arrangement(self, cache: dict[str, Any] | None) -> dict[str, Any]:
        """isEditing / sections / scanCount / nextId come from a real arrangement_scan reply when one is
        cached; otherwise the honest create-mode defaults. The cache is consumed here so a later call
        cannot reuse stale edit-mode data."""
        if cache is not None and cache is self._scan:
            self._scan = None
        scan = (cache or {}).get("scan") or {}
        scan_ok = bool(scan.get("ok"))
        beats, tempo = self._time()
        m = self._m
        tracks = [
            {
                "path": str(t.get("path") or ""),
                "name": str(t.get("name") or t.get("key") or "track"),
                "kind": str(t.get("kind") or "audio").lower(),
                "ticked": t.get("key") in m._targets,
            }
            for t in m._tracks
        ]
        stored = (m._settings.get("tool_prefs") or {}).get("song-mapper", {})
        ctx: dict[str, Any] = {
            "isEditing": bool(scan_ok and scan.get("isEditing")),
            "sections": (scan.get("sections") or []) if scan_ok else [],
            "nextId": int(scan.get("nextId") or 0) if scan_ok else 0,
            "scanCount": int(scan.get("scanCount") or 0) if scan_ok else 0,
            "beatsPerBar": beats,
            "tempo": tempo,
            "tracks": tracks,
            "lastSectionTrackPath": str((cache or {}).get("trackPath") or "") or str(stored.get("sectionTrackPath") or ""),
        }
        if scan_ok and scan.get("startBar") is not None:
            ctx["startBar"] = scan.get("startBar")
        if scan_ok and scan.get("truncated"):
            ctx["truncated"] = True
        return ctx

    @staticmethod
    def _default_section_track(ctx: dict[str, Any]) -> str:
        """Mirrors dialog.html's own defaultSectionTrackPath() so the pre-open scan targets the track the
        dialog shows selected: last persisted (if still a MIDI track) -> one named "Arrangement" -> the
        first ticked MIDI track -> the first MIDI track. Keep both in sync if either changes."""
        midi = [t for t in (ctx.get("tracks") or []) if t.get("kind") == "midi"]
        if not midi:
            return ""
        last = str(ctx.get("lastSectionTrackPath") or "")
        if last and any(t.get("path") == last for t in midi):
            return last
        for t in midi:
            if str(t.get("name") or "").strip().lower() == "arrangement":
                return str(t["path"])
        for t in midi:
            if t.get("ticked"):
                return str(t["path"])
        return str(midi[0]["path"])

    # -- what a dialog sends back ----------------------------------------------------

    def _on_result(self, tool: dict[str, Any], name: str, payload: Any) -> None:
        """Called by the window host on whatever thread closed the dialog -- so hand off at once."""
        self._spawn(lambda: self._handle_result(tool, name, payload))

    def _handle_result(self, tool: dict[str, Any], name: str, payload: Any) -> None:
        m = self._m
        tool_id = str(tool["id"])
        if self._closing:
            return
        data: Any = payload
        if isinstance(payload, str) and payload != "":
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                self._fail(tool_id, "Webview tool sent an invalid payload.")
                return
        if not isinstance(data, dict):                # closed / cancelled: nothing was written
            with m._lock:
                if m._pending_run != tool_id:
                    m._finish_run(tool_id, "idle", "Dialog closed — nothing was written.")
            m.log("%s dialog closed." % name)
            return
        try:
            if tool_id == "fill-forge":
                self._run_breakdowns(name, data)
            elif tool_id == "song-mapper":
                self._run_arrangement_helper(name, data)
        except Exception as exc:                      # never let a handler bug leave the tool "running"
            self._fail(tool_id, "%s failed unexpectedly: %s" % (name, exc))

    def _fail(self, tool_id: str, message: str) -> None:
        with self._m._lock:
            self._m._finish_run(tool_id, "error", "⚠  " + message)
        self._m.log("✗ " + message)

    def _cancelled(self, tool_id: str, name: str) -> None:
        with self._m._lock:
            self._m._finish_run(tool_id, "idle", "Cancelled — nothing was written.")
        self._m.log("%s: cancelled by user." % name)

    def _targets_payload(self) -> list[dict[str, Any]]:
        return [
            {"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")}
            for t in self._m.selected_tracks()
        ]

    # -- Fill Forge ----------------------------------------------------------------------

    def _run_breakdowns(self, name: str, request: dict[str, Any]) -> None:
        m = self._m
        with m._lock:
            targets = self._targets_payload()
        if not targets:
            self._fail("fill-forge", "Select at least one track on the left first.")
            return
        notes = request.get("notes") or []
        if not notes:
            self._fail("fill-forge", "No notes generated to insert.")
            return
        payload = {
            "tracks": targets,
            "fields": {
                "target": str(request.get("target") or "newClip"),
                "lengthBeats": request.get("lengthBeats") or 4,
                "name": str(request.get("name") or "Fill Forge"),
                "notes": notes,
            },
        }
        f = payload["fields"]
        with m._lock:
            m._dispatch_run(
                "fill-forge", name, payload,
                "Inserted fill '%s' (%d notes) as %s on %d track(s)." % (f["name"], len(notes), f["target"], len(targets)),
                "Inserting fill '%s' on %d track(s)…" % (f["name"], len(targets)),
            )

    # -- Song Mapper ----------------------------------------------------------------

    def _run_arrangement_helper(self, name: str, request: dict[str, Any]) -> None:
        """The two-call sequence: arrangement_plan (read-only, real numbers) -> confirm -> execute."""
        m = self._m
        section_track_path = str(request.get("sectionTrackPath") or "")
        with m._lock:
            if not section_track_path:
                m._finish_run("song-mapper", "idle", "No section track chosen — nothing to plan.")
                m.log("Song Mapper: no section track chosen -- nothing to plan.")
                return
            m._save_prefs("song-mapper", {"sectionTrackPath": section_track_path})
            ticked_paths = [
                str(t.get("path") or "") for t in m._tracks
                if t.get("key") in m._targets and t.get("path") and str(t.get("path")) != section_track_path
            ]
            beats, _tempo_unused = self._time()
            bridge = m._bridge
        remap_all_tracks = bool(request.get("remapAllTracks"))
        plan_fields = {
            "sections": request.get("sections") or [],
            "createLocators": bool(request.get("createLocators")),
            "remapAllTracks": remap_all_tracks,
            "renameTrack": bool(request.get("renameTrack")),
            "sectionTrackPath": section_track_path,
            "scanCount": int(request.get("scanCount") or 0),
            "isEditing": bool(request.get("isEditing")),   # the dialog echoes the flag arrangement_scan seeded it with
            "beatsPerBar": beats,
            "tickedTrackPaths": ticked_paths,
        }
        plan = bridge.call_live("arrangement_plan", plan_fields)
        if not plan.get("ok"):
            reason = str(plan.get("message") or plan.get("error") or "unknown error")
            self._fail("song-mapper", "Song Mapper: plan refused -- %s" % reason)
            return

        write_count = int(plan.get("writeCount") or 0)
        moved = int(plan.get("moved") or 0)
        section_count = int(plan.get("sectionCount") or 0)
        # The cap is checked with the plan's own numbers BEFORE any confirm, i.e. before the user says yes.
        if write_count > AH_CAP:
            self._fail(
                "song-mapper",
                "Song Mapper — run refused: %d write operations exceeds the %d-operation safety cap. "
                "Nothing was written." % (write_count, AH_CAP),
            )
            return

        undo_steps = int(plan.get("undoStepCount") or 0)
        move_line = " and moves %d existing clip(s) on remap track(s)" % moved if moved > 0 else ""
        if not self._confirm(
            "Song Mapper — Confirm",
            "This creates %d section clip(s)%s, as %d individual undo step(s).\n\n"
            "This cannot be undone in one step -- save your Set first. A failure partway "
            "through this run can leave temporary clips behind that won't be auto-removed."
            "\n\nContinue?" % (section_count, move_line, undo_steps),
        ):
            self._cancelled("song-mapper", name)
            return
        if remap_all_tracks:
            if not self._confirm(
                "Song Mapper — Whole Project",
                "Whole Project is on -- this also affects all %d eligible track(s), not just "
                "ticked ones.\n\nContinue?" % int(plan.get("remapTrackCount") or 0),
            ):
                self._cancelled("song-mapper", name)
                return

        exec_fields = dict(plan_fields)
        exec_fields["fingerprint"] = plan.get("fingerprint") or {}
        with m._lock:
            m._dispatch_run(
                "song-mapper", name, {"fields": exec_fields},
                "Song Mapper: sent %d section(s)%s to the bridge for execution." % (section_count, move_line),
                "Writing %d section(s)%s…" % (section_count, move_line),
                AH_WAIT_S,
            )
