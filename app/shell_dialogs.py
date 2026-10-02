"""Native dialog windows for the webview tools (Song Mapper, Fill Forge).

The Tk app spawned a child *process* per dialog (webview_pane.py + breakdowns_window.py) and polled a temp
file. The shell opens the very same dialog HTML in a second pywebview window of ITS OWN process instead:
no extra WebView2 host process, and the dialog closes with the shell.

Nothing here edits, wraps or re-themes a dialog. The HTML is loaded as-is (the caller fills the existing
`__CTX_JSON__` placeholder); the only thing added to the page is the same one-line shim the child process
injected, `window.liveActionsSend`, which every dialog's own send() already calls.

The pywebview part is one small function (`native_window`) so everything else -- one dialog at a time, the
once-only result, cleanup -- is testable with a fake window factory (test_shell_dialogs.py).
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

DIALOG_SIZE = (1180, 780)
DIALOG_MIN = (980, 640)
DIALOG_BG = "#08090C"

# Defined on `loaded`, NOT by overriding window.chrome.webview: pywebview's own js_api plumbing is built on
# that channel (see breakdowns_window.py for the history). A separate property cannot collide with it.
SEND_SHIM = """
window.liveActionsSend = function (raw) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.receive) {
    window.pywebview.api.receive(raw);
  }
};
"""


def payload_from_raw(raw: Any) -> Any:
    """What the dialog handed to liveActionsSend -> the payload the run handler wants.
    Dialogs send JSON `{"method": "close_and_send", "params": [payload]}`; anything else passes through."""
    if not isinstance(raw, str):
        return raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, dict) and data.get("method") == "close_and_send":
        params = data.get("params") or []
        return params[0] if params else None
    return data


def embed_json(value: Any) -> str:
    """JSON for a `<script>` block. `<` is written \\u003c so a track named `</script>` cannot close the
    block early; JavaScript reads back the identical value."""
    return json.dumps(value).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class _DialogApi:
    """window.pywebview.api of ONE dialog. pywebview exposes every public attribute to the page, so the
    only public member is `receive`; the wiring is private (test_shell_dialogs pins the surface)."""

    def __init__(self, deliver: Callable[[Any], None]) -> None:
        self._deliver = deliver

    def receive(self, raw: str) -> None:
        self._deliver(payload_from_raw(raw))


class _Open:
    def __init__(self, tool_id: str, html_path: Path, on_result: Callable[[Any], None]) -> None:
        self.tool_id = tool_id
        self.html_path = html_path
        self.on_result = on_result
        self.window: Any = None
        self.done = False


class DialogHost:
    """One dialog at a time. `open_window(title, url, api, on_closed)` returns an object with
    `destroy()` and `raise_()`; the real one is `native_window`, tests pass a fake."""

    def __init__(self, open_window: Callable[..., Any], *, temp_dir: str | None = None, log: Callable[[str], None] | None = None) -> None:
        self._open_window = open_window
        self._temp_dir = temp_dir
        self._log = log or (lambda _t: None)
        self._lock = threading.Lock()
        self._current: _Open | None = None

    def is_open(self, tool_id: str | None = None) -> bool:
        with self._lock:
            cur = self._current
            return cur is not None and not cur.done and (tool_id is None or cur.tool_id == tool_id)

    def open(self, tool_id: str, title: str, html: str, on_result: Callable[[Any], None]) -> str:
        """Show `html` in a native window. Returns "opened", "replaced" (a different tool's dialog was closed
        first, as the Tk tool page did) or "raised" (the same tool was already open). `on_result` is called
        exactly once: with the dialog's payload, or None if it was closed without sending."""
        with self._lock:
            cur = self._current
        if cur is not None and not cur.done:
            if cur.tool_id == tool_id:
                self._raise(cur)
                return "raised"
            self._finish(cur, None)               # cancels the old one (its on_result gets None)
            outcome = "replaced"
        else:
            outcome = "opened"

        handle, name = tempfile.mkstemp(prefix="%s-" % tool_id, suffix=".html", dir=self._temp_dir)
        os.close(handle)
        path = Path(name)
        path.write_text(html, encoding="utf-8")
        rec = _Open(tool_id, path, on_result)
        api = _DialogApi(lambda payload, r=rec: self._finish(r, payload))
        with self._lock:
            self._current = rec
        try:
            rec.window = self._open_window(title, path.as_uri(), api, lambda r=rec: self._finish(r, None))
        except Exception:
            with self._lock:
                if self._current is rec:
                    self._current = None
            rec.done = True
            self._unlink(path)
            raise
        return outcome

    def close_all(self) -> None:
        with self._lock:
            cur = self._current
        if cur is not None and not cur.done:
            self._finish(cur, None)

    # -- internals ---------------------------------------------------------------

    def _finish(self, rec: _Open, payload: Any) -> None:
        with self._lock:
            if rec.done:
                return
            rec.done = True
            if self._current is rec:
                self._current = None
        window = rec.window
        if window is not None:
            try:
                window.destroy()
            except Exception as exc:                # already gone (user closed it): nothing to do
                self._log("Dialog window close: %s" % exc)
        self._unlink(rec.html_path)
        try:
            rec.on_result(payload)
        except Exception as exc:                    # a handler bug must never wedge the window thread
            self._log("Dialog result handler failed: %s" % exc)

    def _raise(self, rec: _Open) -> None:
        try:
            if rec.window is not None:
                rec.window.raise_()
        except Exception as exc:
            self._log("Could not raise the dialog: %s" % exc)

    @staticmethod
    def _unlink(path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass


# ── The one pywebview-specific piece ───────────────────────────────────────────

class _NativeWindow:
    def __init__(self, window: Any) -> None:
        self._window = window

    def destroy(self) -> None:
        self._window.destroy()

    def raise_(self) -> None:
        import ctypes
        try:
            self._window.restore()
        except Exception:
            pass
        try:
            hwnd = int(self._window.native.Handle.ToInt64())
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


def native_window(title: str, url: str, api: Any, on_closed: Callable[[], None]) -> _NativeWindow:
    """Create the dialog window. Same parameters breakdowns_window.py used (size, minimum, background,
    on top, no text selection). Callable from any thread once webview.start() is running."""
    import ctypes
    import webview

    window = webview.create_window(
        title, url, width=DIALOG_SIZE[0], height=DIALOG_SIZE[1], min_size=DIALOG_MIN,
        background_color=DIALOG_BG, text_select=False, on_top=True, js_api=api,
    )

    state = {"closed": False}

    def on_loaded() -> None:
        if not state["closed"]:                       # a late `loaded` for a window already destroyed would hit a disposed WebView2
            window.evaluate_js(SEND_SHIM)

    def on_gone() -> None:
        state["closed"] = True
        on_closed()

    def on_shown() -> None:
        # Windows' foreground lock would otherwise leave the new window behind Live / the shell.
        try:
            hwnd = int(window.native.Handle.ToInt64())
            ctypes.windll.user32.ShowWindow(hwnd, 5)          # SW_SHOW
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except Exception:
            pass

    window.events.loaded += on_loaded
    window.events.shown += on_shown
    window.events.closed += on_gone
    # Created off the GUI thread, the window may already have loaded before the handlers above existed.
    # The shim is idempotent, so running it twice is harmless; running it never would break Insert/Apply.
    try:
        if window.events.loaded.is_set():
            on_loaded()
    except Exception:
        pass
    return _NativeWindow(window)
