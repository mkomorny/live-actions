"""Live Actions -- WebView2 shell (the redesign's replacement for helper.py's Tk window).

    python shell.py [--demo-state] [--cdp-port N] [--ready-file PATH] [--size WxH]

Layout A · Workbench in the Riso Art Studio theme, served from app/web. Python owns
all state (shell_model.SessionModel); the page is a view of it:

    page  --js_api thread-->  ShellApi (shell_bridge)  -->  SessionModel
    page  <--evaluate_js----  UiBus pusher thread  <----  SessionModel / BridgeClient / Ticker

Threading rules carried over from spike B (docs/plans/v1.0.56-*.md):
  * shutdown is a native WM_CLOSE (single_instance.post_close), never window.destroy()
    off the GUI thread;
  * every live reference on the js_api object is private (see shell_bridge.ShellApi).

--demo-state loads the preview's mock set (no sockets) so a screenshot can be compared
with previews/redesign-round/shots/. --cdp-port exposes the WebView2 DevTools endpoint
for shell_dev/capture_shell.py. --ready-file is written once the window is up.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge_client
import settings_store
import shell_dialogs
import shell_launcher
import single_instance
import tool_manifests
from shell_bridge import ShellApi, Ticker, UiBus
from shell_model import SessionModel, load_demo_state

WEB_DIR = Path(__file__).resolve().parent / "web"
DEFAULT_SIZE = (1280, 800)
MIN_SIZE = (720, 520)


def _make_dpi_aware() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def _parse_size(text: str) -> tuple[int, int]:
    w, _, h = text.lower().partition("x")
    return int(w), int(h)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Live Actions WebView2 shell")
    ap.add_argument("--demo-state", action="store_true", help="show the preview's mock Set; open no sockets")
    ap.add_argument("--cdp-port", type=int, default=0, help="expose WebView2 DevTools on this port (test harness)")
    ap.add_argument("--ready-file", default="", help="write hwnd/pid here once the window has been shown")
    ap.add_argument("--dpi-unaware", action="store_true", help="fidelity capture only: lay out at a true 1x like the reference shots")
    ap.add_argument("--size", default="%dx%d" % DEFAULT_SIZE, help="initial window size WxH")
    args, extra = ap.parse_known_args(argv)
    # The liveactions:// protocol handler (registered by install.ps1, fired by the Max device's "Open desktop host")
    # runs `pythonw shell.py "liveactions://open"`. A bare argument like that is ignored, as helper.py always did;
    # an unknown --flag is still an error.
    flags = [a for a in extra if a.startswith("-")]
    if flags:
        ap.error("unrecognized arguments: %s" % " ".join(flags))
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.dpi_unaware:
        _make_dpi_aware()
    problems = shell_launcher.preflight()
    if problems:
        shell_launcher.show_problem(shell_launcher.preflight_message(problems))
        return 3
    if not single_instance.claim():
        single_instance.raise_existing()
        return 0

    if args.cdp_port:
        # Only reachable through this flag; WebView2 reads it when the environment is created.
        # Capture-only rendering flags, so the pixel grid matches the references (headless Chromium, 1x):
        #                                 (LCD text stays ON: the references were captured with it)
        #   --force-device-scale-factor=1 layout on a true 1x grid; on this 144-DPI display Chromium would
        #                                 otherwise snap borders/heights to 1.5x physical pixels (47.33px
        #                                 chips, blurred 1px borders) even under CDP's metrics override
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--remote-debugging-port=%d --force-device-scale-factor=1" % args.cdp_port

    import webview  # deferred so `python shell.py --help` and the tests don't need it

    settings = settings_store.load_settings()
    tools = tool_manifests.load_tools(Path(str(settings.get("tools_dir") or "")))

    bus = UiBus()
    api = ShellApi()
    model = SessionModel(settings, tools, emit=bus.push)
    bridge = None
    ticker = None
    if args.demo_state:
        load_demo_state(model)
    else:
        bridge = bridge_client.BridgeClient(int(settings["listen_port"]), int(settings["bridge_port"]), model.handle_osc)
        model.attach_bridge(bridge)
        ticker = Ticker(model.tick)

    width, height = _parse_size(args.size)
    window = webview.create_window(
        single_instance.WINDOW_TITLE,
        url=str(WEB_DIR / "index.html"),
        js_api=api,
        width=width,
        height=height,
        min_size=MIN_SIZE,
    )
    bus.attach(window.evaluate_js)

    def hwnd() -> int:
        try:
            return int(window.native.Handle.ToInt64())
        except Exception:
            return 0

    def request_quit() -> None:
        h = hwnd()
        if h:
            single_instance.post_close(h)

    api._bind(model=model, bus=bus, window=window, quit_cb=request_quit)
    # Dialog tools open their own native window (unchanged HTML) and confirm with a native yes/no.
    model.attach_dialogs(
        shell_dialogs.DialogHost(shell_dialogs.native_window, log=model.log),
        lambda title, message: bool(window.create_confirmation_dialog(title, message)),
    )

    def pick_save(title: str, directory: str, filename: str, file_types: tuple) -> str:
        # "Save to PC" after a host tool: the native Save As (pywebview's dialog has no title parameter).
        picked = window.create_file_dialog(webview.FileDialog.SAVE, directory=directory, save_filename=filename, file_types=file_types)
        return str(picked[0]) if picked else ""

    model.attach_save_dialog(pick_save)

    def on_shown() -> None:
        h = hwnd()
        if h:
            single_instance.force_foreground(h)
        if args.ready_file:
            try:
                Path(args.ready_file).write_text("hwnd=%d\npid=%d\n" % (h, os.getpid()), encoding="utf-8")
            except OSError:
                pass

    def on_closing() -> None:
        # Not on the pusher thread: stop the things that never touch the window first.
        model.genius.close()
        model.close_dialogs()
        if ticker is not None:
            ticker.stop()
        if bridge is not None:
            bridge.close()

    def on_closed() -> None:
        bus.stop()

    window.events.shown += on_shown
    window.events.closing += on_closing
    window.events.closed += on_closed

    bus.start()
    if ticker is not None:
        bridge.start()
        ticker.start()
        model.log("Studio Host initialized. Drop 'Live Actions Bridge.amxd' on an audio track in Live.")
    else:
        model.log("Demo state — no bridge connection.")
    single_instance.start_raise_watcher(hwnd)

    settings_store.APP_DATA.mkdir(parents=True, exist_ok=True)
    # A per-instance WebView2 profile: two isolated instances (LIVE_ACTIONS_INSTANCE) must not
    # share one user-data folder, and a --cdp-port run must not poison the normal profile.
    # private_mode=False: pywebview's default (True) runs WebView2 InPrivate, which throws away every
    # dialog's localStorage on exit -- Fill Forge keeps its own theme choice there. Nothing else in the
    # shell uses the browser's storage (settings live in settings.json), so this only lets that survive.
    profile = settings_store.APP_DATA / ("webview-cdp" if args.cdp_port else "webview")
    clear_http_cache(profile)
    webview.start(gui="edgechromium", private_mode=False, storage_path=str(profile))
    return 0



def clear_http_cache(profile: Path) -> None:
    """Drop the persistent WebView2 profile's HTTP + compiled-script caches before the window opens.
    With private_mode=False the profile outlives the app, and WebView2 kept serving an old
    components.js after an update (v1.7.0's model picker never appeared). Only the caches go:
    Local Storage (Fill Forge's theme) is kept."""
    import shutil
    for sub in ("Cache", "Code Cache"):
        shutil.rmtree(profile / "EBWebView" / "Default" / sub, ignore_errors=True)

if __name__ == "__main__":
    raise SystemExit(main())
