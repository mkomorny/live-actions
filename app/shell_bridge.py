"""UiBus + ShellApi -- the Python <-> page boundary of the WebView2 shell.

Design proven by spike B (docs/plans/v1.0.56-slice1-spike-a-and-b.md); the two
rules that spike found are load-bearing here:

  1. Shutdown is a native WM_CLOSE (see shell.py), never window.destroy() from a
     spawned thread or from inside a js_api method.
  2. Every live window/bridge/model/lock reference on ShellApi is a `_private`
     attribute. pywebview builds window.pywebview.api by recursively walking every
     PUBLIC attribute of the js_api object (webview/util.py get_functions), so a
     public `self.window` is walked straight into the WebView2 COM object graph.
     test_shell_bridge asserts every public attribute here is a plain method.

No pywebview import at module level: the window only has to expose
`evaluate_js(str)` (and, for ShellApi, `create_file_dialog`), which is what lets
the tests drive all of this with a fake window.
"""

from __future__ import annotations

import json
import queue
import threading
from typing import Any, Callable

import shell_model

_STOP = object()


class UiBus:
    """One ordered channel from Python threads into the page.

    `push()` is safe from any thread and never blocks (a queue put) -- the
    BridgeClient listener thread calls it via the model and must return
    immediately. One dedicated pusher thread drains the queue and is the ONLY
    thread that calls evaluate_js, so events reach the page in exactly the order
    they were pushed and evaluate_js is never re-entered.

    Events are held back until the page has fetched its snapshot (`open_gate`),
    because evaluate_js before the page exists would silently drop them.
    """

    def __init__(self, evaluate_js: Callable[[str], Any] | None = None) -> None:
        self._evaluate_js = evaluate_js
        self._queue: queue.Queue = queue.Queue()
        self._gate = threading.Event()
        self._seq = 0
        self._pusher = threading.Thread(target=self._pump, daemon=True, name="ui-bus-pusher")
        self._started = False
        self._errors: list[str] = []

    def attach(self, evaluate_js: Callable[[str], Any]) -> None:
        self._evaluate_js = evaluate_js

    def start(self) -> None:
        if not self._started:
            self._started = True
            self._pusher.start()

    def push(self, event: dict[str, Any]) -> None:
        self._queue.put(event)

    def open_gate(self) -> None:
        """Discard anything queued before the page's snapshot (the snapshot already
        contains it) and let later events through. Callers hold the model lock so
        no event can slip between the snapshot and this call."""
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass
        self._gate.set()

    def close_gate(self) -> None:
        self._gate.clear()

    def _pump(self) -> None:
        while True:
            # Wait for the gate BEFORE taking an item. Taking first would leave the pump holding
            # one pre-snapshot event that open_gate() can no longer discard -- the page would
            # receive it a second time (once in the snapshot, once as a push).
            self._gate.wait()
            item = self._queue.get()
            if item is _STOP:
                return
            self._seq += 1
            payload = json.dumps(dict(item, seq=self._seq))
            try:
                if self._evaluate_js is not None:
                    self._evaluate_js("window.__uiBusRecv && window.__uiBusRecv(%s)" % payload)
            except Exception as exc:  # the page can vanish mid-push during shutdown
                self._errors.append(str(exc))

    def stop(self) -> None:
        # Order matters (spike B): callers close the bridge first so nothing new is
        # queued, then this joins the pusher so no evaluate_js is in flight when
        # the window is torn down on the GUI thread.
        self._queue.put(_STOP)
        self._gate.set()
        if self._started:
            self._pusher.join(timeout=2.0)


class Ticker:
    """Calls `model.tick()` every PING_EVERY_S on its own thread."""

    def __init__(self, tick: Callable[[], None], every: float = shell_model.PING_EVERY_S) -> None:
        self._tick = tick
        self._every = every
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="live-actions-ticker")

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self._every):
            try:
                self._tick()
            except Exception:  # a failed ping must never kill the heartbeat
                pass

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


class ShellApi:
    """window.pywebview.api. PUBLIC = callable from the page, so keep the public
    surface to plain methods with JSON-serialisable arguments and results, and
    keep every reference private (see module docstring, rule 2).

    API keys never cross this boundary: nothing here returns settings values
    other than ports and the theme slug (Preferences, slice 3, must expose
    masked keys only).
    """

    # Wiring is underscore-private on purpose: every public name here is callable from the page's
    # JavaScript, so a public bind()/set_window() would let the page swap out the live window.
    def _bind(self, *, model: shell_model.SessionModel, bus: UiBus, window: Any = None,
              quit_cb: Callable[[], None] | None = None) -> None:
        self._model = model
        self._bus = bus
        self._window = window
        self._quit_cb = quit_cb

    # -- state ---------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Atomic snapshot + open the event gate (see UiBus.open_gate)."""
        return self._model.snapshot_and(self._bus.open_gate)

    def log_text(self) -> str:
        return self._model.log_text()

    # -- target tracks -------------------------------------------------------

    def toggle_track(self, key: str) -> list:
        return self._model.toggle_track(str(key))

    def select_all(self) -> list:
        return self._model.set_all(True)

    def select_none(self) -> list:
        return self._model.set_all(False)

    def use_live_selection(self) -> list:
        return self._model.use_live_selection()

    # -- tools ---------------------------------------------------------------

    def run_tool(self, tool_id: str, fields: dict | None = None) -> dict:
        return self._model.run_tool(str(tool_id), fields if isinstance(fields, dict) else {})

    def pick_file(self, current: str = "", filetypes: list | None = None) -> str:
        """Native open-file dialog for a manifest `file` field. Returns "" when
        cancelled. pywebview marshals create_file_dialog onto the GUI thread."""
        window = self._window
        if window is None:
            return ""
        import os
        import webview  # deferred: keeps this module importable without pywebview

        start = os.path.dirname(current) if current else ""
        types = tuple(
            "%s (%s)" % (str(t[0]), str(t[1]).replace(",", ";"))
            for t in (filetypes or [])
            if isinstance(t, (list, tuple)) and len(t) >= 2
        )
        try:
            picked = window.create_file_dialog(
                webview.FileDialog.OPEN, directory=start if os.path.isdir(start) else "", file_types=types
            )
        except Exception as exc:
            self._model.log("File dialog failed: %s" % exc)
            return ""
        return str(picked[0]) if picked else ""

    # -- host-tool placement ---------------------------------------------------
    # The page's answer to the "choose a clip slot" modal (slot None = skip). The question itself arrives
    # as a pushed `placement` patch; the overwrite rule is enforced in Python (shell_placement.SlotPicker).

    def place_answer(self, req_id: int, slot: int | None = None, confirmed: bool = False) -> dict:
        return self._model.placement.answer(req_id, slot, bool(confirmed))

    # -- spend approval ----------------------------------------------------------
    # The page's answer to "may I run this paid tool call?". `remember` only takes effect on
    # an approval and lives in memory for this session only (shell_confirm.ConfirmPicker).

    def confirm_answer(self, req_id: int, approved: bool = False, remember: bool = False) -> dict:
        return self._model.confirm.answer(req_id, bool(approved), bool(remember))

    # -- Genius chat -----------------------------------------------------------
    # Every reply, tool-call chip and error reaches the page as pushed "genius" events;
    # these calls only start, stop or reset a turn.

    def genius_send(self, text: str) -> dict:
        return self._model.genius.send(str(text or ""))

    def genius_stop(self) -> bool:
        return self._model.genius.stop()

    def genius_clear(self) -> bool:
        self._model.genius.clear()
        return True

    def genius_set_agent(self, slug: str = "") -> dict:
        return self._model.genius.set_agent(str(slug or ""))

    # -- Preferences ---------------------------------------------------------------
    # ONE entry point on purpose: shell_prefs.PrefsService.OPS is the whitelist of what the page may
    # do, and every result carries the new masked snapshot. API keys only ever flow page -> Python.

    def prefs(self, op: str, args: dict | None = None) -> dict:
        return self._model.prefs.call(str(op), args if isinstance(args, dict) else {})

    def pick_folder(self, current: str = "") -> str:
        """Native folder dialog for a Preferences path field. "" when cancelled."""
        window = self._window
        if window is None:
            return ""
        import os
        import webview
        try:
            picked = window.create_file_dialog(webview.FileDialog.FOLDER, directory=current if os.path.isdir(current or "") else "")
        except Exception as exc:
            self._model.log("Folder dialog failed: %s" % exc)
            return ""
        return str(picked[0]) if picked else ""

    # -- bridge diagnostics ----------------------------------------------------

    def ping(self) -> bool:
        self._model.ping()
        return True

    def request_status(self) -> bool:
        self._model.request_status()
        return True

    def request_tracks(self) -> bool:
        self._model.request_tracks()
        return True

    def reset_bridge(self) -> dict:
        return self._model.reset_bridge()

    # -- lifecycle -------------------------------------------------------------

    def quit(self) -> bool:
        cb = self._quit_cb
        if cb is not None:
            # Off the js_api thread on purpose: shell.py's quit posts WM_CLOSE,
            # which Windows marshals onto the GUI thread. Never window.destroy().
            threading.Thread(target=cb, daemon=True, name="shell-quit").start()
        return True
