"""Host-runtime tool registry -- pure logic, no UI.

Tools with tool.json "runtime": "host" run in Python instead of going over OSC to
the Max bridge -- for work (HTTPS calls, ffmpeg, etc.) Max should never do or see.
Add an entry per host tool id; each handler is (fields, settings) -> dict with at
least an "ok" bool and a "message" string.

Lifted out of helper.py (slice 1 of the WebView2 redesign) so the Tk app and the
new shell share one registry.
"""

from __future__ import annotations

from typing import Any

import audio_sample
import tts_vocal

HOST_TOOLS: dict[str, Any] = {
    "tts-vocal": tts_vocal.run,
    "audio-sample": audio_sample.run,
}
