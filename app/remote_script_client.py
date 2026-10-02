"""TCP client for the LiveActionsRS Remote Script ("engine E2") — pure logic, no UI.

Sits alongside bridge_client.py and follows the same rule stated there: no UI
dependency (no tkinter, no pywebview), so both the Tk app and the WebView2 shell
can use it unchanged.

Why a second client at all: the OSC bridge in bridge_client.py talks to Max for
Live, whose LiveAPI has no Browser class, so Live's library panel is unreachable
from it (probed live in v1.0.34). Engine E2 is a MIDI Remote Script — real
CPython inside Live — and is the only place Application.browser exists.

Transport differs from the bridge on purpose. BridgeClient carries a whole
chunk-reassembly subsystem because OSC/UDP datagrams are size-capped; a browser
listing is exactly the payload that stresses it hardest. This speaks
newline-delimited JSON over TCP, so a reply of any size arrives intact and none
of that machinery is needed.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any

import live_version

RS_HOST = "127.0.0.1"

# How long a ping result is trusted before the engine is considered stale. Same
# 15s window build_system_prompt already applies to the bridge's last_pong, so
# "online" means the same thing for both engines.
ONLINE_WINDOW_S = 15.0

# Browsing a cold, deep folder (a large Pack, a Samples tree) is genuinely slow
# the first time; the script caches per folder, so only the first call pays it.
DEFAULT_TIMEOUT_S = 12.0
CONNECT_TIMEOUT_S = 1.5


class RemoteScriptClient:
    """One reused TCP connection to LiveActionsRS, guarded by a lock.

    Requests are serialized rather than multiplexed. The browser is a single
    shared object inside Live and every call is short, so a request pipeline
    would add concurrency bugs without buying throughput.
    """

    def __init__(self, port: int, host: str = RS_HOST) -> None:
        self.port = int(port)
        self.host = host
        self.last_pong = 0.0
        self.last_error = ""
        self._sock: socket.socket | None = None
        self._buf = b""
        self._lock = threading.Lock()
        self._req_id = 0

    # ── connection ────────────────────────────────────────────────────────

    def _connect_locked(self) -> socket.socket:
        if self._sock is not None:
            return self._sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CONNECT_TIMEOUT_S)
        try:
            sock.connect((self.host, self.port))
        except OSError:
            # Close before re-raising: a failed connect still leaves a real fd
            # open, and the engine being down is the common path (the user
            # hasn't enabled the Control Surface), so this would leak on every
            # single call rather than rarely.
            try:
                sock.close()
            except OSError:
                pass
            raise
        sock.settimeout(DEFAULT_TIMEOUT_S)
        self._sock = sock
        self._buf = b""
        return sock

    def _drop_locked(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._buf = b""

    def close(self) -> None:
        with self._lock:
            self._drop_locked()

    # ── request / reply ───────────────────────────────────────────────────

    def _read_line_locked(self, sock: socket.socket) -> bytes:
        while b"\n" not in self._buf:
            chunk = sock.recv(65536)
            if not chunk:
                raise ConnectionError("Remote Script closed the connection")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return line

    def call(
        self,
        action: str,
        params: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> dict[str, Any]:
        """Send one action, return the decoded reply.

        Never raises: a dead engine is an ordinary, expected state (the user may
        simply not have enabled the Control Surface yet), so failures come back
        as {"ok": False, "error": ...} for the caller to surface verbatim.
        """
        with self._lock:
            self._req_id += 1
            request = {"id": self._req_id, "action": action, "params": params or {}}
            payload = json.dumps(request).encode("utf-8") + b"\n"

            # One retry: Live may have dropped a socket that has been idle since
            # the last call, and reconnecting is cheaper than surfacing a
            # spurious "engine offline" to the user.
            for attempt in (0, 1):
                try:
                    sock = self._connect_locked()
                    sock.settimeout(timeout)
                    sock.sendall(payload)
                    line = self._read_line_locked(sock)
                except (OSError, ConnectionError) as exc:
                    self._drop_locked()
                    if attempt == 0:
                        continue
                    self.last_error = str(exc)
                    return {
                        "ok": False,
                        "error": (
                            f"Live Actions browser engine (LiveActionsRS) not reachable on "
                            f"port {self.port}: {exc}. In Live: Preferences > Link/Tempo/MIDI > "
                            f"Control Surface, select \"LiveActionsRS\"."
                        ),
                    }

                try:
                    data = json.loads(line.decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    self.last_error = str(exc)
                    return {"ok": False, "error": f"Invalid JSON from Remote Script: {exc}"}

                if not isinstance(data, dict):
                    return {"ok": True, "result": data}
                self.last_pong = time.time()
                self.last_error = ""
                return data

        return {"ok": False, "error": "unreachable"}

    # ── status ────────────────────────────────────────────────────────────

    def ping(self, timeout: float = CONNECT_TIMEOUT_S) -> dict[str, Any]:
        return self.call("ping", {}, timeout=timeout)

    def online(self) -> bool:
        """True when the engine answered recently.

        Mirrors the bridge's freshness check rather than probing, so callers on
        a hot path (every Genius turn builds a system prompt) stay cheap.
        """
        return bool(self.last_pong) and (time.time() - self.last_pong) < ONLINE_WINDOW_S

    def probe(self) -> bool:
        """Actively refresh online state. Use on a timer or before a decision
        that depends on capability, not inside a tight loop."""
        reply = self.ping()
        if reply.get("live_version"):
            live_version.record(reply["live_version"])
        return bool(reply.get("ok"))
