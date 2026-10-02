"""Launch-side helpers of the WebView2 shell (slice 4c): the start-up preflight.

Pure logic, no UI import -- every OS touch (filesystem, Popen, startfile, registry, importing) is injected so the
tests drive all of it with fakes, like shell_placement.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Callable

# Evergreen WebView2 runtime: Edge's updater keeps its version under this product GUID.
_WEBVIEW2_GUID = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_WEBVIEW2_KEYS = (
    ("HKLM", r"SOFTWARE\WOW6432Node\%s" % _WEBVIEW2_GUID),
    ("HKLM", r"SOFTWARE\%s" % _WEBVIEW2_GUID),
    ("HKCU", r"Software\%s" % _WEBVIEW2_GUID),
)


# -- start-up preflight -----------------------------------------------------------------------------

def webview2_version() -> str:
    """The installed WebView2 runtime's version, or "" when there is none."""
    try:
        import winreg
    except ImportError:  # not Windows
        return ""
    for hive, sub in _WEBVIEW2_KEYS:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE if hive == "HKLM" else winreg.HKEY_CURRENT_USER, sub) as key:
                value = str(winreg.QueryValueEx(key, "pv")[0] or "")
        except OSError:
            continue
        if value and value != "0.0.0.0":
            return value
    return ""


def preflight(import_module: Callable[[str], Any] = importlib.import_module,
              runtime_version: Callable[[], str] = webview2_version) -> list[str]:
    """What is missing for the shell to start, as sentences a person can act on. Empty = good to go."""
    problems: list[str] = []
    for module, package in (("webview", "pywebview"), ("clr", "pythonnet")):
        try:
            import_module(module)
        except Exception:  # ImportError, or a native load failure -- either way the shell cannot start
            problems.append("The Python package %s is not installed." % package)
    if not runtime_version():
        problems.append("The Microsoft Edge WebView2 Runtime is not installed (get the Evergreen runtime from microsoft.com/edge/webview2).")
    return problems


def preflight_message(problems: list[str]) -> str:
    fix = ""
    if any("Python package" in p for p in problems):
        fix = "\n\nTo install the Python packages, run this in the app folder:\n    python -m pip install -r requirements.txt"
    return "Live Actions can't start yet:\n\n\u2022 " + "\n\u2022 ".join(problems) + fix


def show_problem(text: str, title: str = "Live Actions") -> None:
    """A native message box: the launcher runs under pythonw, so a traceback would go nowhere."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)  # MB_ICONERROR
    else:
        print(text, file=sys.stderr)
