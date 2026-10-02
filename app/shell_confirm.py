"""One pending "may I do this?" question for the WebView2 shell -- pure logic, no UI import.

Genius tools that spend the user's money (today: `live_tts_vocal`, which bills a Cartesia /
OpenAI / xAI key) must not fire unprompted. A Genius turn runs on its own worker thread
(shell_genius._work, name="genius-turn"), so it can block on a question the page answers --
the same trick shell_placement.SlotPicker uses for "which clip slot?".

Deliberately a sibling of shell_placement rather than a second class inside it: that module is
about generated files and clip slots, this one is about approval, and the only thing they share
is the ask/answer/patch shape.

The "don't ask again" flag lives on this object, in memory. The user asked for it to last the
session, so it must never reach settings.json -- closing the app is what clears it.
"""

from __future__ import annotations

import threading
from typing import Any, Callable


class ConfirmPicker:
    """The one pending approval question.

    A worker calls `ask()` and blocks; the page shows the request (it arrives as a `confirm`
    patch, and is part of the snapshot) and answers through `answer()` on a js_api thread.
    `lock` is the session model's RLock and `patch` its `_patch`, so the request reaches the
    page in the same order as every other state change. The lock is never held while waiting.

    Every path that does not produce an explicit "yes" returns False. A spend guard that
    fails open is not a guard.
    """

    def __init__(self, lock: Any, patch: Callable[..., None]) -> None:
        self._lock = lock
        self._patch = patch
        self._next_id = 0
        self._pending: dict[str, Any] | None = None   # {"view": {...}, "event": Event, "ok": bool}
        self._suppressed: set[str] = set()            # kinds the user said not to ask about again

    # -- state -------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._pending["view"]) if self._pending else None

    def suppressed(self, kind: str) -> bool:
        with self._lock:
            return str(kind) in self._suppressed

    def clear_suppression(self) -> None:
        """Forget every "don't ask again" -- used by tests and by a session reset."""
        with self._lock:
            self._suppressed.clear()

    # -- the question ------------------------------------------------------------

    def ask(self, kind: str, detail: dict[str, Any]) -> bool:
        """Show the modal and wait. True only if the user approved.

        `detail` is plain data built by the caller (genius_client) -- a title, label/value
        rows, and the button text -- so nothing about a specific tool is encoded here.
        """
        kind = str(kind or "")
        event = threading.Event()
        with self._lock:
            if kind in self._suppressed:
                return True
            if self._pending is not None:        # one Genius turn at a time; never strand the older worker
                self._resolve(False)
            self._next_id += 1
            view = {
                "id": self._next_id,
                "kind": kind,
                "title": str(detail.get("title") or "Confirm"),
                "body": str(detail.get("body") or ""),
                "rows": [
                    {"label": str(r[0]), "value": str(r[1])}
                    for r in (detail.get("rows") or [])
                    if isinstance(r, (list, tuple)) and len(r) >= 2
                ],
                "confirmLabel": str(detail.get("confirmLabel") or "Continue"),
                "rememberLabel": str(detail.get("rememberLabel") or "Don't ask again this session"),
            }
            self._pending = {"view": view, "event": event, "ok": False}
            entry = self._pending
            self._patch(confirm=view)
        event.wait()
        return bool(entry["ok"])                 # `_resolve` stores it before setting the event

    def answer(self, req_id: Any, approved: Any, remember: Any = False) -> dict[str, Any]:
        """The page's reply. `remember` only sticks on an approval -- a "no, and stop asking"
        would silently approve every later call, which is the opposite of what it says."""
        with self._lock:
            pending = self._pending
            if pending is None or pending["view"]["id"] != req_id:
                return {"ok": False, "stale": True, "error": "That question is no longer open."}
            ok = bool(approved)
            if ok and bool(remember):
                self._suppressed.add(str(pending["view"]["kind"]))
            self._resolve(ok)
            return {"ok": True, "approved": ok}

    def cancel(self, quiet: bool = False) -> None:
        """Deny whatever is pending. `quiet` (app closing): do not push a patch into a window
        that is being disposed."""
        with self._lock:
            if self._pending is not None:
                self._resolve(False, quiet=quiet)

    def _resolve(self, ok: bool, quiet: bool = False) -> None:
        pending, self._pending = self._pending, None
        if pending is None:
            return
        pending["ok"] = ok
        if not quiet:
            self._patch(confirm=None)
        pending["event"].set()
