"""Host-tool placement for the WebView2 shell -- pure logic, no UI import.

TTS Vocal and Audio Sample have a `destination` field. After the file is generated:

  "Add to Live Set"  place it on the first ticked audio track: validate, let the user choose a clip slot
                     (an in-page modal, see SlotPicker), then `create_clip` through the bridge.
  "Save to PC"       offer a native Save As and copy the file there.

Ported from helper._place_generated_file / _ask_placement_slot / _offer_save_as (the Tk app). The dialog
itself is not here: `place_generated_file` takes an injected `ask_slot`, and `SlotPicker` is the piece that
lets a worker thread wait for the page's answer.
"""

from __future__ import annotations

import re
import shutil
import threading
from pathlib import Path
from typing import Any, Callable

SAVE_FILE_LABELS: dict[str, str] = {
    ".wav": "WAV audio",
    ".aiff": "AIFF audio",
    ".aif": "AIFF audio",
    ".mp3": "MP3 audio",
    ".flac": "FLAC audio",
    ".ogg": "Ogg Vorbis",
}

CONFIRM_REPLACE = "That slot has a clip — click Place again to replace it."


# ── Add to Live Set ───────────────────────────────────────────────────────────

def slot_view(slot: dict[str, Any]) -> dict[str, Any]:
    """One bridge `session_clips` entry -> what the modal needs (0-based `index`, 1-based `n`)."""
    idx = int(slot.get("index"))
    has = bool(slot.get("has_clip"))
    name = str((slot.get("clip") or {}).get("name") or "") if has else ""
    return {"index": idx, "n": idx + 1, "has": has, "name": name}


def place_generated_file(
    result: dict[str, Any],
    targets: list[dict[str, Any]],
    connected: bool,
    call_live: Callable[[str, dict[str, Any]], dict[str, Any]],
    ask_slot: Callable[[dict[str, Any], list[dict[str, Any]]], int | None],
) -> dict[str, Any]:
    """Place an already-generated file on the first ticked audio track (worker thread).

    Validation (offline / no audio track / unreadable slots) happens before any question is asked -- the
    slot picker only ever appears for a confirmed-valid target. `ask_slot(track, slot_views)` returns the
    chosen 0-based slot index, or None for "skip". Mutates and returns `result`."""
    path = result.get("path")
    base = str(result.get("message") or "Generated.")
    if not path:
        return result

    def out(text: str, placed: bool) -> dict[str, Any]:
        result["message"] = base + text
        result["placed"] = placed
        return result

    if not connected:
        return out(" Bridge offline — file saved, not placed in Live.", False)
    audio_targets = [t for t in targets if str(t.get("kind") or "audio") == "audio"]
    if not audio_targets:
        return out(" No ticked audio track — file saved, not placed.", False)
    track = audio_targets[0]
    track_index = track.get("index")

    slots_resp = call_live("read_track", {"track_index": track_index})
    if not slots_resp.get("ok"):
        reason = str(slots_resp.get("error") or slots_resp.get("message") or "unknown error")
        return out(" Could not read clip slots: " + reason, False)
    slots = [slot_view(s) for s in (slots_resp.get("session_clips") or []) if isinstance(s, dict) and s.get("index") is not None]
    if not slots:
        return out(" Track has no clip slots — file saved, not placed.", False)

    slot_index = ask_slot(track, slots)
    if slot_index is None:
        return out(" Placement skipped.", False)

    resp = call_live("create_clip", {"track_index": track_index, "slot_index": slot_index, "sample_file": path})
    if resp.get("ok"):
        track_name = str(track.get("name") or track.get("key") or "track")
        return out(" Placed on " + track_name + " (slot %d)." % (slot_index + 1), True)
    reason = str(resp.get("error") or resp.get("message") or "unknown error")
    return out(" Placement failed: " + reason, False)


class SlotPicker:
    """The one pending "choose a clip slot" question.

    A host worker calls `ask()` and blocks; the page shows the request (it arrives as a `placement` patch,
    and is part of the snapshot) and answers through `answer()` on a js_api thread. `lock` is the session
    model's RLock and `patch` its `_patch` (a non-blocking queue put), so the request reaches the page in
    the same order as every other state change. The lock is never held while waiting.
    """

    def __init__(self, lock: Any, patch: Callable[..., None]) -> None:
        self._lock = lock
        self._patch = patch
        self._next_id = 0
        self._pending: dict[str, Any] | None = None    # {"view": {...}, "event": Event, "slot": int|None, "occupied": set[int], "valid": set[int]}

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._pending["view"]) if self._pending else None

    def ask(self, tool_name: str, track: dict[str, Any], slots: list[dict[str, Any]]) -> int | None:
        """Show the modal and wait. Returns the chosen slot index, or None (cancelled / app closing /
        superseded)."""
        event = threading.Event()
        with self._lock:
            if self._pending is not None:              # cannot happen (one host run at a time); never strand the older worker
                self._resolve(None)
            self._next_id += 1
            view = {
                "id": self._next_id,
                "tool": tool_name,
                "track": str(track.get("name") or track.get("key") or "Track"),
                "slots": [dict(s) for s in slots],
            }
            entry = {
                "view": view, "event": event, "slot": None,
                "valid": {int(s["index"]) for s in slots},
                "occupied": {int(s["index"]) for s in slots if s.get("has")},
            }
            self._pending = entry
            self._patch(placement=view)
        event.wait()
        return entry["slot"]                           # `_resolve` stores it before setting the event

    def answer(self, req_id: Any, slot: Any, confirmed: bool = False) -> dict[str, Any]:
        """The page's reply. `slot` None = cancel. An occupied slot is refused until `confirmed` is true."""
        with self._lock:
            pending = self._pending
            if pending is None or pending["view"]["id"] != req_id:
                return {"ok": False, "stale": True, "error": "That question is no longer open."}
            if slot is None:
                self._resolve(None)
                return {"ok": True, "cancelled": True}
            if isinstance(slot, bool) or not isinstance(slot, int) or slot not in pending["valid"]:
                return {"ok": False, "error": "That is not one of the offered slots."}
            if slot in pending["occupied"] and not confirmed:
                return {"ok": False, "needsConfirm": True, "message": CONFIRM_REPLACE}
            self._resolve(slot)
            return {"ok": True}

    def cancel(self, quiet: bool = False) -> None:
        """Answer "skip" for whatever is pending. `quiet` (app closing): do not push a patch into a window
        that is being disposed."""
        with self._lock:
            if self._pending is not None:
                self._resolve(None, quiet=quiet)

    def _resolve(self, slot: int | None, quiet: bool = False) -> None:
        pending, self._pending = self._pending, None
        if pending is None:
            return
        pending["slot"] = slot
        if not quiet:
            self._patch(placement=None)
        pending["event"].set()


# ── Save to PC ────────────────────────────────────────────────────────────────

def save_dialog_args(path: str, tool_name: str = "File") -> dict[str, Any]:
    """What the native Save As needs: start in the file's folder, propose its name, filter to its type."""
    src = Path(path)
    ext = src.suffix or ".wav"
    label = SAVE_FILE_LABELS.get(ext.lower(), "%s file" % ext.lstrip(".").upper())
    label = re.sub(r"[^\w ]", "", label).strip() or "Audio"        # pywebview's filter grammar: word chars and spaces only
    return {
        "title": "Save %s As" % tool_name,
        "directory": str(src.parent),
        "filename": src.name,
        "file_types": ("%s (*%s)" % (label, ext), "All files (*.*)"),
        "ext": ext,
    }


def offer_save_as(
    path: str,
    tool_name: str,
    pick_save: Callable[..., str],
    copy: Callable[[Any, Any], Any] = shutil.copyfile,
) -> dict[str, Any]:
    """Ask where to save a copy and copy it. Returns {"status": "cancelled"|"same"|"saved"|"error", "dest": str, "error": str}.
    `pick_save(title=, directory=, filename=, file_types=)` -> chosen path or "" (cancelled)."""
    args = save_dialog_args(path, tool_name)
    picked = pick_save(title=args["title"], directory=args["directory"], filename=args["filename"], file_types=args["file_types"])
    if not picked:
        return {"status": "cancelled", "dest": "", "error": ""}
    dest = Path(str(picked))
    if not dest.suffix:
        dest = dest.with_suffix(args["ext"])
    src = Path(path)
    try:
        if dest.resolve() == src.resolve():
            return {"status": "same", "dest": str(dest), "error": ""}
        copy(src, dest)
    except OSError as exc:
        return {"status": "error", "dest": str(dest), "error": str(exc)}
    return {"status": "saved", "dest": str(dest), "error": ""}
