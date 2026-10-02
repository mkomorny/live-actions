"""Regression test for the bridge <-> app OSC chunked-reply protocol.

Added for the bridge-timeout-disconnect fix (v1.0.12): bridge/live-actions-
bridge.js's sendChunked() now splits any /live-actions/reply or
/live-actions/result payload over REPLY_CHUNK_LIMIT bytes into numbered
(key, seq, total, chunk) messages instead of shipping one oversized UDP
datagram -- Windows raises WSAEMSGSIZE on those instead of silently
truncating the way POSIX does, which used to kill BridgeClient's listener
thread permanently on the first large Genius/Pal reply.

This exercises the REAL Python reassembler (BridgeClient._reassemble /
_sweep_chunk_buffers in bridge_client.py) against a hand-mirrored copy of the
JS splitter's math. The splitter itself can't be imported here -- see
tools/detect-key/test-detect-key.mjs's header for why: the bridge file
assigns Max globals at top level under "use strict", which throws under
plain Node or any non-Max JS host. Keep _split_like_bridge and
REPLY_CHUNK_LIMIT in sync with sendChunked() in
bridge/live-actions-bridge.js if either side's chunking math ever changes.

Run from app\\:  python -m unittest test_osc_chunking
"""

from __future__ import annotations

import random
import time
import unittest
from unittest import mock

import bridge_client

REPLY_CHUNK_LIMIT = 4000  # mirrors bridge/live-actions-bridge.js


def _split_like_bridge(payload: str, key: str = "k") -> list[tuple]:
    """Mirrors sendChunked() in bridge/live-actions-bridge.js: a payload at
    or under the limit stays the original 2-arg (key, payload) shape; a
    larger one becomes several 4-arg (key, seq, total, chunk) messages."""
    if len(payload) <= REPLY_CHUNK_LIMIT:
        return [(key, payload)]
    total = -(-len(payload) // REPLY_CHUNK_LIMIT)  # ceil division
    return [
        (key, i, total, payload[i * REPLY_CHUNK_LIMIT : (i + 1) * REPLY_CHUNK_LIMIT])
        for i in range(total)
    ]


class OscChunkingTests(unittest.TestCase):
    def setUp(self) -> None:
        # Port 0 -- the OS picks a free ephemeral port, so this never
        # collides with a running copy of the app bound to the real 11925.
        self.client = bridge_client.BridgeClient(listen_port=0, bridge_port=0, on_message=lambda *a: None)
        self.addCleanup(self.client.close)

    def test_small_reply_is_unchanged_two_arg_shape(self) -> None:
        chunk = _split_like_bridge("short")[0]
        result = self.client._reassemble("/live-actions/reply", list(chunk))
        self.assertEqual(result, ("k", "short"))

    def test_large_reply_reassembles_in_order(self) -> None:
        payload = "x" * (REPLY_CHUNK_LIMIT * 3 + 1234)
        chunks = _split_like_bridge(payload)
        self.assertGreater(len(chunks), 1)
        result = None
        for c in chunks:
            result = self.client._reassemble("/live-actions/reply", list(c))
        self.assertEqual(result, ("k", payload))

    def test_reassembles_out_of_order(self) -> None:
        # UDP does not guarantee delivery order -- the last-arriving chunk
        # need not be the highest-numbered one.
        payload = "y" * (REPLY_CHUNK_LIMIT * 4 + 7)
        chunks = _split_like_bridge(payload)
        shuffled = chunks[:]
        random.Random(42).shuffle(shuffled)
        result = None
        for c in shuffled:
            result = self.client._reassemble("/live-actions/reply", list(c))
        self.assertEqual(result, ("k", payload))

    def test_exact_multiple_of_limit_has_no_empty_trailing_chunk(self) -> None:
        payload = "z" * (REPLY_CHUNK_LIMIT * 2)
        chunks = _split_like_bridge(payload)
        self.assertEqual(len(chunks), 2)
        result = None
        for c in chunks:
            result = self.client._reassemble("/live-actions/reply", list(c))
        self.assertEqual(result, ("k", payload))

    def test_incomplete_sequence_returns_none_until_final_chunk(self) -> None:
        payload = "w" * (REPLY_CHUNK_LIMIT * 2 + 5)
        chunks = _split_like_bridge(payload)
        self.assertEqual(len(chunks), 3)
        self.assertIsNone(self.client._reassemble("/live-actions/reply", list(chunks[0])))
        self.assertIsNone(self.client._reassemble("/live-actions/reply", list(chunks[1])))
        result = self.client._reassemble("/live-actions/reply", list(chunks[2]))
        self.assertEqual(result, ("k", payload))

    def test_two_pending_calls_do_not_cross_contaminate(self) -> None:
        # Two Genius calls in flight at once, each with its own req_id, must
        # reassemble independently even when their chunks interleave.
        payload_a = "a" * (REPLY_CHUNK_LIMIT * 2 + 3)
        payload_b = "b" * (REPLY_CHUNK_LIMIT * 2 + 9)
        chunks_a = _split_like_bridge(payload_a, key="req-a")
        chunks_b = _split_like_bridge(payload_b, key="req-b")
        self.assertEqual(len(chunks_a), len(chunks_b))  # both 3 chunks, so zip below is lossless

        result_a = result_b = None
        for a, b in zip(chunks_a, chunks_b):
            ra = self.client._reassemble("/live-actions/reply", list(a))
            rb = self.client._reassemble("/live-actions/reply", list(b))
            if ra is not None:
                result_a = ra
            if rb is not None:
                result_b = rb
        self.assertEqual(result_a, ("req-a", payload_a))
        self.assertEqual(result_b, ("req-b", payload_b))

    def test_result_and_reply_addresses_reassemble_independently(self) -> None:
        # /live-actions/result is chunked through the same sendChunked() as
        # /live-actions/reply but buffered under a separate address key.
        payload = "r" * (REPLY_CHUNK_LIMIT * 2 + 1)
        chunks = _split_like_bridge(payload)
        result_via_reply = result_via_result = None
        for c in chunks:
            result_via_reply = self.client._reassemble("/live-actions/reply", list(c))
        for c in chunks:
            result_via_result = self.client._reassemble("/live-actions/result", list(c))
        self.assertEqual(result_via_reply, ("k", payload))
        self.assertEqual(result_via_result, ("k", payload))

    def test_call_live_reports_empty_payload_clearly(self) -> None:
        # P4 A2: a reply that reassembles to the empty string (Max silently
        # dropped an oversized atom before udpsend ever saw it) must not
        # read as a generic JSON parse failure.
        def fake_send(address: str, *args) -> None:
            req_id = args[0]
            with self.client._pending_lock:
                pair = self.client._pending_calls.get(req_id)
            if pair:
                evt, res_box = pair
                res_box.append("")
                evt.set()

        with mock.patch.object(self.client, "send", side_effect=fake_send):
            result = self.client.call_live("read_set", {})
        self.assertFalse(result["ok"])
        self.assertIn("empty", result["error"].lower())
        self.assertIn("too large", result["error"].lower())

    def test_stale_incomplete_chunk_buffer_is_dropped(self) -> None:
        # A lost UDP datagram means the rest of a sequence never arrives.
        # The partial buffer must not sit in memory forever -- confirm
        # _sweep_chunk_buffers (called every _listen socket-timeout tick)
        # clears it once REPLY_CHUNK_TIMEOUT_S has passed.
        chunks = _split_like_bridge("s" * (REPLY_CHUNK_LIMIT * 2 + 1))
        self.assertIsNone(self.client._reassemble("/live-actions/reply", list(chunks[0])))
        self.assertEqual(len(self.client._chunk_buffers), 1)

        with mock.patch("time.time", return_value=time.time() + bridge_client.REPLY_CHUNK_TIMEOUT_S + 1):
            self.client._sweep_chunk_buffers()
        self.assertEqual(len(self.client._chunk_buffers), 0)
        self.assertEqual(self.client.dropped_packets, 1)


if __name__ == "__main__":
    unittest.main()
