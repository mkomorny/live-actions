"""Single-instance mutex + "raise the running window" event -- Win32, no UI toolkit.

Same names as helper.py's (mutex, raise event, window title) so the WebView2 shell
and the Tk app are the *same* app as far as a second launch is concerned: whichever
is running gets raised instead of a duplicate starting. `LIVE_ACTIONS_INSTANCE`
suffixes all three (via settings_store), so an isolated copy still coexists.

Spike A (docs/plans/v1.0.56-slice1-spike-a-and-b.md) verified this logic unchanged
against a real WebView2 HWND.
"""

from __future__ import annotations

import ctypes
import threading
from typing import Callable

import settings_store

SUFFIX = settings_store.instance_suffix()
MUTEX_NAME = "Local\\LiveActionsDesktopHost" + SUFFIX
RAISE_EVENT_NAME = "Local\\LiveActionsRaiseHost" + SUFFIX
WINDOW_TITLE = "Live Actions — DAW Studio Host" + (f" [{settings_store.INSTANCE}]" if SUFFIX else "")
SW_RESTORE = 9
WM_CLOSE = 0x0010
ERROR_ALREADY_EXISTS = 183
EVENT_MODIFY_STATE = 0x0002

_mutex_handle = None
_raise_handle = None


def claim() -> bool:
    """True if this process is the only instance."""
    global _mutex_handle
    kernel32 = ctypes.windll.kernel32
    _mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return int(kernel32.GetLastError()) != ERROR_ALREADY_EXISTS


def force_foreground(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.ShowWindow(hwnd, SW_RESTORE)
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    this_tid = kernel32.GetCurrentThreadId()
    user32.AttachThreadInput(this_tid, fg_tid, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(this_tid, fg_tid, False)


def raise_existing() -> None:
    """Second launch: raise the running window and signal its raise watcher."""
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd and not SUFFIX:
        hwnd = user32.FindWindowW(None, "Live Actions")
    if hwnd:
        force_foreground(hwnd)
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, RAISE_EVENT_NAME)
    if handle:
        kernel32.SetEvent(handle)
        kernel32.CloseHandle(handle)


def start_raise_watcher(get_hwnd: Callable[[], int]) -> None:
    """Background thread: when a second launch signals the event, foreground our window."""
    global _raise_handle
    kernel32 = ctypes.windll.kernel32
    _raise_handle = kernel32.CreateEventW(None, False, False, RAISE_EVENT_NAME)
    handle = _raise_handle

    def watch() -> None:
        while True:
            if kernel32.WaitForSingleObject(handle, 0xFFFFFFFF) != 0:
                return
            try:
                hwnd = get_hwnd()
                if hwnd:
                    force_foreground(hwnd)
            except Exception:
                return

    threading.Thread(target=watch, daemon=True, name="raise-watcher").start()


def post_close(hwnd: int) -> None:
    """Shut a window down the one way spike B proved safe from any thread: a native
    WM_CLOSE, which Windows delivers on the window's own GUI thread. Never
    window.destroy() off the GUI thread (it touches WebView2 COM objects)."""
    ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
