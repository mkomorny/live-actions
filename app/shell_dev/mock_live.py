"""A stand-in for the Max device (bridge/live-actions-bridge.js), for tests and
for driving the shell end to end when Ableton isn't running.

Speaks just enough of the real OSC protocol over real UDP loopback:
  /live-actions/ping    -> /live-actions/pong   {"on_track": true, "track": "Bridge"}
  /live-actions/status  -> /live-actions/status {"ok": true, name, tempo, tracks, time_signature, ...}
  /live-actions/tracks  -> /live-actions/tracks {"ok": true, tracks: [...]}   (10 tracks, "Bass" selected in Live)
  /live-actions/run     -> records (tool_id, payload) in .runs, then /live-actions/result ("ok"|"error", message)
                            (unless silent_runs; fail_runs makes it an error)
  /live-actions/reset   -> records in .resets
  /live-actions/call    -> records (action, params) in .calls, then /live-actions/reply (req_id, {"ok": true, ...})
                            (`call_replies[action]` overrides the reply: a dict, or a callable(params) -> dict)

`muted = True` stops all replies (simulates the device going away); `silent_runs`
suppresses only the /result reply. Not part of the shipped app.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # app/
import bridge_client as bc

TRACKS = [
    ("Drums", "midi"), ("Bass", "midi"), ("Chords", "midi"), ("Lead", "midi"),
    ("Vox", "audio"), ("Guitar DI", "audio"), ("FX Risers", "audio"),
    ("A  Reverb", "return"), ("B  Delay", "return"), ("Master", "master"),
]


def tracks_payload(selected_index: int = 1) -> dict[str, Any]:
    out = []
    for i, (name, kind) in enumerate(TRACKS):
        path = {"return": "live_set return_tracks %d", "master": "live_set master_track"}.get(kind, "live_set tracks %d")
        out.append({
            "key": "%s:%d" % (kind, i), "index": i, "id": str(100 + i), "name": name, "kind": kind,
            "path": path % i if "%d" in path else path, "devices": [], "selected_in_live": i == selected_index,
        })
    return {"ok": True, "selected_id": str(100 + selected_index), "tracks": out}


class MockLive:
    def __init__(self, listen_port: int, reply_port: int) -> None:
        self._reply_port = reply_port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((bc.BRIDGE_HOST, listen_port))
        self._sock.settimeout(0.2)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="mock-live")
        self.muted = False
        self.silent_runs = False
        self.fail_runs = False
        self.runs: list[tuple[str, dict[str, Any]]] = []
        self.resets = 0
        self.calls: list[tuple[str, dict[str, Any]]] = []      # /live-actions/call (Genius tool calls, dialog scans/plans)
        self.call_replies: dict[str, Any] = {}
        self.received: list[str] = []
        self.selected_index = 1

    def start(self) -> "MockLive":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass

    def _send(self, address: str, *args: Any) -> None:
        try:
            self._sock.sendto(bc.pack_message(address, *args), (bc.BRIDGE_HOST, self._reply_port))
        except OSError:
            pass

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                address, args = bc.unpack_message(data)
            except Exception:
                continue
            self.received.append(address)
            if address == "/live-actions/reset":
                self.resets += 1
                continue
            if address == "/live-actions/run" and len(args) == 2:
                try:
                    self.runs.append((str(args[0]), json.loads(str(args[1]))))
                except json.JSONDecodeError:
                    self.runs.append((str(args[0]), {}))
                if not self.muted and not self.silent_runs:
                    # real shape (bridge sendChunked): ("ok" | "error", message)
                    reply = ("error", "%s failed" % args[0]) if self.fail_runs else ("ok", "%s finished" % args[0])
                    threading.Timer(0.1, self._send, ("/live-actions/result",) + reply).start()
                continue
            if address == "/live-actions/call" and len(args) == 3 and not self.muted:
                try:
                    params = json.loads(str(args[2]))
                except json.JSONDecodeError:
                    params = {}
                self.calls.append((str(args[1]), params))
                reply = self.call_replies.get(str(args[1]))
                if callable(reply):
                    reply = reply(params)
                if reply is None:
                    reply = {"ok": True, "name": "Neon Nights 128.als", "tempo": 128.0, "track_count": len(TRACKS)}
                self._send("/live-actions/reply", str(args[0]), json.dumps(reply))
                continue
            if self.muted:
                continue
            if address == "/live-actions/ping":
                self._send("/live-actions/pong", json.dumps({"on_track": True, "track": "Bridge"}))
            elif address == "/live-actions/status":
                self._send("/live-actions/status", json.dumps({
                    "ok": True, "name": "Neon Nights 128.als", "tempo": 128.0, "tracks": len(TRACKS),
                    "time_signature": "4/4", "on_track": True, "host_track": "Bridge", "host_kind": "audio",
                }))
            elif address == "/live-actions/tracks":
                self._send("/live-actions/tracks", json.dumps(tracks_payload(self.selected_index)))
