"""Session model for the WebView2 shell -- pure logic, no UI import.

Everything the Tk app kept in widget variables (`_tracks`, `_track_vars`,
`_connected`, `_host_track`, `_log_lines`, `_open_tool`'s field values...) lives
here instead, behind one lock, so the page is only ever a *view* of Python
state. The model never touches a window: it pushes small JSON events through
the `emit` callable it was given (in the shell that is `UiBus.push`, which only
enqueues), and sends OSC through the `send` callable (`BridgeClient.send`).

Thread safety: the BridgeClient listener thread, the 1 s ticker thread,
pywebview's js_api worker threads and host-tool worker threads all call in.
Every mutation happens under `self._lock`, and `emit` is called *inside* the
lock -- it is a non-blocking queue put -- so the order events reach the page is
the order the state actually changed in.

Event shapes (all plain JSON):
  {"type": "patch", "patch": {<snapshot keys to overwrite>}}
  {"type": "log",   "line":  [time, direction, text]}
  {"type": "genius", "op": ...}   the chat (see shell_genius.py for its ops)
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable

import host_tools
import settings_store
import shell_dialog_tools
import shell_genius
import shell_launcher
import shell_confirm
import shell_placement
import shell_prefs
import tool_manifests

PING_EVERY_S = 1.0
OFFLINE_AFTER_S = 4.0
RESULT_WAIT_S = 1.8          # how long a bridge run may stay silent before we warn
DEFAULT_THEME = "risograph-art-studio"
LOG_LIMIT = 1000
KIND_TAGS = {"midi": "MIDI", "audio": "AUD", "return": "RET", "master": "MST"}
DEMO_TICKER = "Ready · OSC bridge on 127.0.0.1"
OFFLINE_TICKER = "Bridge offline — drop 'Live Actions Bridge.amxd' on an audio track in Live."


# ── Tool catalogue (manifests -> what the page renders) ───────────────────────

def _field_spec(field: dict[str, Any], settings: dict[str, Any], stored: dict[str, Any]) -> dict[str, Any]:
    """One manifest field, resolved the way helper._open_tool_screen resolves it:
    tts_profiles-backed selects are filled from Settings, a select with nothing
    to pick from degrades to a text box, and a saved per-tool preference beats
    the manifest default."""
    fid = str(field["id"])
    ftype = str(field.get("type") or "text")
    options: list[str] = []
    if ftype == "select":
        if str(field.get("optionsSource") or "") == "tts_profiles":
            options = [str(p.get("name") or "") for p in (settings.get("tts_profiles") or []) if p.get("name")]
        else:
            options = [str(o) for o in (field.get("options") or [])]
        if not options:
            ftype = "text"
    default = field.get("default")
    if fid in stored:
        default = stored[fid]
    if ftype == "select" and not (default and str(default) in options):
        default = options[0] if options else ""
    return {
        "id": fid,
        "label": str(field.get("label") or fid),
        "type": ftype,
        "default": "" if default is None else str(default),
        "hint": str(field.get("hint") or ""),
        "options": options or None,
        "showIf": field.get("showIf") if isinstance(field.get("showIf"), dict) else None,
        "filetypes": field.get("filetypes") if isinstance(field.get("filetypes"), list) else None,
    }


def build_catalog(tools: list[dict[str, Any]], settings: dict[str, Any]) -> list[dict[str, Any]]:
    prefs = settings.get("tool_prefs") or {}
    out: list[dict[str, Any]] = []
    for tool in tools:
        if tool.get("enabled") is False:
            continue
        stored = prefs.get(str(tool.get("id") or ""), {})
        fields = [
            _field_spec(f, settings, stored if isinstance(stored, dict) else {})
            for f in (tool.get("fields") or [])
            if isinstance(f, dict) and f.get("id")
        ]
        out.append({
            "id": str(tool["id"]),
            "name": str(tool.get("name") or tool["id"]),
            "description": str(tool.get("description") or ""),
            "accent": str(tool.get("accent") or ""),
            "scope": str(tool.get("scope") or ""),
            "ui": str(tool.get("ui") or ""),
            "runtime": str(tool.get("runtime") or ""),
            "runLabel": str(tool.get("runLabel") or ""),
            "fields": fields,
            "fieldCount": len(fields),
        })
    return out


def _matches_show_if(cond: Any, values: dict[str, Any]) -> bool:
    """Same rule as helper._matches_show_if -- used server-side only to decide
    whether a hidden field still travels with a Run (it does, like the Tk app:
    every field var is sent regardless of visibility)."""
    if not isinstance(cond, dict):
        return True
    value = str(values.get(str(cond.get("field") or ""), "")).strip()
    allowed = cond.get("in")
    if isinstance(allowed, list) and value not in [str(a) for a in allowed]:
        return False
    denied = cond.get("notIn")
    if isinstance(denied, list) and value in [str(d) for d in denied]:
        return False
    return True


# ── The model ────────────────────────────────────────────────────────────────

class SessionModel:
    def __init__(
        self,
        settings: dict[str, Any],
        tools: list[dict[str, Any]],
        *,
        send: Callable[..., None] | None = None,
        emit: Callable[[dict[str, Any]], None] | None = None,
        bridge: Any = None,
        save_settings: Callable[[dict[str, Any]], None] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._lock = threading.RLock()
        self._settings = settings
        self._tools = tools
        self._send = send or (lambda *_a, **_k: None)
        self._emit = emit or (lambda _e: None)
        self._bridge = bridge
        self._save_settings = save_settings or settings_store.save_settings
        self._clock = clock

        self._connected = False
        self._host_track = ""
        self._set: dict[str, Any] = self._offline_set()
        self._tracks: list[dict[str, Any]] = []
        self._known_keys: set[str] = set()
        self._targets: set[str] = set()
        self._log: list[list[str]] = []
        self._ticker = OFFLINE_TICKER
        self._runs: dict[str, dict[str, str]] = {}
        self._host_running = False
        self._wait_id = 0
        self._wait_seen: set[int] = set()
        self._pending_run = ""
        self._demo = False
        # The three webview-dialog tools; None until the shell attaches a window host (see attach_dialogs).
        self.dialogs: shell_dialog_tools.DialogTools | None = None
        # Host tools' "Add to Live Set" question (the page's slot-picker modal) and "Save to PC" dialog.
        self.placement = shell_placement.SlotPicker(self._lock, self._patch)
        # "May I spend your API credit?" -- asked before a Genius tool that bills the user.
        self.confirm = shell_confirm.ConfirmPicker(self._lock, self._patch)
        self._pick_save: Callable[..., str] | None = None
        self._closing = False
        # The Genius chat shares this lock and emit so its events are ordered with everything else
        # the page receives, and so a snapshot can never miss one (see snapshot_and).
        self.genius = shell_genius.GeniusSession(
            lock=self._lock,
            emit=lambda evt: self._emit(evt),
            get_settings=lambda: self._settings,
            live_line=self.live_line,
            get_bridge=lambda: self._bridge,
            save_settings=lambda data: self._save_settings(data),
            confirm=self.confirm.ask,
        )
        # Preferences mutate `settings` IN PLACE (same dict the Genius session reads), one validated,
        # persisted change per call; the page only ever receives a masked snapshot.
        self.prefs = shell_prefs.PrefsService(
            lock=self._lock,
            settings=self._settings,
            save=lambda data: self._save_settings(data),
            log=self.log,
            hooks={"tools": self.reload_tools, "catalog": self.refresh_catalog, "genius": self.genius.announce_agent,
                   "notice": self.genius.notice},
        )

    def attach_bridge(self, bridge: Any) -> None:
        """The BridgeClient needs the model's handle_osc as its callback, so the two
        are built in that order and joined here."""
        self._bridge = bridge
        self._send = bridge.send

    def attach_dialogs(self, host: Any, confirm: Callable[[str, str], bool], spawn: Callable[..., None] | None = None) -> None:
        """Give the dialog tools a window host (shell_dialogs.DialogHost) and a blocking yes/no `confirm`."""
        kw = {"spawn": spawn} if spawn else {}
        self.dialogs = shell_dialog_tools.DialogTools(self, host, confirm, **kw)

    def attach_save_dialog(self, pick_save: Callable[..., str]) -> None:
        """`pick_save(title=, directory=, filename=, file_types=)` -> a path, or "" when cancelled (the shell passes
        pywebview's native Save As)."""
        self._pick_save = pick_save

    def close_dialogs(self) -> None:
        """The window is going away: end every open dialog / question quietly (nothing may be pushed to the page)."""
        with self._lock:
            self._closing = True
        self.placement.cancel(quiet=True)
        self.confirm.cancel(quiet=True)
        if self.dialogs is not None:
            self.dialogs.shutdown()

    # -- snapshot ------------------------------------------------------------

    @staticmethod
    def _offline_set() -> dict[str, Any]:
        return {"name": "(Waiting for Live Set...)", "bpm": "—", "sig": "—", "tracks": 0}

    def _track_view(self) -> list[dict[str, Any]]:
        return [
            {
                "key": t["key"],
                "n": i + 1,
                "name": str(t.get("name") or t["key"]),
                "kind": KIND_TAGS.get(str(t.get("kind") or "audio").lower(), "AUD"),
                "devices": [str(d) for d in (t.get("devices") or [])],
                "selectedInLive": bool(t.get("selected_in_live")),
            }
            for i, t in enumerate(self._tracks)
        ]

    def reload_tools(self) -> None:
        """Re-read the tool manifests after Preferences changed the tools folder."""
        from pathlib import Path
        tools = tool_manifests.load_tools(Path(str(self._settings.get("tools_dir") or "")))
        with self._lock:
            self._tools = tools
            self._patch(tools=build_catalog(self._tools, self._settings))
            self._runs = {k: v for k, v in self._runs.items() if any(t["id"] == k for t in tools)}
        self.log("Tools folder reloaded: %d tool(s)." % len(tools))

    def refresh_catalog(self) -> None:
        """Rebuild the page's catalog from the CURRENT settings without re-reading manifests: a TTS profile added,
        renamed or removed in Preferences must show up in the TTS Vocal tool's Profile dropdown at once (Tk filled
        it each time the tool opened). Typed field values live page-side in LA.vals, so they survive the redraw."""
        with self._lock:
            self._patch(tools=build_catalog(self._tools, self._settings))

    def live_line(self) -> str:
        """The one-line Live status handed to Genius's system prompt (same wording as the Tk app)."""
        with self._lock:
            if not self._connected:
                return "Live offline"
            return "Live connected: %s @ %s" % (self._set.get("name", ""), self._set.get("bpm", ""))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "instance": settings_store.INSTANCE,
                "demo": self._demo,
                "theme": str(self._settings.get("theme") or DEFAULT_THEME),
                "connected": self._connected,
                "hostTrack": self._host_track,
                "set": dict(self._set),
                "tracks": self._track_view(),
                "targets": self.target_keys(),
                "tools": build_catalog(self._tools, self._settings),
                "log": [list(l) for l in self._log],
                "ticker": self._ticker,
                "runs": {k: dict(v) for k, v in self._runs.items()},
                "genius": self.genius.snapshot(),
                "prefs": self.prefs.snapshot(),
                "placement": self.placement.snapshot(),
                "confirm": self.confirm.snapshot(),
                "ports": {
                    "listen": int(self._settings.get("listen_port") or 0),
                    "bridge": int(self._settings.get("bridge_port") or 0),
                },
            }

    def snapshot_and(self, then: Callable[[], None]) -> dict[str, Any]:
        """Snapshot and run `then` under one hold of the lock, so no event can be
        emitted between the two (UiBus.open_gate relies on this)."""
        with self._lock:
            snap = self.snapshot()
            then()
            return snap

    def _patch(self, **patch: Any) -> None:
        self._emit({"type": "patch", "patch": patch})

    # -- log -----------------------------------------------------------------

    def log(self, text: str, direction: str = "•") -> None:
        with self._lock:
            line = [time.strftime("%H:%M:%S", time.localtime(self._clock())), direction, str(text)]
            self._log.append(line)
            del self._log[:-LOG_LIMIT]
            self._emit({"type": "log", "line": line})

    def log_text(self) -> str:
        with self._lock:
            return "\n".join(f"{t}  {d} {x}" for t, d, x in self._log)

    def _set_ticker(self, text: str) -> None:
        self._ticker = text
        self._patch(ticker=text)

    # -- targets (ticked tracks) ---------------------------------------------

    def target_keys(self) -> list[str]:
        with self._lock:
            return [t["key"] for t in self._tracks if t["key"] in self._targets]

    def selected_tracks(self) -> list[dict[str, Any]]:
        with self._lock:
            return [t for t in self._tracks if t["key"] in self._targets]

    def toggle_track(self, key: str) -> list[str]:
        with self._lock:
            if key in {t["key"] for t in self._tracks}:
                self._targets.symmetric_difference_update({key})
            return self._emit_targets()

    def set_all(self, value: bool) -> list[str]:
        with self._lock:
            self._targets = {t["key"] for t in self._tracks} if value else set()
            return self._emit_targets()

    def use_live_selection(self) -> list[str]:
        with self._lock:
            if not self._tracks:
                self._send("/live-actions/tracks")
                self.log("Requested track hierarchy from Live.", "→")
                return self.target_keys()
            self._targets = {t["key"] for t in self._tracks if t.get("selected_in_live")}
            return self._emit_targets()

    def _emit_targets(self) -> list[str]:
        keys = self.target_keys()
        self._patch(targets=keys)
        return keys

    # -- connection ----------------------------------------------------------

    def _set_connected(self, connected: bool) -> None:
        if connected == self._connected:
            return
        self._connected = connected
        if connected:
            self._set_ticker("Connected to Live. Bridge is active on %s." % (self._host_track or "track"))
            self._patch(connected=True, hostTrack=self._host_track)
            self.log("Connected to Live Actions Bridge in Ableton.")
            self._send("/live-actions/status")
            self._send("/live-actions/tracks")
        else:
            self._host_track = ""
            self._set = self._offline_set()
            self._set_ticker(OFFLINE_TICKER)
            self._patch(connected=False, hostTrack="", set=dict(self._set))
            self.log("Bridge connection lost.")

    def tick(self) -> None:
        """Called once per PING_EVERY_S by the shell's ticker thread."""
        try:
            self._send("/live-actions/ping")
        except OSError:
            pass
        with self._lock:
            last_pong = float(getattr(self._bridge, "last_pong", 0.0) or 0.0)
            silent = (self._clock() - last_pong) > OFFLINE_AFTER_S
            if silent and self._bridge is not None and getattr(self._bridge, "has_pending_calls", lambda: False)():
                # A call_live() is in flight: the bridge may just be busy
                # building a big reply. Let that call's own timeout decide.
                silent = False
            if silent and self._connected:
                self._set_connected(False)

    def ping(self) -> None:
        self._send("/live-actions/ping")
        self.log("OSC Ping sent to bridge (127.0.0.1:%s)." % self._settings.get("bridge_port"), "→")

    def request_status(self) -> None:
        self._send("/live-actions/status")
        self.log("Requested Live Set status.", "→")

    def request_tracks(self) -> None:
        self._send("/live-actions/tracks")
        self.log("Requested track hierarchy from Live.", "→")

    def reset_bridge(self) -> dict[str, Any]:
        """Rebuild our listener socket AND ask the Max side to re-arm -- either
        half can fail independently, so both run every time."""
        self.log("Resetting Live Actions Bridge connection…")
        if self._bridge is not None:
            try:
                self._bridge.restart()
            except OSError as exc:
                self.log("✗ Bridge reset failed: %s" % exc)
                return {"ok": False, "message": "Could not rebuild the bridge socket: %s" % exc}
        self._send("/live-actions/reset")
        self.log("Bridge socket rebuilt; sent reset to the Max device.", "→")
        return {"ok": True, "message": "Bridge reset."}

    # -- inbound OSC (BridgeClient listener thread) --------------------------

    @staticmethod
    def _parse_json(args: list[Any]) -> dict[str, Any] | None:
        if not args:
            return None
        raw = args[0]
        if isinstance(raw, dict):
            return raw
        try:
            data = json.loads(str(raw))
        except (TypeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def handle_osc(self, address: str, args: list[Any]) -> None:
        with self._lock:
            if address == "__error__":
                self.log("⚠ Bridge transport: " + " ".join(str(a) for a in args))
                return
            if address in ("/live-actions/pong", "/live-actions/hello"):
                payload = self._parse_json(args)
                if payload:
                    self._remember_host(payload)
                self._set_connected(True)
                return
            if address == "/live-actions/status":
                self._apply_status(args)
                return
            if address == "/live-actions/tracks":
                self._apply_tracks(args)
                return
            if address == "/live-actions/result":
                self._wait_seen.add(self._wait_id)
                # The bridge sends (status, message) with status "ok" or "error" (sendChunked in
                # live-actions-bridge.js). The Tk app showed both as "Done"; a failed tool must not.
                failed = bool(args) and str(args[0]).lower() == "error"
                msg = " ".join(str(a) for a in (args[1:] if len(args) > 1 else args))
                if failed:
                    self.log("✗ Failed: " + msg, "←")
                    self._set_ticker("⚠ Action failed: " + msg[:60])
                    self._finish_run(self._pending_run, "error", "⚠  " + (msg[:200] or "The tool reported an error."))
                else:
                    self.log("✓ Done: " + msg, "←")
                    self._set_ticker("✓ Action completed: " + msg[:60])
                    self._finish_run(self._pending_run, "done", "✓ Done! " + msg[:200])
                self._pending_run = ""
                return
            if address == "/live-actions/api/reply":
                self.log("API Reply: " + " ".join(str(a) for a in args), "←")

    def _remember_host(self, data: dict[str, Any]) -> None:
        if data.get("on_track") and data.get("track"):
            self._host_track = str(data.get("track") or "")
        elif data.get("host_track"):
            self._host_track = str(data.get("host_track") or "")
        if self._connected and self._host_track:
            self._patch(hostTrack=self._host_track)

    def _apply_status(self, args: list[Any]) -> None:
        data = self._parse_json(args)
        if data is None:
            return
        if not data.get("ok"):
            self._set = dict(self._offline_set(), name=str(data.get("error") or "Live API initializing"))
            self._patch(set=dict(self._set))
            return
        self._remember_host(data)
        tempo = data.get("tempo")
        tracks = data.get("tracks")
        self._set = {
            "name": str(data.get("name") or "Untitled Live Set"),
            "bpm": ("%.2f" % float(tempo)) if tempo is not None else "—",
            "sig": str(data.get("time_signature") or "4/4"),
            "tracks": tracks if tracks is not None else 0,
        }
        self._patch(set=dict(self._set))
        # Genius binds custom instructions per Live Set, so it needs the name as
        # soon as Live reports it. Imported lazily and guarded: shell_model must
        # keep working (and stay unit-testable) without the Genius import chain.
        try:
            import genius_client

            genius_client.remember_live_set(self._set["name"])
        except Exception:
            pass
        self.log("Set Status: %s @ %s BPM (%s tracks)." % (self._set["name"], self._set["bpm"], self._set["tracks"]), "←")

    def _apply_tracks(self, args: list[Any]) -> None:
        data = self._parse_json(args)
        if not data or not data.get("ok"):
            return
        self._tracks = [t for t in (data.get("tracks") or []) if isinstance(t, dict) and t.get("key")]
        keys = {t["key"] for t in self._tracks}
        known_before = self._known_keys & keys
        self._targets &= keys
        had_any = bool(self._targets)
        for t in self._tracks:
            if t["key"] not in known_before and not had_any and t.get("selected_in_live"):
                self._targets.add(t["key"])
        self._known_keys = keys
        self._patch(tracks=self._track_view(), targets=self.target_keys())
        self.log("Synchronized %d tracks from Live." % len(self._tracks), "←")

    # -- running a tool ------------------------------------------------------

    def _finish_run(self, tool_id: str, state: str, message: str) -> None:
        if tool_id:
            self._runs[tool_id] = {"state": state, "message": message}
            self._patch(runs={tool_id: dict(self._runs[tool_id])})

    def _save_prefs(self, tool_id: str, fields: dict[str, Any]) -> None:
        prefs = dict(self._settings.get("tool_prefs") or {})
        prefs[tool_id] = dict(fields)
        self._settings["tool_prefs"] = prefs
        try:
            self._save_settings(self._settings)
        except OSError as exc:
            self.log("Could not save tool preferences: %s" % exc)

    def _tool(self, tool_id: str) -> dict[str, Any] | None:
        return next((t for t in self._tools if str(t.get("id")) == tool_id), None)

    def run_tool(self, tool_id: str, fields: dict[str, Any] | None) -> dict[str, Any]:
        """Start a tool. Returns immediately with {ok, message}; the outcome
        arrives later as a `runs` patch. Never blocks on the bridge or ffmpeg."""
        fields = {str(k): "" if v is None else str(v) for k, v in (fields or {}).items()}
        with self._lock:
            tool = self._tool(tool_id)
            if tool is None:
                return {"ok": False, "message": "Unknown tool: %s" % tool_id}
            name = str(tool.get("name") or tool_id)
            if str(tool.get("ui") or "") == "webview":
                if self.dialogs is None:
                    msg = "⚠  %s opens its own dialog window, which is not available in this session." % name
                    self._finish_run(tool_id, "error", msg)
                    return {"ok": False, "message": msg}
                return self.dialogs.open(tool, name)
            if str(tool.get("runtime") or "live") == "host":
                return self._run_host(tool, name, fields)
            return self._run_bridge(tool, name, fields)

    def _run_bridge(self, tool: dict[str, Any], name: str, fields: dict[str, Any]) -> dict[str, Any]:
        tool_id = str(tool["id"])
        if not self._connected:
            msg = "⚠  Bridge offline — start Live and drop the bridge device."
            self._finish_run(tool_id, "error", msg)
            return {"ok": False, "message": msg}
        set_scope = str(tool.get("scope") or "") == "set"
        targets = self.selected_tracks()
        if not set_scope and not targets:
            msg = "⚠  No tracks selected — tick tracks on the left first."
            self._finish_run(tool_id, "error", msg)
            return {"ok": False, "message": msg}
        payload = {
            "tracks": [{"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")} for t in targets],
            "fields": fields,
        }
        self._save_prefs(tool_id, fields)
        if set_scope:
            line, msg = "Executing %s across the entire Set." % name, "Running %s on full set…" % name
        else:
            line, msg = "Executing %s on %d track(s)." % (name, len(targets)), "Running %s on %d track(s)…" % (name, len(targets))
        self._dispatch_run(tool_id, name, payload, line, msg)
        return {"ok": True, "message": msg}

    def _dispatch_run(self, tool_id: str, name: str, payload: dict[str, Any], log_line: str, message: str, wait_s: float | None = None) -> None:
        """Send one /live-actions/run and start waiting for its result. Caller holds the lock.
        /live-actions/result carries no tool id, so a result can only ever be attributed to the most
        recent run; an earlier one still waiting is closed out rather than left "running" forever."""
        if self._pending_run and self._pending_run != tool_id and self._runs.get(self._pending_run, {}).get("state") == "running":
            self._finish_run(self._pending_run, "idle", "Superseded by a newer run.")
        self._send("/live-actions/run", tool_id, json.dumps(payload))
        self.log(log_line, "→")
        self._pending_run = tool_id
        self._finish_run(tool_id, "running", message)
        self._await_result(tool_id, name, wait_s)

    def _await_result(self, tool_id: str, name: str, wait_s: float | None = None) -> None:
        self._wait_id += 1
        wait_id = self._wait_id

        def check() -> None:
            with self._lock:
                if wait_id != self._wait_id or wait_id in self._wait_seen:
                    return
                if not self._connected:
                    self._finish_run(tool_id, "error", "⚠  Bridge offline — no reply received.")
                    self.log("No response from %s — Live Actions Bridge is offline." % name)
                else:
                    self._finish_run(tool_id, "error", "⚠  No reply from Live — try re-dropping the bridge device.")
                    self.log("No reply from %s. Re-drop the bridge device in Live if needed." % name)

        timer = threading.Timer(RESULT_WAIT_S if wait_s is None else wait_s, check)
        timer.daemon = True
        timer.start()

    def _run_host(self, tool: dict[str, Any], name: str, fields: dict[str, Any]) -> dict[str, Any]:
        tool_id = str(tool["id"])
        handler = host_tools.HOST_TOOLS.get(tool_id)
        if handler is None:
            msg = "⚠  No host handler registered for this tool."
            self.log("✗ %s: no host handler registered." % name)
            self._finish_run(tool_id, "error", msg)
            return {"ok": False, "message": msg}
        if self._host_running:
            return {"ok": False, "message": "Already running — wait for the current run to finish."}
        self._host_running = True
        settings = dict(self._settings)
        self._save_prefs(tool_id, fields)
        destination = str(fields.get("destination") or "").strip().lower()
        placing = destination == "add to live set"
        save_pc = destination == "save to pc"
        connected = self._connected
        targets = self.selected_tracks() if placing else []
        self.log("Running %s (host)." % name)
        msg = "Running %s…" % name
        self._finish_run(tool_id, "running", msg)

        def worker() -> None:
            try:
                result = handler(fields, settings)
            except Exception as exc:  # host handlers must never take the app down
                result = {"ok": False, "message": "Unexpected error: %s" % exc}
            if result.get("ok") and placing and not self._closing:
                result = self._place(tool_id, name, result, targets, connected)
            with self._lock:
                self._host_running = False
                if self._closing:
                    return
                ok = bool(result.get("ok"))
                message = str(result.get("message") or ("Done." if ok else "Failed."))
                path = result.get("path")
                if ok:
                    self.log("✓ %s: %s" % (name, message))
                    if path:
                        self.log("Saved: %s" % path)
                    shown = "✓ " + message + (("\n" + str(path)) if path else "")
                else:
                    self.log("✗ %s: %s" % (name, message))
                    shown = "⚠  " + message
                self._finish_run(tool_id, "done" if ok else "error", shown)
            if ok and path and save_pc:
                self._offer_save_as(tool_id, name, message, str(path))     # after the lock: a native dialog blocks

        threading.Thread(target=worker, daemon=True, name="host-tool").start()
        return {"ok": True, "message": msg}

    def _place(self, tool_id: str, name: str, result: dict[str, Any], targets: list[dict[str, Any]], connected: bool) -> dict[str, Any]:
        """"Add to Live Set" (worker thread): validate, ask the page for a slot, create the clip."""
        def call_live(action: str, params: dict[str, Any]) -> dict[str, Any]:
            bridge = self._bridge
            if bridge is None:
                return {"ok": False, "error": "No bridge connection."}
            return bridge.call_live(action, params)

        def ask_slot(track: dict[str, Any], slots: list[dict[str, Any]]) -> int | None:
            where = str(track.get("name") or track.get("key") or "track")
            with self._lock:
                self._finish_run(tool_id, "running", "Waiting for you to choose a clip slot on “%s”…" % where)
            return self.placement.ask(name, track, slots)

        try:
            return shell_placement.place_generated_file(result, targets, connected, call_live, ask_slot)
        except Exception as exc:  # the file exists either way; say what did not happen
            result["message"] = str(result.get("message") or "Generated.") + " Placement failed: %s" % exc
            result["placed"] = False
            return result

    def _offer_save_as(self, tool_id: str, name: str, message: str, path: str) -> None:
        """"Save to PC" (worker thread, model lock NOT held): native Save As, then copy."""
        pick = self._pick_save
        if pick is None:
            self.log("Save As is not available in this session — file remains at " + path)
            return
        try:
            res = shell_placement.offer_save_as(path, name, pick)
        except Exception as exc:
            self.log("✗ Save As failed: %s" % exc)
            return
        with self._lock:
            if self._closing:
                return
            status = res["status"]
            if status == "cancelled":
                self.log("Save As canceled — file remains at " + path)
            elif status == "error":
                self.log("✗ Could not save to that location: %s" % res["error"])
                self._finish_run(tool_id, "done", "✓ %s\n%s\n⚠  Could not save a copy there: %s" % (message, path, res["error"]))
            else:                                       # "saved", or "same" (the file already lives there)
                self.log("Saved copy to: %s" % res["dest"])
                self._finish_run(tool_id, "done", "✓ %s\n%s" % (message, res["dest"]))


# ── Demo state (the preview's mock set) ──────────────────────────────────────

DEMO_TRACKS = [
    ("Drums", "midi", ["Drum Rack", "Glue Compressor"]),
    ("Bass", "midi", ["Wavetable", "Saturator"]),
    ("Chords", "midi", ["Operator", "Chorus-Ensemble"]),
    ("Lead", "midi", ["Drift", "Echo"]),
    ("Vox", "audio", ["Compressor", "EQ Eight"]),
    ("Guitar DI", "audio", ["Amp", "Cabinet"]),
    ("FX Risers", "audio", []),
    ("A  Reverb", "return", ["Hybrid Reverb"]),
    ("B  Delay", "return", ["Echo"]),
    ("Master", "master", ["Limiter"]),
]


def load_demo_state(model: SessionModel) -> None:
    """Fill `model` with exactly what previews/redesign-round/shared/shared.js mocks
    (Neon Nights 128.als, 10 tracks, tracks 2-4 ticked, connected), so a screenshot
    of the real shell can be pixel-compared with the reference shots. No sockets."""
    with model._lock:
        model._connected = True
        model._host_track = "Bridge"
        model._set = {"name": "Neon Nights 128.als", "bpm": "128.00", "sig": "4/4", "tracks": len(DEMO_TRACKS)}
        model._tracks = [
            {"key": "%s:%d" % (kind, i), "index": i, "name": name, "kind": kind, "devices": devs, "selected_in_live": i == 1}
            for i, (name, kind, devs) in enumerate(DEMO_TRACKS)
        ]
        model._known_keys = {t["key"] for t in model._tracks}
        model._targets = {"midi:1", "midi:2", "midi:3"}
        model._ticker = DEMO_TICKER
        model._demo = True
        model.genius.load_demo()
        model.prefs.load_demo()
