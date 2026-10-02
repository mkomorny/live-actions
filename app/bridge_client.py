"""OSC bridge client for Live Actions Bridge.amxd — pure logic, no UI.

Lifted verbatim out of helper.py (slice 0 of the WebView2 redesign) so it can
be reused unchanged by both the Tk app and the new shell. Do not add any UI
dependency here (no tkinter, no pywebview) — the shell's UiBus wraps this.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
import time
import uuid
from typing import Any

BRIDGE_HOST = "127.0.0.1"
# A chunked /live-actions/reply or /live-actions/result whose remaining
# pieces never arrive (a lost UDP datagram) is dropped after this long, so a
# stuck partial can't sit in memory forever -- see BridgeClient._reassemble.
REPLY_CHUNK_TIMEOUT_S = 8.0


# ── OSC helpers ────────────────────────────────────────────────────────────────

def osc_string(s: str) -> bytes:
    raw = s.encode("utf-8") + b"\x00"
    pad = (4 - (len(raw) % 4)) % 4
    return raw + (b"\x00" * pad)


def pack_message(address: str, *args: Any) -> bytes:
    tags = ","
    payload = b""
    for arg in args:
        if isinstance(arg, bool):
            tags += "T" if arg else "F"
        elif isinstance(arg, int):
            tags += "i"
            payload += struct.pack(">i", arg)
        elif isinstance(arg, float):
            tags += "f"
            payload += struct.pack(">f", arg)
        else:
            tags += "s"
            payload += osc_string(str(arg))
    return osc_string(address) + osc_string(tags) + payload


def _read_osc_string(data: bytes, index: int) -> tuple[str, int]:
    end = data.find(b"\x00", index)
    if end < 0:
        return data[index:].decode("utf-8", "replace"), len(data)
    text = data[index:end].decode("utf-8", "replace")
    size = end - index + 1
    index = end + 1 + ((4 - (size % 4)) % 4)
    return text, index


def unpack_message(data: bytes) -> tuple[str, list[Any]]:
    address, index = _read_osc_string(data, 0)
    if index >= len(data):
        return address, []
    tags, index = _read_osc_string(data, index)
    args: list[Any] = []
    for tag in tags[1:]:
        if tag == "i":
            args.append(struct.unpack(">i", data[index : index + 4])[0])
            index += 4
        elif tag == "f":
            args.append(struct.unpack(">f", data[index : index + 4])[0])
            index += 4
        elif tag == "s":
            value, index = _read_osc_string(data, index)
            args.append(value)
        elif tag == "T":
            args.append(True)
        elif tag == "F":
            args.append(False)
    return address, args


# ── OSC Bridge Client ──────────────────────────────────────────────────────────

class BridgeClient:
    # Addresses whose payload can exceed one UDP datagram (Genius/Pal replies
    # off a real-sized Set) and so may arrive as numbered chunks from the
    # bridge's sendChunked() -- see bridge/live-actions-bridge.js. Reassembled
    # here before anything downstream ever sees them.
    _CHUNKED_ADDRESSES = ("/live-actions/reply", "/live-actions/result")

    def __init__(self, listen_port: int, bridge_port: int, on_message) -> None:
        self.on_message = on_message
        self.bridge_port = bridge_port
        self._listen_port = listen_port
        self._stop = threading.Event()
        self._sock = self._make_socket()
        self.last_pong = 0.0
        self.dropped_packets = 0
        self._pending_calls: dict[str, tuple[threading.Event, list[str]]] = {}
        self._pending_lock = threading.Lock()
        self._chunk_buffers: dict[tuple[str, str], dict[str, Any]] = {}
        self._chunk_lock = threading.Lock()
        self.thread = threading.Thread(target=self._run_supervised, name="live-actions-osc", daemon=True)

    def _make_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((BRIDGE_HOST, self._listen_port))
        sock.settimeout(0.4)
        return sock

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass

    def restart(self) -> None:
        """Tear down and rebuild the listener thread + socket from scratch.
        Used by the "Reset Bridge" button. A Python Thread object can't be
        restarted once its run() returns, so this builds a fresh one -- this
        is the one guaranteed way back to a working bridge that doesn't
        involve re-dropping the device in Live."""
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        with self._pending_lock:
            for evt, _res_box in self._pending_calls.values():
                evt.set()  # unblock any call_live() still waiting -- it will see an empty res_box
            self._pending_calls.clear()
        with self._chunk_lock:
            self._chunk_buffers.clear()
        self._stop = threading.Event()
        self._sock = self._make_socket()
        self.thread = threading.Thread(target=self._run_supervised, name="live-actions-osc", daemon=True)
        self.thread.start()

    def has_pending_calls(self) -> bool:
        with self._pending_lock:
            return bool(self._pending_calls)

    def send(self, address: str, *args: Any) -> None:
        packet = pack_message(address, *args)
        self._sock.sendto(packet, (BRIDGE_HOST, self.bridge_port))

    def call_live(self, action: str, params: dict[str, Any] | None = None, timeout: float = 6.0) -> dict[str, Any]:
        req_id = "req-" + str(uuid.uuid4())[:8]
        payload_str = json.dumps(params or {})
        evt = threading.Event()
        res_box: list[str] = []
        with self._pending_lock:
            self._pending_calls[req_id] = (evt, res_box)
        try:
            self.send("/live-actions/call", req_id, action, payload_str)
            if not evt.wait(timeout=timeout):
                return {"ok": False, "error": f"Live Actions Bridge timed out after {timeout}s on action: {action}"}
            if not res_box:
                return {"ok": False, "error": "Empty response from Live Actions Bridge"}
            if not res_box[0]:
                return {"ok": False, "error": "Bridge reply payload was empty (likely too large for one Max message)"}
            try:
                data = json.loads(res_box[0])
                return data if isinstance(data, dict) else {"ok": True, "result": data}
            except json.JSONDecodeError:
                return {"ok": False, "error": f"Invalid JSON reply: {res_box[0][:200]}"}
        finally:
            with self._pending_lock:
                self._pending_calls.pop(req_id, None)

    def _reassemble(self, address: str, args: list[Any]) -> tuple[str, str] | None:
        """Undo bridge-side sendChunked(). Small replies stay a 2-arg
        (key, payload) message, unchanged from before chunking existed. A
        large reply arrives as several 4-arg (key, seq, total, chunk)
        messages; this buffers them by (address, key) and returns the joined
        payload once the last one lands, or None while still waiting."""
        if len(args) == 2:
            return str(args[0]), str(args[1])
        if len(args) != 4:
            return None
        key = str(args[0])
        try:
            seq = int(args[1])
            total = int(args[2])
        except (TypeError, ValueError):
            return None
        chunk = str(args[3])
        if total <= 0 or not (0 <= seq < total):
            return None
        buf_key = (address, key)
        now = time.time()
        with self._chunk_lock:
            entry = self._chunk_buffers.get(buf_key)
            if entry is None or entry["total"] != total:
                entry = {"total": total, "parts": {}, "started": now}
                self._chunk_buffers[buf_key] = entry
            entry["parts"][seq] = chunk
            if len(entry["parts"]) < total:
                return None
            del self._chunk_buffers[buf_key]
            parts = entry["parts"]
        return key, "".join(parts[i] for i in range(total))

    def _sweep_chunk_buffers(self) -> None:
        now = time.time()
        with self._chunk_lock:
            stale = [k for k, v in self._chunk_buffers.items() if now - v["started"] > REPLY_CHUNK_TIMEOUT_S]
            for k in stale:
                del self._chunk_buffers[k]
        if stale:
            self.dropped_packets += len(stale)
            self.on_message("__error__", [f"dropped {len(stale)} incomplete chunked reply(ies) after timeout"])

    def _handle_datagram(self, address: str, args: list[Any]) -> None:
        if address in (
            "/live-actions/pong",
            "/live-actions/hello",
            "/live-actions/status",
            "/live-actions/tracks",
            "/live-actions/result",
            "/live-actions/reply",
        ):
            self.last_pong = time.time()

        if address in self._CHUNKED_ADDRESSES:
            reassembled = self._reassemble(address, args)
            if reassembled is None:
                return  # a chunk landed but the reply isn't complete yet
            key, payload_str = reassembled
            if address == "/live-actions/reply":
                with self._pending_lock:
                    pair = self._pending_calls.get(key)
                if pair:
                    evt, res_box = pair
                    res_box.append(payload_str)
                    evt.set()
            self.on_message(address, [key, payload_str])
            return

        self.on_message(address, args)

    def _listen(self) -> None:
        # Every branch below must swallow its error and keep looping --
        # this thread is the only thing that hears the bridge, and it used
        # to `break` on any OSError, permanently deafening the app on the
        # first oversized reply (Windows raises WSAEMSGSIZE instead of
        # silently truncating the way POSIX does). See App Changes Tracker
        # for the bridge-timeout-disconnect fix this replaced.
        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(65535)
            except socket.timeout:
                self._sweep_chunk_buffers()
                continue
            except OSError as exc:
                if self._stop.is_set():
                    return
                self.dropped_packets += 1
                self.on_message("__error__", [f"oversized or malformed packet dropped ({exc})"])
                continue

            try:
                address, args = unpack_message(data)
            except Exception as exc:
                self.dropped_packets += 1
                self.on_message("__error__", [f"unpack failed, packet dropped ({exc})"])
                continue

            try:
                self._handle_datagram(address, args)
            except Exception as exc:  # pragma: no cover - defense in depth
                self.dropped_packets += 1
                self.on_message("__error__", [f"handler error on {address} ({exc})"])

    def _run_supervised(self) -> None:
        # Belt-and-suspenders on top of _listen's own per-message guards: if
        # the loop ever exits without a real stop request, rebuild the
        # socket and keep serving instead of leaving the bridge permanently
        # deaf until the app is restarted.
        while not self._stop.is_set():
            try:
                self._listen()
            except Exception as exc:  # pragma: no cover - last-resort guard
                self.dropped_packets += 1
                self.on_message("__error__", [f"listener thread crashed, restarting ({exc})"])
            if self._stop.is_set():
                return
            self.on_message("__error__", ["listener exited unexpectedly -- restarting"])
            try:
                self._sock.close()
            except OSError:
                pass
            try:
                self._sock = self._make_socket()
            except OSError as exc:
                self.on_message("__error__", [f"listener restart failed, retrying in 1s ({exc})"])
                time.sleep(1.0)
