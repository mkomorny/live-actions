"""Live Actions — Genius AI chat with Live control.

Talks to the user's chosen AI provider (xAI, OpenAI, Gemini or Anthropic) with
live_* tools plus library_read/search. Tools run on the Live Actions OSC Bridge.
This app is independent of Producer Pal; its Producer_Pal.amxd device is not used.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

import agent_registry
import custom_instructions
import genius_db
import live_version
import remote_script_client
import settings_store
import tts_vocal
from live_numbering import ModelArgError, args_from_model, live_track_label, model_view, mv_json

# ── Constants ──────────────────────────────────────────────────────────────────

MAX_INDEX_CHARS = 16_000
MAX_SKILL_CHARS = 10_000
MAX_LIBRARY_CHARS = 20_000
MAX_TOOL_LOOPS = 40          # max function-call rounds before forcing a reply -- a broad multi-track
                             # ask ("fix the whole mix") can legitimately need many rounds; the last
                             # round always forces a text-only reply instead of raising (v1.0.43)
MAX_AGENT_CHARS = 8_000      # cap on a persona file's body when it replaces the stock persona
CONTEXT_DIR_NAME = "context"

# Genius's own skill + fallback library index ship inside the app, not as a
# separately configurable folder — Genius never has to pull them from anywhere else.
GENIUS_DIR = Path(__file__).resolve().parent / "genius"


# ── Engine E2: Live's browser, via the LiveActionsRS Remote Script ─────────────
#
# The OSC bridge runs inside Max for Live, whose LiveAPI has no Browser class --
# `live_app browser` came back exists:false / 0 children when probed live in
# v1.0.34. Application.browser only exists in a MIDI Remote Script, so browser
# work (packs, presets, plug-ins, audition) goes over this second connection.
#
# Kept as a module-level singleton keyed by port rather than threaded through
# call_live_tool(): every caller of that function (helper.py, shell_genius.py)
# would otherwise need a new argument for a capability most tools never touch.

# Tools that cannot work without engine E2. Withheld from the model entirely
# when the engine is offline: a tool the model can't call is a capability it
# can't promise, which is more reliable than asking it not to in the prompt.
E2_TOOLS = frozenset({"live_browse", "live_load_browser_item", "live_preview_browser_item"})

# Tools that bill the user's own API key. Withheld when no TTS profile is
# configured -- same reasoning as E2_TOOLS: a tool the model can't call is a
# capability it can't promise. Unlike E2 this needs no probe, because the
# answer is entirely local ("has the user saved a profile?").
TTS_TOOLS = frozenset({"live_tts_vocal"})

# Tool calls that must be approved before they run, keyed by the `kind` the
# front-end's confirm dialog groups them under (and remembers per session).
CONFIRM_KINDS: dict[str, str] = {"live_tts_vocal": "tts_spend"}


def tts_available(settings: dict[str, Any] | None = None) -> bool:
    """Is there at least one saved TTS profile to generate with?"""
    profiles = (settings or {}).get("tts_profiles") or []
    return isinstance(profiles, list) and len(profiles) > 0


_RS_CLIENTS: dict[int, remote_script_client.RemoteScriptClient] = {}
_RS_LOCK = threading.Lock()

# An engine that has never answered is re-probed at most this often, so a Genius
# turn taking place while the Remote Script is disabled doesn't pay a connect
# timeout on every single tool call.
RS_PROBE_INTERVAL_S = 10.0
_RS_LAST_PROBE: dict[int, float] = {}


def rs_port(settings: dict[str, Any] | None = None) -> int:
    return _int((settings or {}).get("rs_port"), 11926)


def rs_client(settings: dict[str, Any] | None = None) -> remote_script_client.RemoteScriptClient:
    port = rs_port(settings)
    with _RS_LOCK:
        client = _RS_CLIENTS.get(port)
        if client is None:
            client = remote_script_client.RemoteScriptClient(port)
            _RS_CLIENTS[port] = client
        return client


def rs_online(settings: dict[str, Any] | None = None, probe: bool = True) -> bool:
    """Is the browser engine answering right now?

    Drives both which tools Genius is offered and what the system prompt claims
    it can do, so it must reflect reality rather than configuration. `probe`
    is rate-limited; pass probe=False on a hot path to use the cached answer.
    """
    client = rs_client(settings)
    if client.online():
        return True
    if not probe:
        return False
    port = rs_port(settings)
    now = time.time()
    with _RS_LOCK:
        if now - _RS_LAST_PROBE.get(port, 0.0) < RS_PROBE_INTERVAL_S:
            return False
        _RS_LAST_PROBE[port] = now
    return client.probe()


# ── Which Live Set is open ────────────────────────────────────────────────────
#
# Custom instructions are bound per Live Set, so the prompt builder and the
# live_custom_instructions tool both need the Set's name. Rather than thread a
# new argument through every Genius entry point in both front-ends, the front-
# ends report the name here whenever Live tells them it changed. Falls back to
# parsing live_line, whose format both front-ends already share, so a front-end
# that forgets to report still resolves the right preset.

_CURRENT_SET_NAME = ""


def remember_live_set(name: str | None) -> None:
    """Called by the shell / Tk app when Live reports the open Set."""
    global _CURRENT_SET_NAME
    _CURRENT_SET_NAME = str(name or "").strip()


def current_live_set(live_line: str | None = None) -> str:
    if _CURRENT_SET_NAME:
        return _CURRENT_SET_NAME
    # "Live connected: <name> @ <bpm>" -- see shell_model.live_line / helper.py.
    text = str(live_line or "")
    if text.startswith("Live connected:"):
        rest = text[len("Live connected:"):].strip()
        return rest.rsplit(" @ ", 1)[0].strip() if " @ " in rest else rest
    return ""


def live_capabilities(settings: dict[str, Any] | None = None) -> set[str]:
    """Capability set for recipe gating (app/recipes.py).

    Recomputed per call rather than cached at import: the user can enable the
    Control Surface without restarting the app, and a recipe reported as
    unavailable forever after that would be wrong.
    """
    import recipes

    caps = set(recipes.AVAILABLE_CAPABILITIES)
    if rs_online(settings):
        caps.add("browser")
    return caps


def _rs_offline_message(settings: dict[str, Any] | None = None) -> str:
    return (
        "Live's browser is not reachable: the Live Actions browser engine "
        f"(LiveActionsRS) isn't answering on port {rs_port(settings)}. In Live, open "
        "Preferences > Link/Tempo/MIDI and set an unused Control Surface slot to "
        '"LiveActionsRS", then restart Live. Until then, browser/preset/plug-in '
        "actions are unavailable -- disk sample search (live_find_samples) still works."
    )


def _int(value: Any, default: int = 0) -> int:
    """Best-effort int coercion for tool-call args. The model can send any
    JSON type for a numeric field (a non-numeric string, null, a bool); this
    degrades to `default` instead of raising out of call_live_tool."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _float(value: Any, default: float = 0.0) -> float:
    """Best-effort float coercion for tool-call args -- see _int."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ── Live Actions Native Tool Definitions (sent to xAI as "tools") ───────────────

def _tool(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    props = properties or {}
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": props,
            "required": required or [],
            "additionalProperties": False,
        },
    }


LIVE_TOOLS: list[dict[str, Any]] = [
    _tool("live_connect", "Connect / ping Ableton through Live Actions Bridge. Call first when the user wants Live work. Returns set name, tempo, scale, track/scene counts."),
    _tool(
        "live_read_set",
        "Read Live Set globals plus optional detail. Default include is tracks+scenes.",
        {
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": ["tracks", "scenes", "routings", "mixer", "color", "locators", "*"]},
                "description": "tracks, scenes, routings, mixer, color, locators, or * for all.",
            }
        },
    ),
    _tool(
        "live_update_set",
        "Update Live Set tempo, time signature, scale, or locators (create/delete/rename).",
        {
            "tempo": {"type": "number", "description": "BPM 20-999."},
            "time_signature": {"type": "string", "description": "N/D e.g. 4/4."},
            "scale": {"type": "string", "description": "Root + name e.g. 'D Dorian'. Empty string disables scale."},
            "locator_operation": {"type": "string", "enum": ["create", "delete", "rename"]},
            "locator_time": {"type": "string", "description": "Bar|beat (1|1) or beats."},
            "locator_name": {"type": "string"},
            "locator_id": {"type": "string", "description": "locator-0 style id."},
            "metronome": {"type": "boolean", "description": "Turn metronome on (true) or off (false)."},
            "clip_trigger_quantization": {"type": "integer", "description": "Global clip launch quantization (0=None, 1=8 Bars, 2=4 Bars, 3=2 Bars, 4=1 Bar, 5=1/2, 6=1/2T, 7=1/4, 8=1/4T, 9=1/8, 10=1/8T, 11=1/16, 12=1/16T, 13=1/32)."},
        },
    ),
    _tool(
        "live_read_track",
        "Read one track (midi/audio/return/master): mixer, devices, session clips, arrangement clips, drum map, routings.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": ["session-clips", "arrangement-clips", "notes", "devices", "drum-map", "routings", "available-routings", "mixer", "color", "*"]},
            },
        },
        ["track_number"],
    ),
    _tool(
        "live_update_track",
        "Update track name, color, mute/solo/arm, volume/pan, send, monitoring, routing.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given. This selects the target track; use `name` to rename it."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "name": {"type": "string"},
            "color": {"type": "string"},
            "volume": {"type": "number", "description": "0-1 fader (0.85 ≈ 0 dB)."},
            "gain_db": {"type": "number"},
            "pan": {"type": "number"},
            "mute": {"type": "boolean"},
            "solo": {"type": "boolean"},
            "arm": {"type": "boolean"},
            "send": {"type": "string", "description": "Return letter A/B/C…"},
            "send_gain": {"type": "number", "description": "0-1 send amount."},
            "send_gain_db": {"type": "number"},
            "monitoring_state": {"type": "string", "enum": ["in", "auto", "off"]},
            "monitoring": {"type": "string", "enum": ["in", "auto", "off"], "description": "Track monitoring state (in, auto, off)."},
            "delay_ms": {"type": "number", "description": "Track delay compensation offset in milliseconds."},
            "crossfade_assign": {"type": "string", "enum": ["none", "a", "b"], "description": "Master crossfader assignment."},
            "input_routing_type": {"type": "string"},
            "input_routing_channel": {"type": "string"},
            "output_routing_type": {"type": "string"},
            "output_routing_channel": {"type": "string"},
        },
        ["track_number"],
    ),
    _tool(
        "live_create_track",
        "Create midi, audio, or return track(s).",
        {
            "type": {"type": "string", "enum": ["midi", "audio", "return"]},
            "name": {"type": "string", "description": "Name, or comma-separated for count>1."},
            "color": {"type": "string"},
            "position_number": {"type": "integer", "minimum": 1, "description": "Insert position, exactly as Live would number the new track (e.g. 1 = before today's track 1). Omit to append at the end."},
            "count": {"type": "integer"},
            "mute": {"type": "boolean"},
            "solo": {"type": "boolean"},
            "arm": {"type": "boolean"},
        },
        ["type"],
    ),
    _tool(
        "live_read_scene",
        "Read a scene and its clips.",
        {
            "scene_number": {"type": "integer", "minimum": 1},
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": ["clips", "notes", "color", "*"]},
            },
        },
        ["scene_number"],
    ),
    _tool(
        "live_update_scene",
        "Update scene name, color, or tempo.",
        {
            "scene_number": {"type": "integer", "minimum": 1},
            "scene_numbers": {"type": "array", "items": {"type": "integer", "minimum": 1}, "description": "Scene numbers to update, exactly as Live shows them, e.g. [1,3]. Updates one scene when scene_number is given instead."},
            "name": {"type": "string"},
            "color": {"type": "string"},
            "tempo": {"type": "number"},
        },
    ),
    _tool(
        "live_create_scene",
        "Create empty scene(s) or capture playing session clips.",
        {
            "scene_number": {"type": "integer", "minimum": 1},
            "count": {"type": "integer"},
            "name": {"type": "string"},
            "color": {"type": "string"},
            "capture": {"type": "boolean", "description": "Copy currently playing session clips."},
        },
    ),
    _tool(
        "live_read_clip",
        "Read a session clip: notes, timing, warp/sample for audio.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number."},
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": ["notes", "timing", "sample", "warp", "color", "*"]},
            },
        },
    ),
    _tool(
        "live_update_clip",
        "Update clip name/color/mute/loop/length, write notes, quantize, or audio warp/pitch.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number."},
            "name": {"type": "string"},
            "color": {"type": "string"},
            "mute": {"type": "boolean"},
            "loop": {"type": "boolean"},
            "length_beats": {"type": "number"},
            "length": {"type": "string", "description": "e.g. 4bar or n/4."},
            "notes": {"type": "string", "description": "Pal-style notes (v100 n/16 C1 1|1) or JSON text of a note array."},
            "replace": {"type": "boolean"},
            "quantize": {"type": "number"},
            "warping": {"type": "boolean"},
            "pitch_shift": {"type": "number"},
            "pitch": {"type": "number", "description": "Audio clip pitch transposition in semitones (-48 to +48)."},
            "gain": {"type": "number", "description": "Audio clip gain (dB or float value)."},
            "launch_mode": {"type": "string", "enum": ["trigger", "gate", "toggle", "repeat"], "description": "Clip launch mode."},
            "launch_quantization": {"type": "string", "description": "global, none, 8_bars, 4_bars, 2_bars, 1_bar, 1/2, 1/4, 1/8, 1/16, 1/32..."},
            "velocity_amount": {"type": "number", "description": "Velocity sensitivity (0.0 to 1.0)."},
            "warp_mode": {"type": "string", "enum": ["beats", "tones", "texture", "re-pitch", "complex", "complex_pro"], "description": "Audio warp mode."},
            "ram_mode": {"type": "boolean", "description": "Audio clip RAM mode toggle."},
            "legato": {"type": "boolean", "description": "Legato (continuous) launch mode."},
            "start_marker": {"type": "number", "description": "Start marker in beats."},
            "end_marker": {"type": "number", "description": "End marker in beats."},
            "fade_in_start": {"type": "number", "description": "Fade-in start position in beats (audio clips)."},
            "fade_in_end": {"type": "number", "description": "Fade-in end position in beats (audio clips)."},
            "fade_out_start": {"type": "number", "description": "Fade-out start position in beats (audio clips)."},
            "fade_out_end": {"type": "number", "description": "Fade-out end position in beats (audio clips)."},
            "follow_action_a": {"type": "string", "enum": ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"], "description": "Follow action A."},
            "follow_action_b": {"type": "string", "enum": ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"], "description": "Follow action B."},
            "follow_action_chance": {"type": "number", "description": "Probability of follow action A (0.0–1.0)."},
            "follow_action_time": {"type": "number", "description": "Follow action trigger time in beats."},
            "follow_action_enabled": {"type": "boolean", "description": "Whether follow actions are active."},
        },
    ),
    _tool(
        "live_create_clip",
        "Create a MIDI or audio clip in Session (slot) or Arrangement (arrangement_start). Audio: pass sample_file.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number."},
            "arrangement_start": {"type": "string", "description": "Bar|beat in arrangement."},
            "name": {"type": "string"},
            "color": {"type": "string"},
            "length_beats": {"type": "number"},
            "length": {"type": "string"},
            "looping": {"type": "boolean"},
            "notes": {"type": "string", "description": "MIDI notes after create (Pal-style string or JSON array text)."},
            "sample_file": {"type": "string", "description": "Absolute audio path for an audio clip."},
            "auto": {"type": "string", "enum": ["play-clip", "play-scene"]},
        },
    ),
    _tool(
        "live_write_notes",
        "Write MIDI notes into a session clip (creates the clip if empty). Prefer this for drum patterns, chords, bass, melody.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1},
            "name": {"type": "string"},
            "length_beats": {"type": "number"},
            "replace": {"type": "boolean"},
            "notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pitch": {"type": "integer"},
                        "start_time": {"type": "number"},
                        "duration": {"type": "number"},
                        "velocity": {"type": "integer"},
                        "mute": {"type": "boolean"},
                        "probability": {"type": "number", "description": "Note probability 0.0–1.0 (Live 12 probabilistic notes)."},
                        "velocity_deviation": {"type": "integer", "description": "Velocity deviation –127 to +127."},
                    },
                    "required": ["pitch", "start_time", "duration", "velocity"],
                    "additionalProperties": False,
                },
            },
        },
        ["track_number", "slot_number", "notes"],
    ),
    _tool(
        "live_read_device",
        "Read a device, rack chain, or drum pad (native or already-present VST/AU). Path examples: t1/d1, t2/d1/c1, t1/d1/pC1.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "device_number": {"type": "integer", "minimum": 1},
            "path": {"type": "string", "description": "t1/d1 or t1/d1/pC1."},
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": ["params", "param-values", "chains", "drum-pads", "drum-map", "*"]},
            },
            "param_search": {"type": "string"},
        },
    ),
    _tool(
        "live_update_device",
        "Set device params (display units) on a native device or an already-present VST/AU, rename, or mute/solo chains. To load an audio file into a Simpler that is on a track, set a param named 'sample' to an absolute file path (from live_tts_vocal, live_audio_op, live_find_samples or live_library). Simpler only -- Sampler has no sample-loading method in the API. The system prompt states whether this running Live build supports SimplerDevice.replace_sample -- trust that over any assumption. If a sample does not load, the response's params_skipped/error names the real reason (read-back verified); do not guess it was a version limit. To load a sample onto a Drum Rack pad, "
        "set a param named 'p<note>/sample' (e.g. 'pC1/sample') to an absolute file path from live_find_samples "
        "or live_library -- this creates the pad's chain and a Simpler on it if needed, then loads the file; "
        "check params_skipped in the response for the real reason if a pad did not take.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "device_number": {"type": "integer", "minimum": 1},
            "path": {"type": "string"},
            "name": {"type": "string"},
            "is_active": {"type": "boolean"},
            "is_collapsed": {"type": "boolean", "description": "Collapse or expand the device in Detail View."},
            "mute": {"type": "boolean"},
            "solo": {"type": "boolean"},
            "params": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {
                            "type": "string",
                            "description": "The value AS DISPLAYED in Live, including its unit/symbol, e.g. '40 %', '-30 dB', '200 ms', '1.5 kHz', '10:1'. This is matched against Live's own displayed number. A bare number with no unit (e.g. '0.4' or '40') is instead applied as the RAW 0-1 (or enum-index) parameter value, which is almost never what you want for a dB/%/ms/Hz-style knob -- use it only when you actually mean a raw or enum-index value.",
                        },
                    },
                    "required": ["name", "value"],
                    "additionalProperties": False,
                },
            },
        },
    ),
    _tool(
        "live_create_device",
        "Insert a native Live device onto a track by name (Drum Rack, Drift, Reverb, Scale, Simpler…), Live 12.3+ only. Omit device_name to list insertable native device names. For VST/AU, Max for Live devices, or browser presets, see the system prompt's Live control section for whether the browser engine is online. "
        "Bundle the sample into the same call via params: 'sample' = an absolute file path loads it into a new Simpler; for a Drum Rack, 'p<note>/sample' does the same per pad (see live_update_device).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "device_name": {"type": "string", "description": "e.g. Drum Rack, Drift, Reverb, EQ Eight, Scale, Arpeggiator."},
            "params": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {
                            "type": "string",
                            "description": "The value AS DISPLAYED in Live, including its unit/symbol, e.g. '40 %', '-30 dB', '200 ms', '1.5 kHz', '10:1'. This is matched against Live's own displayed number. A bare number with no unit (e.g. '0.4' or '40') is instead applied as the RAW 0-1 (or enum-index) parameter value, which is almost never what you want for a dB/%/ms/Hz-style knob -- use it only when you actually mean a raw or enum-index value.",
                        },
                    },
                    "additionalProperties": False,
                },
            },
        },
        ["track_number"],
    ),
    _tool(
        "live_delete",
        "Delete a track, session clip, arrangement clip, scene, or device.",
        {
            "type": {"type": "string", "enum": ["track", "clip", "arrangement_clip", "scene", "device", "drum-pad"]},
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "slot_number": {"type": "integer", "minimum": 1},
            "clip_number": {"type": "integer", "minimum": 1, "description": "For arrangement_clip: number in track.arrangement_clips, exactly as Live shows it."},
            "scene_number": {"type": "integer", "minimum": 1},
            "device_number": {"type": "integer", "minimum": 1},
            "path": {"type": "string"},
        },
        ["type"],
    ),
    _tool(
        "live_duplicate",
        "Duplicate a track, scene, session clip, or duplicate a session clip into the Arrangement timeline.",
        {
            "type": {"type": "string", "enum": ["track", "clip", "scene", "device"]},
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1},
            "to_slot": {"type": "integer"},
            "destination_time": {"type": "number", "description": "Beat position in Arrangement timeline. When provided for type=clip, duplicates the Session clip directly into the Arrangement."},
            "to_track_number": {"type": "integer", "minimum": 1, "description": "Optional target track number when duplicating to Arrangement."},
            "scene_number": {"type": "integer", "minimum": 1},
        },
        ["type"],
    ),
    _tool(
        "live_select",
        "Show/select a track, scene, clip slot, or device. Switch Session/Arrangement. Open a plugin window already on a track.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "scene_number": {"type": "integer", "minimum": 1},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number to select, exactly as Live shows it -- combine with track_number."},
            "path": {"type": "string"},
            "device_path": {"type": "string"},
            "view": {"type": "string", "enum": ["session", "arrangement"]},
            "open_plugin_window": {"type": "boolean"},
        },
    ),
    _tool(
        "live_playback",
        "Transport and launch: play/stop arrangement, fire clip/scene, loop region, stop session clips.",
        {
            "action": {
                "type": "string",
                "enum": [
                    "play", "stop", "continue", "play-arrangement", "update-arrangement",
                    "fire_clip", "play-session-clips", "stop_clip", "stop-session-clips",
                    "stop-all-session-clips", "fire_scene", "play-scene",
                ],
            },
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1},
            "scene_number": {"type": "integer", "minimum": 1},
            "start_time": {"type": "string"},
            "start_locator": {"type": "string"},
            "loop": {"type": "boolean"},
            "loop_start": {"type": "string"},
            "loop_end": {"type": "string"},
        },
        ["action"],
    ),
    _tool(
        "live_record_to_arrangement",
        "Record a Session scene's performance into the Arrangement timeline (arms Song's Arrangement Record, fires the "
        "scene, so it plays and records the same as pressing Record then launching a scene by hand). Different from "
        "live_create_scene capture=true, which only snapshots currently playing clips into a NEW SESSION scene — this "
        "one writes into the Arrangement. Never blocks: with duration_beats it schedules an auto-stop and returns "
        "immediately with the estimated wait; without it, recording keeps going until you call this again with "
        "op='stop'.",
        {
            "op": {"type": "string", "enum": ["start", "stop"], "description": "Default start."},
            "scene_number": {"type": "integer", "minimum": 1, "description": "Required for op=start."},
            "duration_beats": {"type": "number", "description": "Auto-stop after this many beats at the Set's current tempo. Omit to leave it running until op=stop."},
            "stop_playback": {"type": "boolean", "description": "op=stop only: also stop the transport, not just disarm recording."},
        },
    ),
    _tool(
        "live_library",
        "Search the user's disk Samples folder, and -- when the browser engine is online -- Live's own browser as well. "
        "listPlugins returns real installed VST/VST3 when the engine is online, and an empty list when it isn't. "
        "listTags/listCategories return the category list. For walking the browser tree rather than searching it, use live_browse.",
        {
            "action": {"type": "string", "enum": ["search", "searchBatch", "listTags", "listCategories", "listPlugins"]},
            "query": {"type": "string"},
            "kind": {"type": "string", "enum": ["audio", "midi", "preset", "device-group", "m4l-device", "plugin", "folder"]},
            "category": {"type": "string"},
            "limit": {"type": "number"},
            "queries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"label": {"type": "string"}, "query": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
        },
    ),
    _tool(
        "live_custom_instructions",
        "The user's own standing instructions for how you should answer, saved per Live Set. "
        "action='read' shows what is currently active — use it if the user asks what your instructions are. "
        "action='add' appends ONE new instruction, and you may only call it when the user has explicitly asked "
        "you to remember/save a preference. Never call add on your own initiative, and never to record "
        "musical facts about the project (that is live_context). After adding, tell the user exactly what "
        "you added, word for word. You cannot delete instructions: the only removal is `replaces`, which you "
        "pass ONLY when the new instruction directly contradicts an existing one — quote that existing line in "
        "`replaces` and say in your reply which line was replaced and why.",
        {
            "action": {"type": "string", "enum": ["read", "add"], "description": "Default read."},
            "text": {"type": "string", "description": "action=add: the single instruction to append, in the user's own terms."},
            "replaces": {
                "type": "string",
                "description": "action=add only, and only on a direct contradiction: the existing instruction line this one supersedes, quoted as closely as you can.",
            },
        },
    ),
    _tool(
        "live_browse",
        "Walk Live's own browser tree -- the library panel on the left of Live (Sounds, Drums, Instruments, "
        "Audio Effects, MIDI Effects, Max for Live, Plug-ins, Clips, Samples, User Library, Packs). "
        "Call with no category to list the categories. Call with a category and an optional path (a list of "
        "folder names, outermost first) to list what is inside that folder. Each item reports is_folder and "
        "is_loadable; only is_loadable items can be given to live_load_browser_item. Folder listings are cached, "
        "so pass refresh=true after the user installs a pack or saves a preset.",
        {
            "category": {
                "type": "string",
                "description": "sounds, drums, instruments, audio_effects, midi_effects, max_for_live, plugins, clips, samples, user_library, current_project, packs. Omit to list categories.",
            },
            "path": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Folder names from the category root, outermost first, e.g. [\"Bass\", \"Sub Bass\"]. Omit for the category's top level.",
            },
            "refresh": {"type": "boolean", "description": "Bypass the cached listing and re-read from Live."},
            "offset": {"type": "integer", "minimum": 0, "description": "Skip this many items. Big folders are paged (the Samples category has tens of thousands of entries); the reply says the true total."},
            "limit": {"type": "integer", "minimum": 1, "description": "How many items to return (default 500). Prefer searching over paging through a huge folder."},
        },
    ),
    _tool(
        "live_load_browser_item",
        "Load a browser item -- a .adv/.adg preset, a native device, a Max for Live device, a VST/VST3 plug-in, "
        "or a sample -- onto a track, exactly as dragging it from Live's browser would. Identify it either by "
        "category + path (preferred: use the path live_browse or live_library search returned) or by uri. "
        "The item must be is_loadable. Loading appends to the target track's device chain.",
        {
            "category": {"type": "string", "description": "Browser category, as in live_browse."},
            "path": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Folder names then the item name, e.g. [\"Bass\", \"Sub Bass\"].",
            },
            "uri": {"type": "string", "description": "Browser URI, if you have one instead of a path."},
            "track_number": {"type": "integer", "minimum": 1, "description": "1-based Live track. Omit to use the currently selected track."},
        },
    ),
    _tool(
        "live_preview_browser_item",
        "Audition a browser item through Live's preview channel without adding it to the Set -- the same as "
        "clicking it in Live's browser. Use op='stop' to stop playback. Good for checking a sample or preset "
        "before committing to live_load_browser_item.",
        {
            "op": {"type": "string", "enum": ["play", "stop"], "description": "Default play."},
            "category": {"type": "string", "description": "Browser category, as in live_browse."},
            "path": {"type": "array", "items": {"type": "string"}, "description": "Folder names then the item name."},
            "uri": {"type": "string", "description": "Browser URI, if you have one instead of a path."},
        },
    ),
    _tool(
        "live_tts_vocal",
        "Generate a spoken vocal WAV from text with the user's saved TTS profile (Cartesia / OpenAI / xAI), "
        "on the desktop host -- the audio never crosses into Max. Returns the absolute file path, which "
        "live_update_device (a 'sample' param, into a Simpler), live_create_device or live_create_clip "
        "(sample_file) can then load into Live. "
        "TWO THINGS TO BE HONEST WITH THE USER ABOUT: (1) these are SPEECH models -- they do not sing. "
        "You can change speed, language and voice, but not pitch or melody. If the user asks for singing, "
        "say it will come back spoken and offer live_audio_op pitch-time as the nearest thing; do not "
        "promise a sung result. (2) Length is a RESULT, not a setting -- it follows from how much text you "
        "send and the speed. Never claim you generated 'a 10-second vocal'; read durationSec from the "
        "response and say what it actually is. To hit an exact length, generate first, then trim or pad "
        "with live_audio_op. "
        "This call bills the user's own API key, so the app asks them to approve it first; if they decline, "
        "say so and stop rather than trying again.",
        {
            "text": {"type": "string", "description": "What to say. Up to 2000 characters."},
            "profile": {"type": "string", "description": "Saved profile name. Omit to use the first saved profile. If the user has pinned a profile in Settings > TTS Vocal Profiles, that one is used regardless of this field -- naming a different one is refused, not substituted; see the system prompt's Live control section for whether one is pinned right now."},
            "voice": {"type": "string", "description": "Voice ID override. Omit to use the profile's own voice. Ignored while a profile is pinned (see 'profile' above) -- pinning exists to guarantee one exact voice, so it also blocks this override."},
            "speed": {"type": "string", "description": "e.g. '1.0'. Cartesia accepts 0.6-1.5. Omit for the profile default."},
            "language": {"type": "string", "description": "e.g. 'en', 'es'. Affects pronunciation."},
        },
        ["text"],
    ),
    _tool(
        "live_audio_op",
        "Edit or generate an audio file on disk with ffmpeg: trim, auto-trim silence, fades, gain, normalize, "
        "convert/resample, reverse, pitch & time-stretch, echo, chorus, tremolo, vibrato, EQ, bitcrush, and "
        "tone/noise/silence generators. Writes a NEW file and returns its path -- the input is never "
        "overwritten. Call it with no 'operation' to list every operation with its field names and defaults; "
        "do that before guessing a field name. Use 'trim' to hit an exact length and 'pitch-time' to shift "
        "pitch or tempo (this is the closest thing to making a spoken vocal musical).",
        {
            "operation": {"type": "string", "description": "Operation id, e.g. trim, autotrim, fades, gain, normalize, convert, reverse, pitch-time, echo, chorus, tremolo, vibrato, eq, bitcrush, tone, noise, silence. Omit to list them all."},
            "input_file": {"type": "string", "description": "Absolute path to the source audio. Not needed by the tone/noise/silence generators."},
            "params": {
                "type": "object",
                "description": "Operation fields by their own names, e.g. {\"start\": \"0\", \"end\": \"10\"} for trim, {\"semitones\": \"-3\"} for pitch-time. Any field left out uses its default.",
                "additionalProperties": {"type": "string"},
            },
        },
    ),
    _tool(
        "live_find_samples",
        "Search the user's Samples folder on disk for one-shots (kicks, snares, 808s, hats).",
        {
            "query": {"type": "string"},
            "category": {"type": "string", "enum": ["all", "kick", "snare", "clap", "hat", "tom", "perc", "808"]},
        },
        ["query"],
    ),
    _tool(
        "live_context",
        "Persistent production memory. scope=project (this set), global (who the user is), memory (named facts). Prefer read before write.",
        {
            "action": {"type": "string", "enum": ["read", "write", "delete"]},
            "scope": {"type": "string", "enum": ["project", "global", "memory"]},
            "content": {"type": "string"},
            "name": {"type": "string", "description": "Memory entry name."},
            "description": {"type": "string", "description": "One-line recall hook for a memory write."},
            "project": {"type": "string", "description": "Live Set name for project scope."},
        },
    ),
    _tool(
        "live_api",
        "Raw Live Object Model access (get/set/call/goto). Use only when a specialized live_* tool cannot do the job.",
        {
            "path": {"type": "string", "description": "e.g. live_set tracks 0."},
            "operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["get", "set", "call", "goto", "info", "getcount", "exists"]},
                        "property": {"type": "string"},
                        "method": {"type": "string"},
                        "args": {"type": "array", "items": {"type": ["string", "number", "boolean"]}},
                        "value": {"type": ["string", "number", "boolean"]},
                    },
                    "required": ["type"],
                    "additionalProperties": False,
                },
            },
        },
        ["operations"],
    ),
    _tool(
        "live_run_action",
        "Run a built-in Live Actions host tool. payload is {\"tracks\": [...], \"fields\": {...}}. "
        "`tracks` is a list of {\"track_number\": N, \"kind\": \"midi\"|\"audio\"|\"return\"|\"master\"} for the "
        "tracks this action should run on, track_number exactly as Live shows it -- call live_read_set first "
        "and build this list from the tracks the user is talking about (by name or by the track number they "
        "said); most tool_ids require at least one track and return an error message (not a hard failure) "
        "like 'Tick a MIDI track.' if the list is empty. `fields` holds tool-specific "
        "options, all optional unless noted: "
        "clip-namer {pattern: \"{track} {bar} take\"}; "
        "color-clips {color: \"#3b82f6\" (required), also_scenes: \"yes\"|\"no\"}; "
        "empty-clips {length: 4, name: \"Empty\"} (MIDI tracks only); "
        "mutate {count: 4, seed: 1, mode: \"independent\"} (needs a MIDI clip selected on a ticked MIDI track); "
        "track-batch {action: \"rename\", pattern: \"{name}\"}; "
        "duplicate-clips {} (copies each ticked track's clips into its own empty slots); "
        "reveal-device {name: \"Chord Explorer\"}; "
        "arrangement-skeleton, fill-forge, song-mapper: see live_context for their fields. "
        "detect-key: prefer the dedicated live_detect_key tool instead of this one. "
        "Async tool_ids (song-mapper section placement) return {ok: true, pending: true, "
        "message: \"...\"} immediately and keep working in the background; that is a normal 'started' "
        "response, not a failure.",
        {
            "tool_id": {"type": "string", "enum": ["clip-namer", "arrangement-skeleton", "mutate", "empty-clips", "color-clips", "duplicate-clips", "track-batch", "reveal-device", "fill-forge", "song-mapper"]},
            "payload": {
                "type": "object",
                "properties": {
                    "tracks": {
                        "type": "array",
                        "description": "Ticked tracks, e.g. [{\"track_number\": 1, \"kind\": \"midi\"}], track_number exactly as Live shows it. Get these from live_read_set/live_context, not invented.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "track_number": {"type": "integer", "minimum": 1},
                                "kind": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
                            },
                        },
                    },
                    "fields": {"type": "object", "description": "Tool-specific options; see the tool description above for each tool_id's fields."},
                },
            },
        },
        ["tool_id"],
    ),
    _tool(
        "live_detect_key",
        "Deterministic key/mode detection (Krumhansl-Schmuckler pitch-class analysis) for a MIDI clip, track(s), or the whole Set. "
        "Always call this for 'what key/scale is this in' questions instead of guessing from live_read_clip note data yourself — "
        "the math is exact, eyeballing notes is not.",
        {
            "scope": {"type": "string", "enum": ["clip", "track", "set"], "description": "clip = selected/detail MIDI clip (default). track = all clips on given track_number(s). set = every MIDI clip in the Set."},
            "profile": {"type": "string", "enum": ["krumhansl-kessler", "temperley"], "description": "Weight table to correlate against. Default krumhansl-kessler."},
            "results": {"type": "integer", "description": "How many top key/mode guesses to return (1-12, default 3)."},
            "track_numbers": {"type": "array", "items": {"type": "integer", "minimum": 1}, "description": "Track number(s) for scope=track, exactly as Live shows them, e.g. [1] or [1,3]."},
        },
    ),
    _tool(
        "live_read_meter",
        "Read real-time peak/VU output meters (output_meter_left, output_meter_right, output_meter_level 0.0-1.0) from a track, return track, or master bus while playback is running.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"], "description": "Default regular track. Pass 'master' for master bus, 'return' for return track."},
        },
    ),
    _tool(
        "live_read_macros",
        "List the macro controls of a Rack device (Instrument, Audio Effect, MIDI, or Drum Rack) on a track, including names, values, ranges, is_quantized, and is_enabled state.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "device_number": {"type": "integer", "minimum": 1},
            "path": {"type": "string", "description": "Path e.g. t1/d1 or t2/d1."},
        },
    ),
    _tool(
        "live_update_macro",
        "Set a Rack macro control value by number (1-based, e.g. macro_number 1 = Macro 1) or name. Accepts native units (value) or normalized 0.0-1.0 (value_normalized).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
            "device_number": {"type": "integer", "minimum": 1},
            "path": {"type": "string", "description": "Path e.g. t1/d1."},
            "macro": {"type": "string", "description": "Macro name, e.g. 'Filter Freq'. For numeric addressing use macro_number instead."},
            "macro_number": {"type": "integer", "minimum": 1, "description": "Macro number, exactly as Live shows it (1 for Macro 1). Ignored if macro is also given."},
            "value": {"type": "number", "description": "Value in native units."},
            "value_normalized": {"type": "number", "description": "Value normalized from 0.0 to 1.0."},
        },
    ),
    _tool(
        "live_remove_notes",
        "Surgically remove MIDI notes from a clip within a specific time and pitch window without erasing other notes in the clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number."},
            "from_time": {"type": "number", "description": "Start beat (default 0.0)."},
            "time_span": {"type": "number", "description": "Duration in beats to clear (default entire clip length)."},
            "from_pitch": {"type": "integer", "description": "Lowest MIDI pitch to remove (0-127, default 0)."},
            "pitch_span": {"type": "integer", "description": "Number of semitones above from_pitch to clear (default 128)."},
        },
    ),
    _tool(
        "live_duplicate_to_arrangement",
        "Directly duplicate a Session-view clip into the Arrangement timeline at a specific beat position via track.duplicate_clip_to_arrangement.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Source track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Source clip slot number."},
            "destination_time": {"type": "number", "description": "Beat position in Arrangement timeline (e.g. 0.0, 16.0, 32.0)."},
            "to_track_number": {"type": "integer", "minimum": 1, "description": "Target track number (defaults to same track)."},
        },
        ["destination_time"],
    ),
    _tool(
        "live_read_arrangement_clips",
        "Read all clips placed along the Arrangement timeline for a track (start_time, end_time, length, name, color, is_midi, is_audio, muted).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number to inspect, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_type": {"type": "string", "enum": ["midi", "audio", "return", "master"]},
        },
        ["track_number"],
    ),
    _tool(
        "live_update_arrangement_clip",
        "Update or rename a clip situated on the Arrangement timeline.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "Number within track.arrangement_clips, exactly as Live shows it (ordered by start_time)."},
            "name": {"type": "string", "description": "New clip name."},
            "color": {"type": "string", "description": "Hex color code."},
            "mute": {"type": "boolean", "description": "Mute state."},
        },
        ["track_number", "clip_number"],
    ),
    _tool(
        "live_analyze_audio",
        "Objective acoustic analysis of a WAV audio file: Integrated/Short-term LUFS, True Peak (dBTP), RMS, crest factor, 10-band spectral balance, spectral centroid (brightness Hz), rolloff, flatness, transient punch (band crest dB), and stereo width/correlation.",
        {
            "path": {"type": "string", "description": "Absolute or relative path to the audio file."},
            "max_seconds": {"type": "number", "description": "Maximum seconds to analyze (default 600)."},
        },
        ["path"],
    ),
    _tool(
        "live_compare_audio",
        "Diff and compare two audio files (B relative to A) to evaluate perceptual and acoustic changes before and after a parameter or processing tweak. Returns headline and delta metrics (LUFS, punch, brightness, stereo width).",
        {
            "path_a": {"type": "string", "description": "Before audio file path."},
            "path_b": {"type": "string", "description": "After audio file path."},
            "max_seconds": {"type": "number", "description": "Maximum seconds to analyze (default 600)."},
        },
        ["path_a", "path_b"],
    ),
    _tool(
        "live_record_audio",
        "Capture Ableton Live's real-time audio output to a WAV file via a Windows loopback audio device (e.g. Voicemeeter VAIO / virtual cable) using ffmpeg.",
        {
            "seconds": {"type": "number", "description": "Duration to record in seconds (default 4.0)."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Optional track number to solo during capture, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "scene_number": {"type": "integer", "minimum": 1, "description": "Optional scene number to fire at start."},
            "start_playback": {"type": "boolean", "description": "Whether to start Live transport playback (default true if recording)."},
            "out_path": {"type": "string", "description": "Optional output WAV path."},
        },
    ),
    _tool(
        "live_record_and_analyze",
        "Capture real-time audio output from Live and immediately run acoustic DSP analysis in one call. The core primitive for closed-loop parameter tuning.",
        {
            "seconds": {"type": "number", "description": "Duration to record in seconds (default 4.0)."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Optional track number to solo during capture, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "scene_number": {"type": "integer", "minimum": 1, "description": "Optional scene number to fire at start."},
            "start_playback": {"type": "boolean", "description": "Whether to start Live transport playback."},
        },
    ),
    _tool(
        "library_read",
        "Open one studio-library file (INDEX.md, chapter markdown, or PDF). Always follow Decide first: read INDEX.md, then only the 1–3 books it names.",
        {
            "path": {"type": "string", "description": "Absolute path or path relative to the Knowledge folder."},
            "query": {"type": "string", "description": "Optional substring to jump to (chapter, device, topic)."},
            "max_chars": {"type": "integer"},
        },
        ["path"],
    ),
    _tool(
        "library_search",
        "Search the user's Knowledge folder (and plugin manuals folder, if set) by filename or INDEX row. Use when INDEX has no obvious row.",
        {
            "query": {"type": "string"},
            "limit": {"type": "integer"},
        },
        ["query"],
    ),
    _tool(
        "library_db_search",
        "Full-text search (SQLite FTS5) over the knowledge database — the preferred first stop for beat-making "
        "recipes, preset-rack breakdowns, mix engineering (gain, pan, EQ curves), Vital sound design, beginner "
        "music theory, and notes on Ableton remote-control projects. The user may have added datasets of their "
        "own, so ALWAYS call with topic='?' first if you're not sure of the exact key, rather than guessing or "
        "assuming a topic doesn't exist. For the user's own notes and manuals use library_read/library_search.",
        {
            "topic": {"type": "string", "description": "A topic key, e.g. ableton_god_producer, ableton_racks_labeled, mixology_db, vital_synth_lab, music_theory_basics, ableton_mcp_extended, ableton_live_mcp_bschoepke, abletonosc (see topic='?' for the full current list, including the user's own datasets)."},
            "query": {"type": "string"},
            "limit": {"type": "integer", "description": "1-10, default 5."},
        },
        ["topic", "query"],
    ),
    _tool(
        "live_generate_euclidean",
        "Algorithmic Euclidean rhythm generator (Bjorklund algorithm). Distributes pulses evenly across steps and writes directly to a Session clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "pulses": {"type": "integer", "description": "Number of active hits/pulses (e.g. 5)."},
            "steps": {"type": "integer", "description": "Total steps in cycle (e.g. 16 for 16th notes)."},
            "rotate": {"type": "integer", "description": "Shift pattern forward by N steps."},
            "pitch": {"type": "integer", "description": "MIDI note pitch (e.g. 36 for kick, 38 snare, 42 hat)."},
            "velocity": {"type": "integer", "description": "Base velocity 1-127 (default 100)."},
            "bars": {"type": "integer", "description": "Number of measures/bars to write (default 1)."},
            "humanize": {"type": "number", "description": "Timing and velocity jitter (0.0 to 1.0)."},
        },
        ["track_number", "slot_number", "pulses"],
    ),
    _tool(
        "live_generate_chords",
        "Generate voiced chord progressions with smooth voice leading (Drop-2, rootless A/B, shell voicings) and write directly to a Session clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "progression": {"type": "string", "description": "Progression string e.g. 'ii-V-I', 'Dm7 G7 Cmaj7', or 'I vi IV V'."},
            "key": {"type": "string", "description": "Key root note (e.g. 'C', 'F#', 'Eb', default 'C')."},
            "beats_per_chord": {"type": "number", "description": "Duration of each chord in beats (default 4.0)."},
            "style": {"type": "string", "enum": ["drop2", "rootless", "shell", "open", "root"], "description": "Voicing style (default drop2)."},
            "center_pitch": {"type": "integer", "description": "Center MIDI pitch register (default 60 = C3)."},
            "velocity": {"type": "integer", "description": "Chord velocity (default 85)."},
            "strum": {"type": "number", "description": "Strumming delay between notes in beats (e.g. 0.015)."},
        },
        ["track_number", "slot_number", "progression"],
    ),
    _tool(
        "live_generate_walking_bass",
        "Generate a jazz/blues quarter-note walking bassline with root anchors, diatonic steps, and chromatic approaches.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "progression": {"type": "string", "description": "Progression string e.g. 'ii-V-I-I', 'Dm7-G7-Cmaj7-Cmaj7'."},
            "key": {"type": "string", "description": "Key root (default 'C')."},
            "beats_per_chord": {"type": "number", "description": "Beats per chord (default 4.0)."},
            "octave": {"type": "integer", "description": "Bass octave register (1 = low, 2 = mid)."},
            "ghost": {"type": "boolean", "description": "Include syncopated ghost notes (default true)."},
            "velocity": {"type": "integer", "description": "Base velocity (default 95)."},
        },
        ["track_number", "slot_number", "progression"],
    ),
    _tool(
        "live_transform_clip",
        "Apply classical motif transformations to a MIDI clip's notes: pitch inversion, retrograde (reverse), retrograde inversion, augmentation (time stretch), diminution (compression), transposition, or humanization.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Clip slot number."},
            "op": {"type": "string", "enum": ["invert", "retrograde", "retrograde_invert", "augment", "diminish", "transpose", "humanize"], "description": "Transformation operation."},
            "amount": {"type": "number", "description": "Scaling factor (for augment/diminish) or semitone shift (for transpose)."},
            "axis": {"type": "integer", "description": "Optional pitch axis for inversion (defaults to median pitch)."},
        },
        ["track_number", "slot_number", "op"],
    ),
    _tool(
        "live_write_drum_grid",
        "Parse a multi-line ASCII drum grid into timed MIDI note events and write directly to a Session clip on a Drum Rack track.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target drum track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "grid": {"type": "string", "description": "Multi-line ASCII grid e.g. 'K: x...x...x...x...\\nS: ....x.......x...\\nCH: x.x.x.x.x.x.x.x.'"},
            "step_beats": {"type": "number", "description": "Step length in beats (default 0.25 = 16th note)."},
            "swing": {"type": "number", "description": "Swing amount 0.0 to 1.0 (default 0.0)."},
        },
        ["track_number", "slot_number", "grid"],
    ),
    _tool(
        "als_summary",
        "Inspect an Ableton Live set (.als) file offline without running Ableton: creator version, tempo, time signature, scale, track count, clips, and locators.",
        {
            "path": {"type": "string", "description": "Path to the .als file."},
        },
        ["path"],
    ),
    _tool(
        "als_list_tracks",
        "List all tracks, mixer volumes, pans, loaded devices, and clips directly from a saved .als file offline.",
        {
            "path": {"type": "string", "description": "Path to the .als file."},
        },
        ["path"],
    ),
    _tool(
        "als_extract_midi",
        "Extract MIDI notes from a clip in a saved .als project directly into JSON note events without opening Ableton.",
        {
            "path": {"type": "string", "description": "Path to the .als file."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "MIDI clip number on that track, exactly as Live shows it."},
        },
        ["path", "track_number"],
    ),
    _tool(
        "als_diff",
        "Diff two saved .als project files (e.g. song_v1.als vs song_v2.als) offline, reporting added/removed tracks, renamed tracks, tempo changes, and clip count differences.",
        {
            "path_a": {"type": "string", "description": "First .als file path."},
            "path_b": {"type": "string", "description": "Second .als file path to compare against."},
        },
        ["path_a", "path_b"],
    ),
    _tool(
        "als_find_unfinished",
        "Lint a saved .als file offline for production omissions, unfinished work, clipping master faders, missing limiters, soloed tracks, and empty clips.",
        {
            "path": {"type": "string", "description": "Path to the .als file."},
        },
        ["path"],
    ),
    _tool(
        "live_capture_midi",
        "Trigger Ableton's native Capture MIDI feature to retrieve recently played MIDI into a new clip on the armed track.",
        {},
    ),
    _tool(
        "live_back_to_arranger",
        "Trigger Ableton's Back to Arrangement button to return playback control to the Arrangement timeline.",
        {},
    ),
    _tool(
        "live_re_enable_automation",
        "Re-enable parameter automation that was overridden by manual control tweaks (the orange automation button in Live).",
        {},
    ),
    _tool(
        "live_set_crossfader",
        "Control master crossfader slider position (-1.0 to 1.0) and assign tracks to crossfader sides (A, B, or None).",
        {
            "value": {"type": "number", "description": "Master crossfader position: -1.0 (full A), 0.0 (center), 1.0 (full B)."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Optional track number to assign, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "assign": {"type": "string", "enum": ["A", "B", "None"], "description": "Assign track to Crossfade side A, B, or None."},
        },
    ),
    _tool(
        "live_create_take_lane",
        "Create an audio or MIDI take lane on a track for comping multiple recorded passes.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
        },
        ["track_number"],
    ),
    _tool(
        "live_set_fold_state",
        "Inspect or toggle the fold/collapse state of a Group track in the Live mixer/session.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Group track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "folded": {"type": "boolean", "description": "True to collapse/fold group; False to expand/unfold."},
        },
        ["track_number"],
    ),
    _tool(
        "live_groove_pool",
        "Inspect grooves loaded in the Groove Pool, or attach a groove to a clip to apply swing and timing feel.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Optional track number to attach groove to, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "Optional clip slot number."},
            "groove_number": {"type": "integer", "minimum": 1, "description": "Groove number from the Groove Pool to attach."},
            "clear": {"type": "boolean", "description": "Set true to remove groove from clip."},
        },
    ),
    _tool(
        "live_duplicate_loop",
        "Double a clip's loop length and duplicate all notes inside it (equivalent to Live's native Duplicate Loop button).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Clip slot number."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_analyze_mix",
        "Perform a heuristic structural mix audit on the running Live Set: flags low-end clashing frequencies, clipping tracks, missing master limiters, solo hygiene, and panning balance.",
        {},
    ),
    _tool(
        "live_undo",
        "Undo the last action in Ableton Live (equivalent to Edit -> Undo).",
        {},
    ),
    _tool(
        "live_redo",
        "Redo the last undone action in Ableton Live (equivalent to Edit -> Redo).",
        {},
    ),
    _tool(
        "live_jump_to_time",
        "Jump the arrangement playhead to an exact beat position without starting playback.",
        {
            "time": {"type": "number", "description": "Arrangement beat position (>= 0.0)."},
        },
        ["time"],
    ),
    _tool(
        "live_set_overdub",
        "Enable or disable MIDI/arrangement overdub recording in Ableton Live.",
        {
            "overdub": {"type": "boolean", "description": "True to turn overdub on, False to turn off."},
            "session_record": {"type": "boolean", "description": "Optional: also set session record overdub state."},
        },
        ["overdub"],
    ),
    _tool(
        "live_read_arrangement_length",
        "Query the total length of the Arrangement song timeline in beats (from song.song_length).",
        {},
    ),
    _tool(
        "live_move_arrangement_clip",
        "Move an arrangement clip to a new beat start time and/or different track on the timeline.",
        {
            "source_track_number": {"type": "integer", "minimum": 1, "description": "Source track number."},
            "source_clip_number": {"type": "integer", "minimum": 1, "description": "Source arrangement clip number."},
            "new_start_time": {"type": "number", "description": "New beat start position."},
            "target_track_number": {"type": "integer", "minimum": 1, "description": "Optional target track number (defaults to source track)."},
        },
        ["source_track_number", "source_clip_number", "new_start_time"],
    ),
    _tool(
        "live_read_arrangement_notes",
        "Read all MIDI notes directly from an arrangement clip on the timeline.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number."},
        },
        ["track_number", "clip_number"],
    ),
    _tool(
        "live_write_arrangement_notes",
        "Write or append MIDI notes directly into an arrangement clip on the timeline.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number."},
            "notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pitch": {"type": "integer"},
                        "start_time": {"type": "number"},
                        "duration": {"type": "number"},
                        "velocity": {"type": "integer"},
                        "mute": {"type": "boolean"},
                    },
                    "required": ["pitch", "start_time", "duration", "velocity"],
                },
                "description": "List of note objects or JSON string.",
            },
            "replace": {"type": "boolean", "description": "True to replace all notes (default), False to append."},
        },
        ["track_number", "clip_number", "notes"],
    ),
    _tool(
        "live_remove_arrangement_notes",
        "Surgically remove MIDI notes in a pitch/time range from an arrangement clip on the timeline without erasing the whole clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number."},
            "from_pitch": {"type": "integer", "description": "Lowest pitch (0-127, default 0)."},
            "pitch_span": {"type": "integer", "description": "Number of semitones span (default 128)."},
            "from_time": {"type": "number", "description": "Start time in beats (default 0)."},
            "time_span": {"type": "number", "description": "Duration in beats (default 100000)."},
        },
        ["track_number", "clip_number"],
    ),
    _tool(
        "live_read_take_lanes",
        "Get all take lanes on a track with their index and name.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
        },
        ["track_number"],
    ),
    _tool(
        "live_update_take_lane",
        "Rename an existing take lane on an arrangement track.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "take_lane_number": {"type": "integer", "minimum": 1, "description": "Take lane number."},
            "name": {"type": "string", "description": "New name for the take lane."},
        },
        ["track_number", "take_lane_number", "name"],
    ),
    _tool(
        "live_create_take_lane_clip",
        "Create an empty MIDI clip directly inside a take lane on an arrangement track.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "take_lane_number": {"type": "integer", "minimum": 1, "description": "Take lane number."},
            "start_time": {"type": "number", "description": "Beat start position (default 0.0)."},
            "length": {"type": "number", "description": "Clip length in beats (default 4.0)."},
        },
        ["track_number", "take_lane_number"],
    ),
    _tool(
        "live_batch_tracks",
        "Perform batch track operations across the entire Live Set (unarm_all, unmute_all, unsolo_all, solo_exclusive).",
        {
            "action": {
                "type": "string",
                "enum": ["unarm_all", "unmute_all", "unsolo_all", "solo_exclusive"],
                "description": "Batch operation to execute.",
            },
            "track_number": {
                "type": "integer",
                "minimum": 1,
                "description": "Target track number, exactly as Live shows it (required for solo_exclusive).",
            },
        },
        ["action"],
    ),
    _tool(
        "live_stop_all_clips",
        "Immediately stop all playing clips across all session tracks simultaneously.",
        {},
    ),
    _tool(
        "live_tap_tempo",
        "Tap the session tempo, updating the Live Set BPM according to tap timing.",
        {},
    ),
    _tool(
        "live_continue_playing",
        "Resume transport playback from the current playhead position without restarting.",
        {},
    ),
    _tool(
        "live_scrub",
        "Scrub the transport playhead position forward or backward by a delta in beats.",
        {
            "beats": {"type": "number", "description": "Delta in beats (e.g. 4.0, -4.0, 16.0)."},
        },
        ["beats"],
    ),
    _tool(
        "live_jump_cue",
        "Step transport playhead to the next or previous cue point / locator in the Arrangement.",
        {
            "direction": {"type": "string", "enum": ["next", "prev"], "description": "Direction to jump (default 'next')."},
        },
    ),
    _tool(
        "live_set_punch",
        "Toggle arrangement punch-in and/or punch-out recording markers.",
        {
            "punch_in": {"type": "boolean", "description": "Enable or disable punch-in."},
            "punch_out": {"type": "boolean", "description": "Enable or disable punch-out."},
        },
    ),
    _tool(
        "live_set_cue_volume",
        "Set the master headphone / cue preview output volume (0.0 to 1.0).",
        {
            "volume": {"type": "number", "description": "Cue volume level (0.0 to 1.0, 0.85 ≈ 0 dB)."},
        },
        ["volume"],
    ),
    _tool(
        "live_move_device",
        "Move a device to a new position index within a track's device chain.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Current device number in the chain."},
            "new_device_number": {"type": "integer", "minimum": 1, "description": "Target position in the chain, exactly as Live shows it (1 = first)."},
        },
        ["track_number", "device_number", "new_device_number"],
    ),
    _tool(
        "live_read_drum_pads",
        "Inspect all active drum pads in a Drum Rack device with their note numbers, pad names, mute, solo, and chain counts.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number of the Drum Rack."},
            "all": {"type": "boolean", "description": "Whether to return all 128 pads or only pads with assigned chains (default false)."},
        },
        ["track_number", "device_number"],
    ),
    _tool(
        "live_update_drum_pad",
        "Update or customize a specific drum pad in a Drum Rack (rename, mute, solo).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number of the Drum Rack."},
            "pad_note": {"type": "string", "description": "Pad note number or name, e.g. 36 or 'C1'."},
            "name": {"type": "string", "description": "New custom display name for the pad."},
            "mute": {"type": "boolean", "description": "Mute state for the pad."},
            "solo": {"type": "boolean", "description": "Solo state for the pad."},
        },
        ["track_number", "device_number", "pad_note"],
    ),
    _tool(
        "live_focus_view",
        "Focus a primary Live interface view (Session, Arrangement, Detail, Clip, Device) and optionally toggle Draw or Follow modes.",
        {
            "view": {
                "type": "string",
                "enum": ["session", "arrangement", "detail", "clip", "device"],
                "description": "View window to focus.",
            },
            "draw_mode": {"type": "boolean", "description": "Toggle pencil draw mode on/off."},
            "follow_mode": {"type": "boolean", "description": "Toggle arrangement playhead follow mode on/off."},
        },
    ),
    _tool(
        "live_session_snapshot",
        "Read-only deep structural snapshot of the Live session (tempo, signature, playing state, song time, tracks with volume/pan/mute/solo/arm, clip slots, and devices). Use before and after mutating tools to verify changes with live_session_diff.",
        {
            "include_clips": {"type": "boolean", "description": "Include session clip slots and playing states (default true)."},
            "include_devices": {"type": "boolean", "description": "Include device names and class names (default true)."},
        },
    ),
    _tool(
        "live_session_diff",
        "Compare a previous session_snapshot with the current Live state to verify what actually changed. Returns a detailed list of added/removed/changed paths, before/after values, and total change count.",
        {
            "previous": {"type": "object", "description": "The previous snapshot object returned by live_session_snapshot."},
        },
        ["previous"],
    ),
    _tool(
        "live_read_link_status",
        "Read-only Ableton Link and external sync status discovery (is_link_enabled, num_peers, is_connected, quantum, start_stop_sync_enabled, tempo_sync_enabled).",
        {},
    ),
    _tool(
        "live_list_recipes",
        "Read-only catalog of embedded multi-step music production recipes (tech-house kicks, reese bass, 808 subs, lofi jazz/neo-soul chord voicings, parallel comp racks, master bus/vocal chains, arrangements). Returns recipe names, categories, descriptions, and input parameters. `available:false` means the recipe needs a capability (e.g. the Remote Script companion for real browser presets) this build doesn't have yet -- don't call live_apply_recipe on it.",
        {
            "category": {
                "type": "string",
                "enum": ["drums", "bass", "chords", "racks", "arrangements", "mixing", "live_performance"],
                "description": "Optional category filter.",
            },
        },
    ),
    _tool(
        "live_apply_recipe",
        "Execute an embedded genre recipe by ID, automatically building multi-step production sequences (creating tracks, loading devices, tweaking parameters, and writing MIDI clips/notes) in Ableton Live.",
        {
            "recipe_id": {"type": "string", "description": "The recipe identifier, e.g. 'drums/tech-house-kick', 'bass/reese', 'racks/parallel-comp'."},
            "overrides": {"type": "object", "description": "Optional parameter overrides declared by the recipe (see live_list_recipes' inputs for that recipe). A recipe with a track_number input takes it 1-based, exactly as Live shows it -- never a raw track_index override, which is rejected."},
        },
        ["recipe_id"],
    ),
    _tool(
        "live_inspect_plugin",
        "Deep device and plugin discovery on a track. Identifies whether a device is native, VST/AU plugin, or Max for Live, and extracts class names, display names, total parameter count, and all exposed VST/AU plugin presets. After inspect, use live_read_device / live_update_device for Live-visible knobs. presets is a catalog, not a load command.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number."},
        },
        ["track_number", "device_number"],
    ),
    _tool(
        "live_get_selected",
        "Inspect what the user currently has selected in Ableton Live's GUI (selected track index/name/type, selected scene index/name, selected device index/name/class, and detail clip). Call this first when the user asks 'what is this?' or refers to their current selection.",
        {},
    ),
    _tool(
        "live_clear_clip_envelopes",
        "Reset and clear all parameter automation and modulation envelopes inside a Session clip or Arrangement clip via native LOM clear_all_envelopes.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number (for session clips)."},
            "arrangement_clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number (for arrangement timeline clips)."},
        },
        ["track_number"],
    ),
    _tool(
        "live_create_drum_pattern",
        "Write a drum pattern into a MIDI clip using step strings with velocity dynamics ('2'-'9') and polyrhythms. Pattern is a dict {voice: step_string} where voice can be 'kick', 'snare', 'hat', 'clap', 'tom_low', 'ride', 'shaker', note name ('C1'), or MIDI pitch int. Step chars: 'x'/'1' = hit, '.'/'-'/' ' = rest, '2'-'9' = scaled velocity (2 is ghost ~28, 9 is max ~127). Rows can have different lengths for polyrhythms.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "pattern": {"type": "object", "description": "Dict of {voice: step_string} e.g. {'kick': 'x...x...x...x...', 'snare': '....x.......x...'}"},
            "default_velocity": {"type": "integer", "description": "Base hit velocity (default 100)."},
            "beats_per_bar": {"type": "number", "description": "Beats per measure (default 4.0)."},
            "length_beats": {"type": "number", "description": "Explicit total clip duration in beats (optional)."},
            "name": {"type": "string", "description": "Clip name."},
        },
        ["track_number", "slot_number", "pattern"],
    ),
    _tool(
        "live_create_chord_progression",
        "Write a voiced chord progression into a MIDI clip from Roman numeral tokens ('I', 'vi', 'IV', 'V', 'ii°', 'bVII', 'V7') or explicit chord names ('Cm', 'F#maj7', 'G7'). Supports voicings: 'triad', 'seventh', 'power'. beats_per_chord can be a single number or per-chord list.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Target clip slot number."},
            "chords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of Roman tokens ('I', 'vi', 'IV', 'V', 'ii°', 'bVII') or chord names ('Cm', 'F#maj7'). Also accepts a single space/comma-separated string.",
            },
            "key": {"type": "string", "description": "Key root and mode e.g. 'C', 'Am', 'F#', 'Eb' (default 'C')."},
            "voicing": {"type": "string", "enum": ["triad", "seventh", "power"], "description": "Voicing style (default 'triad')."},
            "beats_per_chord": {"type": "number", "description": "Duration per chord in beats (default 4.0)."},
            "length_beats": {"type": "number", "description": "Explicit total clip length in beats (optional)."},
            "base_octave": {"type": "integer", "description": "Base octave register (default 3 = C3)."},
            "velocity": {"type": "integer", "description": "Chord velocity (default 85)."},
            "name": {"type": "string", "description": "Clip name."},
        },
        ["track_number", "slot_number", "chords"],
    ),
    _tool(
        "live_edit_track",
        "Unified track editor. op is 'delete', 'duplicate', or 'rename'. 'rename' requires name. 'duplicate' inserts copy directly after source.",
        {
            "op": {"type": "string", "enum": ["delete", "duplicate", "rename"], "description": "Operation to perform."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "name": {"type": "string", "description": "New track name (required for op='rename')."},
        },
        ["op", "track_number"],
    ),
    _tool(
        "live_edit_clip",
        "Unified clip editor. op is 'delete', 'duplicate', or 'rename'. 'rename' requires name. Duplicate with no target places into next empty slot on same track.",
        {
            "op": {"type": "string", "enum": ["delete", "duplicate", "rename"], "description": "Operation to perform."},
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Clip slot number."},
            "target_slot_number": {"type": "integer", "minimum": 1, "description": "Optional destination slot number for op='duplicate'."},
            "name": {"type": "string", "description": "New clip name (required for op='rename')."},
        },
        ["op", "track_number", "slot_number"],
    ),
    _tool(
        "live_edit_scene",
        "Unified scene editor. op is 'delete', 'duplicate', or 'rename'. 'rename' requires name.",
        {
            "op": {"type": "string", "enum": ["delete", "duplicate", "rename"], "description": "Operation to perform."},
            "scene_number": {"type": "integer", "minimum": 1, "description": "Target scene number."},
            "name": {"type": "string", "description": "New scene name (required for op='rename')."},
        },
        ["op", "scene_number"],
    ),
    _tool(
        "live_map_rack_magnitude",
        "Analyze an Audio or MIDI Effect Rack, discover Dry/Wet or Mix/Amount blend parameters across all nested chains and devices, rename Macro 1 (or specified macro) to 'Magnitude', and set the overall wet/dry magnitude level. `mapped` in the response is always false and `macro_map_api_supported` only reflects whether the underlying macro_map call didn't throw -- Live's API gives no way to verify a macro mapping actually took, so magnitude control instead relies on `set_directly` writing each blend parameter's value directly, which is what reliably works regardless of mapping.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Target track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number of the Rack (default 1)."},
            "macro_name": {"type": "string", "description": "Name for the macro (default 'Magnitude')."},
            "macro_number": {"type": "integer", "minimum": 1, "description": "Macro number, exactly as Live shows it (1 for Macro 1, default 1)."},
            "value_normalized": {"type": "number", "description": "Normalized magnitude value (0.0=dry, 1.0=full wet) to set immediately across the macro and all mapped blend parameters."},
            "value": {"type": "number", "description": "Raw macro value to set immediately."},
            "blend_names": {"type": "array", "items": {"type": "string"}, "description": "Optional custom parameter names to match as blend controls (defaults to Dry/Wet, Mix, Amount, Blend, Wet)."},
        },
        ["track_number"],
    ),
    _tool(
        "live_set_clip_follow_action",
        "Set follow actions for a Session clip: action A/B (none/stop/again/previous/next/first/last/any/other/jump), chance (0.0–1.0), time in beats, and enabled flag.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "action_a": {"type": "string", "enum": ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"], "description": "Follow action A."},
            "action_b": {"type": "string", "enum": ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"], "description": "Follow action B."},
            "chance": {"type": "number", "description": "Probability of action A (0.0–1.0, default 1.0)."},
            "time": {"type": "number", "description": "Follow action time in beats (default = clip length)."},
            "enabled": {"type": "boolean", "description": "Whether follow actions are active."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_get_clip_follow_action",
        "Read all follow action settings (action A/B names, chance, time, enabled) from a Session clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_set_clip_launch_mode",
        "Set the launch mode, launch quantization, and legato flag for a Session clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "launch_mode": {"type": "string", "enum": ["trigger", "gate", "toggle", "repeat"], "description": "Clip launch mode."},
            "launch_quantization": {"type": "string", "description": "global, none, 8_bars, 4_bars, 2_bars, 1_bar, 1/2, 1/4, 1/8, 1/16, 1/32."},
            "legato": {"type": "boolean", "description": "Whether legato (continuous) launch is enabled."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_set_clip_fades",
        "Set fade in/out times (in beats) on an audio clip. All four points are optional; omit any to leave unchanged.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "fade_in_start": {"type": "number", "description": "Fade-in start position in beats."},
            "fade_in_end": {"type": "number", "description": "Fade-in end position in beats."},
            "fade_out_start": {"type": "number", "description": "Fade-out start position in beats."},
            "fade_out_end": {"type": "number", "description": "Fade-out end position in beats."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_set_clip_markers",
        "Set start/end markers and/or loop start/end times on a clip (in beats).",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "start_marker": {"type": "number", "description": "Start marker in beats."},
            "end_marker": {"type": "number", "description": "End marker in beats."},
            "loop_start": {"type": "number", "description": "Loop start time in beats."},
            "loop_end": {"type": "number", "description": "Loop end time in beats."},
            "start_time": {"type": "number", "description": "Alias for loop_start (loop start time in beats)."},
            "end_time": {"type": "number", "description": "Alias for loop_end (loop end time in beats)."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_manage_warp_markers",
        "Get, add, or delete warp markers on an audio clip. action='get' lists all markers; 'add' inserts at beat_time (with optional sample_time); 'delete' removes at beat_time.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "action": {"type": "string", "enum": ["get", "add", "delete"], "description": "Operation: get, add, or delete."},
            "beat_time": {"type": "number", "description": "Warp marker position in beats (required for add/delete)."},
            "sample_time": {"type": "number", "description": "Sample position in seconds (optional for add)."},
        },
        ["track_number", "slot_number", "action"],
    ),
    _tool(
        "live_set_clip_automation",
        "Write a clip automation envelope for a parameter (by name), on a Session clip (slot_number) or an Arrangement clip (arrangement_clip_number). envelope_data is a list of {time, value} points.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number, exactly as Live shows it. Ignored if arrangement_clip_number is given."},
            "arrangement_clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number in track.arrangement_clips, exactly as Live shows it, instead of a Session clip slot_number."},
            "parameter_name": {"type": "string", "description": "Parameter name (e.g. 'Volume', 'Dry/Wet', 'Filter Freq')."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number (default 1) for device parameter lookup."},
            "envelope_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "number"},
                        "value": {"type": "number"},
                    },
                    "required": ["time", "value"],
                },
                "description": "List of {time (beats), value} automation points.",
            },
        },
        ["track_number", "parameter_name", "envelope_data"],
    ),
    _tool(
        "live_get_clip_automation",
        "Check whether a clip has automation envelopes.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Session clip slot number, exactly as Live shows it. Ignored if arrangement_clip_number is given."},
            "arrangement_clip_number": {"type": "integer", "minimum": 1, "description": "Arrangement clip number in track.arrangement_clips, exactly as Live shows it, instead of a Session clip slot_number."},
        },
        ["track_number"],
    ),
    _tool(
        "live_commit_groove",
        "Commit (bake) groove/quantize permanently into a clip's MIDI notes. quantize_to sets the grid (1=1/4, 5=1/16, 8=1/32, default 5); amount 0.0–1.0 blends original vs full groove.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "quantize_to": {"type": "integer", "description": "Grid: 1=1/4, 2=1/8, 3=1/8T, 4=1/8+T, 5=1/16, 6=1/16T, 7=1/16+T, 8=1/32 (default 5=1/16)."},
            "amount": {"type": "number", "description": "Quantize amount 0.0–1.0 (default 1.0)."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_add_shaped_automation",
        "Generate a shaped automation curve (sine/triangle/saw/square/random) and write it as a clip envelope for a named parameter. Cycles controls how many waveform cycles fit in the clip length.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it (Live's track 1 = track_number 1; digits in a track NAME do not indicate position)."},
            "track_name": {"type": "string", "description": "Track name instead of track_number -- exact match preferred, falls back to a unique substring match. Ignored if track_number is also given."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Slot number, exactly as Live shows it."},
            "parameter_name": {"type": "string", "description": "Parameter name to automate (e.g. 'Volume', 'Dry/Wet')."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number (default 1)."},
            "shape": {"type": "string", "enum": ["sine", "triangle", "saw", "square", "random"], "description": "Waveform shape."},
            "cycles": {"type": "number", "description": "Number of waveform cycles over the clip length (default 1.0)."},
            "min_value": {"type": "number", "description": "Minimum parameter value (default 0.0)."},
            "max_value": {"type": "number", "description": "Maximum parameter value (default 1.0)."},
            "points": {"type": "integer", "description": "Number of automation points (default 32)."},
            "length": {"type": "number", "description": "Clip length in beats (auto-detected if omitted)."},
        },
        ["track_number", "slot_number", "parameter_name", "shape"],
    ),
    # ── v1.0.39: verified present + settable in the Live 12.3.6 LOM truth
    # table (app/lom_surface.json / test_lom_surface.py) before shipping.
    _tool(
        "live_set_loop_region",
        "Set the Arrangement loop brace: enable/disable the loop and its start/length in beats.",
        {
            "enabled": {"type": "boolean", "description": "True to enable the arrangement loop, false to disable it."},
            "loop_start": {"type": "number", "description": "Loop start position in beats."},
            "loop_length": {"type": "number", "description": "Loop length in beats."},
        },
    ),
    _tool(
        "live_set_groove_amount",
        "Set the global groove pool amount -- how strongly the applied groove affects timing/velocity across the whole Live Set.",
        {"amount": {"type": "number", "description": "0.0 (no groove) to 1.0 (full groove)."}},
        ["amount"],
    ),
    _tool(
        "live_nudge",
        "Momentarily nudge the transport tempo up or down, for manual beatmatching against an external source.",
        {"direction": {"type": "string", "enum": ["up", "down"]}},
        ["direction"],
    ),
    _tool(
        "live_set_swing",
        "Set the global swing amount applied to quantized recording/playback.",
        {"amount": {"type": "number", "description": "0.0 (no swing) to 1.0 (max swing)."}},
        ["amount"],
    ),
    _tool(
        "live_set_appointed_device",
        "Appoint a device as the active target for external control surfaces (hardware controllers bound to 'the appointed device').",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number on that track, exactly as Live shows it."},
        },
        ["track_number", "device_number"],
    ),
    _tool(
        "live_set_automation_record",
        "Enable or disable Session View automation recording.",
        {"enabled": {"type": "boolean"}},
        ["enabled"],
    ),
    _tool(
        "live_read_param_range",
        "Read a device parameter's min/max, whether it's quantized, its enum value list (if any), and its current display value -- use this to pick a legal value before writing one, instead of guessing.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number on that track, exactly as Live shows it."},
            "param_name": {"type": "string", "description": "Exact parameter name (case-insensitive). Give this or param_number."},
            "param_number": {"type": "integer", "minimum": 1, "description": "Parameter number, exactly as live_read_device's params list shows it."},
        },
        ["track_number", "device_number"],
    ),
    _tool(
        "live_set_param_raw",
        "Set a device parameter's raw underlying value directly, within its min/max, bypassing display-string formatting entirely. The honest escape hatch when a device's display-string formatter is broken or ambiguous.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it."},
            "device_number": {"type": "integer", "minimum": 1, "description": "Device number on that track, exactly as Live shows it."},
            "param_name": {"type": "string", "description": "Exact parameter name (case-insensitive). Give this or param_number."},
            "param_number": {"type": "integer", "minimum": 1, "description": "Parameter number, exactly as live_read_device's params list shows it."},
            "value": {"type": "number", "description": "Raw value to write, clamped to the parameter's min/max."},
        },
        ["track_number", "device_number", "value"],
    ),
    _tool(
        "live_show_message",
        "Show a short message in Live's own status bar (bottom-left of the Live window) -- a feedback channel visible to the user that isn't Max Console.",
        {"text": {"type": "string"}},
        ["text"],
    ),
    _tool(
        "live_read_dialog",
        "Read the message/button count of a Live modal dialog currently blocking the UI, or press one of its buttons to dismiss it. Use this when another live_* call unexpectedly times out -- a stuck modal is a likely cause.",
        {"press_button_number": {"type": "integer", "minimum": 1, "description": "Button number to press (1-based). Omit to just read the current dialog message."}},
    ),
    _tool(
        "live_read_cpu",
        "Read Live's own average/peak audio engine CPU usage.",
        {},
    ),
    _tool(
        "live_view_control",
        "Show, hide, focus, or query visibility of a Live UI view (Session, Arranger, Detail/Clip, Detail/DeviceChain, Browser, etc.). action='list' (default) returns the valid view names for this Live version.",
        {
            "action": {"type": "string", "enum": ["list", "show", "hide", "focus", "is_visible"], "description": "Default 'list'."},
            "view_name": {"type": "string", "description": "Required for show/hide/focus/is_visible -- one of the names action='list' returns."},
        },
    ),
    _tool(
        "live_read_selected_notes",
        "Read only the MIDI notes currently selected in the piano-roll/MIDI Note editor for a clip -- unlike every other note tool, this does not touch or return the whole clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Clip slot number, exactly as Live shows it."},
        },
        ["track_number", "slot_number"],
    ),
    _tool(
        "live_transform_selected_notes",
        "Apply a classical motif transformation (invert, retrograde, transpose, humanize, etc.) to only the notes currently selected in the MIDI editor, leaving the rest of the clip untouched. The user must select notes in Live's piano roll first; use live_transform_clip instead to transform an entire clip.",
        {
            "track_number": {"type": "integer", "minimum": 1, "description": "Track number, exactly as Live shows it."},
            "slot_number": {"type": "integer", "minimum": 1, "description": "Clip slot number, exactly as Live shows it."},
            "op": {"type": "string", "enum": ["invert", "retrograde", "retrograde_invert", "augment", "diminish", "transpose", "humanize"]},
            "amount": {"type": "number", "description": "Scaling factor (augment/diminish) or semitone shift (transpose)."},
            "axis": {"type": "integer", "description": "Optional pitch axis for inversion (defaults to the median pitch of the selection)."},
        },
        ["track_number", "slot_number", "op"],
    ),
]

# ── Local Sample Searching Helper ───────────────────────────────────────────────

AUDIO_EXTS = {".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg"}
LIBRARY_EXTS = {".md", ".txt", ".pdf"}
SKIP_NAME_PREFIXES = ("unins",)
SKIP_DIR_PARTS = {".git", "node_modules", "__pycache__"}


def search_user_samples(samples_dir: Path, query: str, category: str = "all", max_results: int = 12) -> list[dict[str, str]]:
    """Scan the user's local samples directory for matching audio files."""
    if not samples_dir or not samples_dir.is_dir():
        return []

    tokens = [t.lower() for t in query.split() if t]
    cat_lower = category.lower()
    results: list[dict[str, str]] = []

    try:
        for root, _dirs, files in os.walk(samples_dir):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in AUDIO_EXTS:
                    continue
                path_lower = (root.replace("\\", "/") + "/" + f).lower()
                if cat_lower != "all" and cat_lower and cat_lower not in path_lower:
                    continue
                if all(tok in path_lower for tok in tokens):
                    results.append({
                        "name": f,
                        "path": os.path.join(root, f),
                        "folder": Path(root).name,
                    })
                    if len(results) >= max_results:
                        return results
    except Exception:
        pass
    return results


def _context_root() -> Path:
    appdata = Path(os.environ.get("APPDATA", str(Path.home()))) / "Live Actions" / CONTEXT_DIR_NAME
    appdata.mkdir(parents=True, exist_ok=True)
    (appdata / "memory").mkdir(exist_ok=True)
    return appdata


def _safe_memory_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "").strip()).strip("-")
    return cleaned[:200] or "note"


def handle_context(args: dict[str, Any]) -> str:
    action = str(args.get("action") or "read").lower()
    scope = str(args.get("scope") or "project").lower()
    root = _context_root()
    project = str(args.get("project") or "untitled").strip() or "untitled"
    project_slug = _safe_memory_name(project)

    if scope == "global":
        path = root / "global.md"
    elif scope == "memory":
        path = root / "memory" / (_safe_memory_name(str(args.get("name") or "")) + ".md")
        index_path = root / "memory" / "index.json"
    else:
        path = root / ("project-" + project_slug + ".md")

    if action == "read":
        if scope == "memory" and not args.get("name"):
            index_path = root / "memory" / "index.json"
            if index_path.is_file():
                return index_path.read_text(encoding="utf-8", errors="replace")
            names = sorted(p.stem for p in (root / "memory").glob("*.md"))
            return "Memory index:\n" + ("\n".join("- " + n for n in names) if names else "(empty)")
        if not path.is_file():
            return "(empty %s context)" % scope
        return path.read_text(encoding="utf-8", errors="replace")[:10000]

    if action == "delete":
        if scope != "memory" or not args.get("name"):
            return "delete is only for scope=memory with a name."
        if path.is_file():
            path.unlink()
        index_path = root / "memory" / "index.json"
        if index_path.is_file():
            try:
                idx = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception:
                idx = {}
            idx.pop(str(args.get("name")), None)
            index_path.write_text(json.dumps(idx, indent=2), encoding="utf-8")
        return "Deleted memory '%s'." % args.get("name")

    content = str(args.get("content") or "")
    if len(content) > 10000:
        content = content[:10000]
    path.write_text(content, encoding="utf-8")
    if scope == "memory":
        index_path = root / "memory" / "index.json"
        try:
            idx = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}
        except Exception:
            idx = {}
        if not isinstance(idx, dict):
            idx = {}
        idx[str(args.get("name") or path.stem)] = str(args.get("description") or content[:120])
        index_path.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    return "Wrote %s context (%d chars)." % (scope, len(content))


def _plugin_docs_dir(settings: dict[str, Any]) -> Path | None:
    """The optional plugin-manuals folder from Preferences, or None when it is not set."""
    raw = str(settings.get("plugin_docs_dir") or "").strip()
    return Path(raw) if raw else None


def _resolve_library_path(raw: str, settings: dict[str, Any]) -> Path | None:
    text = str(raw or "").strip().strip('"')
    if not text:
        return None
    candidate = Path(text)
    if candidate.is_file():
        return candidate
    knowledge = settings_store.knowledge_dir(settings)
    guesses = [
        knowledge / text,
        knowledge / text.replace("/", "\\"),
        GENIUS_DIR / "indexes" / text,
    ]
    plugin_docs = _plugin_docs_dir(settings)
    if plugin_docs:
        guesses.append(plugin_docs / Path(text).name)
    for g in guesses:
        if g.is_file():
            return g
    # Filename-only fallback inside knowledge
    name = Path(text).name
    if knowledge.is_dir() and name:
        for root, dirs, files in os.walk(knowledge):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_PARTS]
            if name in files:
                return Path(root) / name
    return candidate if candidate.exists() else None


def _extract_pdf_text(path: Path, limit: int) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        chunks: list[str] = []
        total = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            chunks.append(text)
            total += len(text)
            if total >= limit:
                break
        return "\n".join(chunks)
    except Exception as exc:
        return "(Could not extract PDF text from %s: %s)" % (path.name, exc)


def read_library_file(path: Path, query: str = "", limit: int = MAX_LIBRARY_CHARS) -> str:
    if not path.is_file():
        return "File not found: %s" % path
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf_text(path, max(limit * 4, 80000))
    elif suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        return "Cannot open %s (supported: .md .txt .pdf)." % path.name
    if query:
        needle = query.lower()
        idx = text.lower().find(needle)
        if idx < 0:
            return "Opened %s — no match for %r. First section:\n\n%s" % (path, query, text[: min(4000, limit)])
        start = max(0, idx - 800)
        end = min(len(text), idx + limit)
        return "Opened %s (match for %r):\n\n%s" % (path, query, text[start:end])
    if len(text) > limit:
        return text[:limit] + "\n\n[truncated — call library_read again with query= to jump to a chapter]"
    return text


def search_library(settings: dict[str, Any], query: str, limit: int = 20) -> str:
    tokens = [t.lower() for t in query.split() if t]
    if not tokens:
        return "Provide a search query."
    roots = [
        settings_store.knowledge_dir(settings),
        GENIUS_DIR / "indexes",
        _plugin_docs_dir(settings),
    ]
    hits: list[str] = []
    index_hits: list[str] = []
    for root in roots:
        if not root or not root.exists():
            continue
        index = root / "INDEX.md" if root.is_dir() else None
        if index and index.is_file():
            for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
                low = line.lower()
                if all(tok in low for tok in tokens):
                    index_hits.append("%s :: %s" % (index, line.strip()))
                    if len(index_hits) >= limit:
                        break
        if root.is_dir():
            for dirpath, dirs, files in os.walk(root):
                rel = Path(dirpath).relative_to(root).parts if dirpath != str(root) else ()
                if any(part in SKIP_DIR_PARTS for part in rel):
                    dirs[:] = []
                    continue
                if len(rel) >= 2 and rel[0] == "User Manuals" and rel[1] == "AI":
                    dirs[:] = []
                    continue
                if len(rel) >= 2 and rel[0] == "User Manuals" and rel[1] == "Windows":
                    if "MIDI Services" not in rel:
                        dirs[:] = [d for d in dirs if d == "MIDI Services"]
                        if not dirs:
                            continue
                dirs[:] = [d for d in dirs if d not in SKIP_DIR_PARTS and not d.lower().startswith("unins")]
                for fname in files:
                    low = fname.lower()
                    if low.startswith(SKIP_NAME_PREFIXES):
                        continue
                    if Path(fname).suffix.lower() not in LIBRARY_EXTS:
                        continue
                    path_low = (dirpath.replace("\\", "/") + "/" + fname).lower()
                    if all(tok in path_low for tok in tokens):
                        hits.append(str(Path(dirpath) / fname))
                        if len(hits) >= limit:
                            break
                if len(hits) >= limit:
                    break
    lines = []
    if index_hits:
        lines.append("INDEX rows:")
        lines.extend("  " + h for h in index_hits[:limit])
    if hits:
        lines.append("Files:")
        lines.extend("  " + h for h in hits[:limit])
    if not lines:
        return "No library matches for %r. Try a product name, chapter, or scale/mode." % query
    return "\n".join(lines)


# ── Custom instructions tool handler ───────────────────────────────────────────

def handle_custom_instructions(args: dict[str, Any], settings: dict[str, Any]) -> str:
    action = str(args.get("action") or "read").lower()
    set_name = current_live_set()

    if action == "read":
        preset = custom_instructions.active_preset(settings, set_name)
        if not preset:
            return (
                "No custom instructions are active for this Live Set. The user can create and "
                "assign a preset from the dropdown beside the agent picker, or in Preferences."
            )
        lines = custom_instructions.instruction_lines(preset.get("body", ""))
        if not lines:
            return f"Preset '{preset.get('name')}' is active for this Live Set but has no instructions yet."
        body = "\n".join("  - " + ln.lstrip("- ") for ln in lines)
        return f"Active preset '{preset.get('name')}' ({len(lines)} instruction(s)):\n{body}"

    if action != "add":
        return f"ERROR: unknown action '{action}' (use read or add)."

    text = str(args.get("text") or "").strip()
    if not text:
        return "ERROR: 'text' is required for action=add."

    # Re-read from disk before mutating. `settings` here is a snapshot taken
    # when the turn started (helper.py does dict(self.settings)), so writing it
    # back wholesale would silently revert anything the user changed in
    # Preferences while the turn was running.
    import settings_store

    try:
        fresh = settings_store.load_settings()
    except Exception:
        fresh = dict(settings)

    try:
        result = custom_instructions.add_instruction(
            fresh, set_name, text, replaces=args.get("replaces")
        )
    except ValueError as exc:
        return f"ERROR: {exc}"

    try:
        settings_store.save_settings(fresh)
    except Exception as exc:
        return f"ERROR: could not save custom instructions: {exc}"

    # Keep this turn's snapshot in step, so a later read in the same turn and
    # the next prompt build both see the new line.
    for key in (custom_instructions.PRESETS_KEY, custom_instructions.BINDINGS_KEY):
        settings[key] = fresh.get(key)

    if result.get("duplicate"):
        return (
            f"That instruction is already saved in preset '{result['preset_name']}' — nothing added. "
            f"Tell the user it was already there."
        )

    parts = [f"Added to custom instructions (preset '{result['preset_name']}'): \"{result['text']}\"."]
    if result.get("created_preset"):
        parts.append(f"Created and bound a new preset for this Live Set ('{result['preset_name']}').")
    if result.get("removed"):
        parts.append(f"Replaced the conflicting instruction: \"{result['removed']}\".")
    elif result.get("replaces_requested"):
        parts.append(
            f"No existing instruction matched \"{result['replaces_requested']}\", so nothing was removed — "
            "say so rather than claiming a replacement."
        )
    parts.append(
        f"{result['total']} instruction(s) now active. Report the exact wording above back to the user."
    )
    return " ".join(parts)


# ── Engine E2 tool handlers (Live's browser) ───────────────────────────────────

def _browser_path_arg(args: dict[str, Any]) -> list[str]:
    """The model sends path as a list, but sometimes as "Bass/Sub Bass"."""
    path = args.get("path") or []
    if isinstance(path, str):
        return [p for p in path.split("/") if p.strip()]
    return [str(p) for p in path if str(p).strip()]


def _browser_target(args: dict[str, Any]) -> dict[str, Any]:
    target: dict[str, Any] = {}
    if args.get("category"):
        target["category"] = str(args["category"])
        target["path"] = _browser_path_arg(args)
    if args.get("uri"):
        target["uri"] = str(args["uri"])
    return target


def _format_browser_items(items: list[dict[str, Any]], limit: int = 120) -> list[str]:
    """One line per item, saying what the model can actually DO with each.

    Two things matter here and both were wrong in the first cut, caught on a
    real library: a folder and a preset look identical otherwise (so the model
    tries to load folders), and `is_folder` alone does not mean "expandable" --
    a Live Pack reports is_folder False, is_loadable False, and still has
    children. Anything that is neither loadable nor a known folder is labelled
    "open it to see" rather than implied to be a dead end.
    """
    lines = []
    for item in items[:limit]:
        expandable = item.get("is_folder") or item.get("has_children")
        if item.get("is_loadable"):
            kind = "device" if item.get("is_device") else "loadable"
            note = f"{kind}, loadable" + (" · also has contents" if expandable else "")
        elif expandable:
            note = "folder -- browse into it"
        else:
            note = "not loadable -- try browsing into it"
        lines.append(f"  - {item.get('name')}  [{note}]")
    if len(items) > limit:
        lines.append(f"  ... {len(items) - limit} more in this page")
    return lines


def _dispatch_browser_tool(fn_name: str, args: dict[str, Any], settings: dict[str, Any]) -> str:
    client = rs_client(settings)
    if not rs_online(settings):
        return _rs_offline_message(settings)

    if fn_name == "live_browse":
        category = str(args.get("category") or "").strip()
        params: dict[str, Any] = {"refresh": bool(args.get("refresh"))}
        if category:
            params["category"] = category
            params["path"] = _browser_path_arg(args)
        if args.get("offset") is not None:
            params["offset"] = _int(args.get("offset"))
        if args.get("limit") is not None:
            params["limit"] = _int(args.get("limit"))
        res = client.call("browse", params, timeout=25.0)
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "browse failed")
        if not category:
            return "Live browser categories: " + ", ".join(res.get("categories") or [])
        items = res.get("items") or []
        where = "/".join([res.get("category") or category] + list(res.get("path") or []))
        if not items:
            return f"{where} is empty."
        total = _int(res.get("total"), len(items))
        offset = _int(res.get("offset"))
        head = f"{where} -- {total} item(s)"
        if res.get("truncated") or offset:
            head += f", showing {offset + 1}-{offset + len(items)} (pass offset to page on, or use live_library search)"
        return "\n".join([head] + _format_browser_items(items))

    if fn_name == "live_load_browser_item":
        params = _browser_target(args)
        if not params:
            return "ERROR: give category (+path) or uri for the item to load."
        if args.get("track_index") is not None:
            params["track_index"] = _int(args.get("track_index"))
        res = client.call("load_item", params, timeout=20.0)
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "load failed")
        track_no = res.get("track_index")
        # Name the track the way Live shows it, so a wrong-track load is caught
        # in the same turn rather than costing another one.
        track_label = (
            live_track_label({"index": track_no, "name": res.get("track_name")})
            if isinstance(track_no, int)
            else f"\"{res.get('track_name')}\""
        )
        return f"Loaded '{res.get('item_name')}' onto {track_label}."

    # live_preview_browser_item
    if str(args.get("op") or "play").lower() == "stop":
        res = client.call("stop_preview", {})
        return "Stopped browser preview." if res.get("ok") else "ERROR: " + str(res.get("error"))
    params = _browser_target(args)
    if not params:
        return "ERROR: give category (+path) or uri for the item to preview."
    res = client.call("preview_item", params, timeout=15.0)
    if not res.get("ok"):
        return "ERROR: " + str(res.get("error") or "preview failed")
    return f"Previewing '{res.get('previewing')}' (not added to the Set). Use op='stop' to stop."


# ── Host tools: TTS vocals and ffmpeg audio edits ──────────────────────────────
#
# Both run entirely on the Python host -- no Max, no OSC, and for TTS no API key
# or audio bytes anywhere near the bridge. They were already reachable from the
# Tool screen through host_tools.HOST_TOOLS; these handlers give Genius the same
# two pipelines rather than reimplementing either.


def _resolve_tts_profile(args: dict[str, Any], settings: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Pick the profile Genius asked for. Returns (profile, error_message).

    Deliberately stricter than tts_vocal._pick_profile, which falls back to the first
    profile when a name doesn't match -- fine for a dropdown that can only offer real
    names, wrong for a model that can invent one. Generating in the wrong voice and
    charging for it is worse than an error.

    A pinned profile (settings["active_tts_profile"], set from the checkbox on a
    profile card in Settings > TTS Vocal Profiles) overrides `profile` entirely --
    a `profile` arg naming something else is refused with the real reason rather
    than silently generating with a different voice than the model told the user
    it would.
    """
    profiles = [p for p in (settings.get("tts_profiles") or []) if isinstance(p, dict)]
    if not profiles:
        return None, (
            "No TTS profile is configured, so no vocal can be generated. In Live Actions open "
            "Preferences > TTS Vocal Profiles and add one (provider + API key + voice ID)."
        )
    pinned = str(settings.get("active_tts_profile") or "").strip()
    if pinned:
        for candidate in profiles:
            if str(candidate.get("name") or "").strip().lower() == pinned.lower():
                wanted = str(args.get("profile") or "").strip()
                if wanted and wanted.lower() != pinned.lower():
                    return None, (
                        f"ERROR: the user has pinned '{pinned}' as the only TTS profile (Settings > TTS "
                        f"Vocal Profiles). '{wanted}' cannot be used while it's pinned. Generate with "
                        f"'{pinned}', or tell the user to unpin it first if they actually want a "
                        "different voice."
                    )
                return candidate, ""
        return None, (
            f"ERROR: the pinned TTS profile '{pinned}' no longer exists. Open Settings > TTS Vocal "
            "Profiles and check the pin."
        )
    wanted = str(args.get("profile") or "").strip()
    if not wanted:
        return profiles[0], ""
    for candidate in profiles:
        if str(candidate.get("name") or "").strip().lower() == wanted.lower():
            return candidate, ""
    known = ", ".join(str(p.get("name") or "(unnamed)") for p in profiles)
    return None, f"ERROR: there is no TTS profile named '{wanted}'. Saved profiles: {known}."


def handle_tts_vocal(
    args: dict[str, Any],
    settings: dict[str, Any],
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """live_tts_vocal: approve, generate, report what was actually produced."""
    text = str(args.get("text") or "").strip()
    if not text:
        return "ERROR: Provide 'text' to speak."
    if len(text) > tts_vocal.MAX_TEXT_CHARS:
        return "ERROR: text is %d characters; the limit is %d." % (len(text), tts_vocal.MAX_TEXT_CHARS)

    profile, problem = _resolve_tts_profile(args, settings)
    if profile is None:
        return problem

    # A pinned profile drops any `voice` override too (tts_vocal._apply_overrides does
    # the same at generation time) -- show the voice that will ACTUALLY be used, not
    # one that will be silently ignored, so this dialog never asks approval for a
    # generation that then runs differently.
    voice_locked = bool(str(settings.get("active_tts_profile") or "").strip())
    voice = str(profile.get("voice_id") or "") if voice_locked else str(args.get("voice") or profile.get("voice_id") or "")
    rows = [
        ("Profile", str(profile.get("name") or "(unnamed)")),
        ("Provider", str(profile.get("provider") or "?")),
        ("Voice", voice or "(profile default)"),
        ("Text", text),
    ]
    if str(args.get("speed") or "").strip():
        rows.append(("Speed", str(args["speed"]).strip()))
    if str(args.get("language") or "").strip():
        rows.append(("Language", str(args["language"]).strip()))

    # No way to ask means no generation. This only bites a front-end that forgot to
    # wire `confirm`; a spend guard that fails open would not be a guard.
    if confirm is None:
        return (
            "Not generated: this build cannot ask the user to approve a paid TTS call, and "
            "generating one without asking would bill their API key unprompted. Tell the user "
            "to run the vocal from the TTS Vocal tool screen instead."
        )

    try:
        approved = confirm(CONFIRM_KINDS["live_tts_vocal"], {
            "title": "Generate a TTS vocal?",
            "body": "This calls %s with your saved API key and will be billed to your account."
                    % (profile.get("provider") or "the provider"),
            "rows": rows,
            "confirmLabel": "Generate",
        })
    except Exception as exc:  # noqa: BLE001 -- a broken dialog must not abort the turn
        return f"Not generated: could not ask the user to approve the call ({exc})."
    if not approved:
        return "Not generated: the user declined the TTS call. Do not retry it unless they ask."

    fields = {
        "text": text,
        "profile": str(profile.get("name") or ""),
        "voice": str(args.get("voice") or ""),
        "speed": str(args.get("speed") or ""),
        "language": str(args.get("language") or ""),
    }
    res = tts_vocal.run(fields, settings)
    if not res.get("ok"):
        return "TTS generation failed: " + str(res.get("message") or "unknown error")

    duration = res.get("durationSec")
    spoken = "%.2f s" % duration if isinstance(duration, (int, float)) else "unknown (ffprobe not available)"
    return "\n".join([
        "Generated a spoken vocal (%s)." % ("from cache" if res.get("cacheHit") else "new generation"),
        "  path: %s" % res.get("path"),
        "  actual duration: %s" % spoken,
        "  provider: %s   voice: %s" % (res.get("provider"), res.get("voice")),
        "This is SPEECH, not singing. Report the duration above as-is; do not describe it as a "
        "length the user asked for unless it matches. To change the length use live_audio_op "
        "'trim' (or 'silence' to pad); to shift pitch use 'pitch-time'.",
        "To put it in Live: live_update_device with a param named 'sample' set to this path (a "
        "Simpler on the track), or live_create_clip with sample_file (an audio track).",
    ])


def handle_audio_op(args: dict[str, Any], settings: dict[str, Any]) -> str:
    """live_audio_op: ffmpeg operations on a file, or a listing of them when no op is named."""
    import audio_sample

    operation = str(args.get("operation") or "").strip()
    if not operation:
        lines = ["%d audio operations. Pass 'operation' plus 'params' using these field names:"
                 % len(audio_sample.describe_ops())]
        current = ""
        for op in audio_sample.describe_ops():
            if op["category"] != current:
                current = op["category"]
                lines.append("  [%s]" % current)
            fields = ", ".join(
                "%s=%s" % (f["id"], f["default"] or "''")
                + ("" if not f.get("options") else " (%s)" % "|".join(f["options"]))
                for f in op["fields"]
            ) or "no fields"
            lines.append("    %-11s %-22s %s%s" % (
                op["id"], op["name"], fields,
                "" if op["needs_input"] else "   [needs no input_file]",
            ))
        lines.append("Times accept seconds ('10') or mm:ss.ms. Output is always a new file.")
        return "\n".join(lines)

    params = args.get("params")
    if params is not None and not isinstance(params, dict):
        return "ERROR: 'params' must be an object of field name -> value."
    raw = {str(k): ("" if v is None else str(v)) for k, v in (params or {}).items()}

    res = audio_sample.run_op(operation, str(args.get("input_file") or "").strip() or None, raw, settings)
    if not res.get("ok"):
        return "Audio operation failed: " + str(res.get("message") or "unknown error")
    out = ["%s" % (res.get("message") or "Done."), "  path: %s" % res.get("path")]
    if res.get("durationSec") is not None:
        out.append("  duration: %s s" % res.get("durationSec"))
    return "\n".join(out)


# ── Live Actions Bridge Execution Helper ────────────────────────────────────────

def call_live_tool(
    bridge: Any,
    fn_name: str,
    args: dict[str, Any],
    settings: dict[str, Any] | None = None,
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """Public entry point for a live_* / library_* tool call from the model.

    `confirm(kind, detail) -> bool` is how a tool asks the user's permission before
    doing something that costs them money (see CONFIRM_KINDS). A front-end that does
    not supply it gets a refusal from those tools rather than an unprompted charge.

    Translates the model's 1-based *_number arguments to the bridge's 0-based
    *_index arguments (see live_numbering.args_from_model) before dispatching,
    so every tool implementation below keeps working in 0-based terms
    unchanged. A malformed/0-based argument from the model comes back as an
    ERROR string instead of raising out of the tool-call loop.
    """
    try:
        translated = args_from_model(fn_name, args)
    except ModelArgError as e:
        return f"ERROR: {e}"
    return _dispatch_live_tool(bridge, fn_name, translated, settings=settings, confirm=confirm)


def _dispatch_live_tool(
    bridge: Any,
    fn_name: str,
    args: dict[str, Any],
    settings: dict[str, Any] | None = None,
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """Execute a live_* / library_* tool via the Live Actions OSC Bridge or local helpers.
    `args` is already 0-based here -- call_live_tool() is the only caller."""
    settings = settings or {}
    disk_bits: list[str] = []

    if fn_name == "library_read":
        resolved = _resolve_library_path(str(args.get("path") or ""), settings)
        if not resolved:
            return "File not found: %s" % args.get("path")
        limit = _int(args.get("max_chars"), MAX_LIBRARY_CHARS)
        return read_library_file(resolved, str(args.get("query") or ""), limit=limit)

    if fn_name == "library_search":
        return search_library(settings, str(args.get("query") or ""), _int(args.get("limit"), 20))

    if fn_name == "library_db_search":
        topic = str(args.get("topic") or "")
        if topic.strip() == "?":
            return genius_db.list_topics(genius_db.db_root(settings))
        return genius_db.db_search(settings, topic, str(args.get("query") or ""), _int(args.get("limit"), 5))

    if fn_name == "live_context":
        return handle_context(args)

    if fn_name == "live_custom_instructions":
        return handle_custom_instructions(args, settings)

    if fn_name == "live_tts_vocal":
        return handle_tts_vocal(args, settings, confirm)

    if fn_name == "live_audio_op":
        return handle_audio_op(args, settings)

    if fn_name == "live_find_samples":
        samples_path = settings_store.samples_dir(settings)
        query = str(args.get("query") or "")
        category = str(args.get("category") or "all")
        results = search_user_samples(samples_path, query, category, max_results=10)
        if not results:
            return f"No audio samples matching '{query}' found in {samples_path}."
        lines = [f"Found {len(results)} sample(s) matching '{query}' in {samples_path.name}:"]
        for r in results:
            lines.append(f"  - {r['name']} (folder: {r['folder']}) | path: {r['path']}")
        return "\n".join(lines)

    # One branch per tool rather than a tuple: test_genius_tools'
    # test_every_tool_has_a_route scans for this exact idiom, and a tuple would
    # hide a genuinely unrouted tool from it.
    if fn_name == "live_browse":
        return _dispatch_browser_tool(fn_name, args, settings)

    if fn_name == "live_load_browser_item":
        return _dispatch_browser_tool(fn_name, args, settings)

    if fn_name == "live_preview_browser_item":
        return _dispatch_browser_tool(fn_name, args, settings)

    # live_library never touches the OSC bridge. Disk search is local and
    # browser search is engine E2, so both must keep working with the Max
    # device off a track -- falling through to the bridge here used to turn a
    # perfectly good browser result into "Live Actions Bridge is not connected".
    if fn_name == "live_library" and str(args.get("action") or "search").lower() in ("listplugins", "list_plugins"):
        if not rs_online(settings):
            return (
                "Installed plug-ins cannot be listed: that needs Live's browser, and the browser engine "
                "(LiveActionsRS) isn't answering. " + _rs_offline_message(settings)
            )
        res = rs_client(settings).call("list_plugins", {}, timeout=25.0)
        if not res.get("ok"):
            return "ERROR: " + str(res.get("error") or "could not list plug-ins")
        plugins = res.get("plugins") or []
        if not plugins:
            return "No VST/VST3 plug-ins found in Live's browser."
        lines = [f"{len(plugins)} plug-in(s) installed (from Live's browser):"]
        lines.extend(f"  - {p.get('name')} [{p.get('format')}]" for p in plugins[:200])
        if len(plugins) > 200:
            lines.append(f"  ... and {len(plugins) - 200} more")
        return "\n".join(lines)

    if fn_name == "live_library" and str(args.get("action") or "search").lower() in ("listtags", "list_tags", "listcategories", "list_categories"):
        if rs_online(settings):
            res = rs_client(settings).call("ping", {})
            if res.get("ok") and res.get("categories"):
                return "Live browser categories: " + ", ".join(res["categories"])
        return (
            "Categories (static list -- the browser engine is offline, so this is not read from Live): "
            "drums, instruments, sounds, audio_effects, midi_effects, samples, user_library, packs, plugins, max_for_live"
        )

    if fn_name == "live_library" and str(args.get("action") or "search").lower() in ("search", "searchbatch"):
        samples_path = settings_store.samples_dir(settings)
        disk_bits: list[str] = []
        browser_online = rs_online(settings)
        queries = args.get("queries") if isinstance(args.get("queries"), list) else [{"query": args.get("query") or ""}]
        for q in queries[:8]:
            qtext = str((q or {}).get("query") or args.get("query") or "")
            if not qtext:
                continue
            found = search_user_samples(samples_path, qtext, "all", max_results=8)
            label = str((q or {}).get("label") or qtext)
            if found:
                disk_bits.append(label + ":")
                disk_bits.extend("  - %s | %s" % (r["name"], r["path"]) for r in found)
            else:
                disk_bits.append("%s: (no disk samples)" % label)

            # Live's own browser, when engine E2 is up. Reported as a separate
            # block rather than merged: a browser hit is loaded by path via
            # live_load_browser_item, while a disk hit is an absolute file path
            # for the Simpler/Drum Rack sample params -- different next steps.
            if browser_online:
                hits = (rs_client(settings).call(
                    "search", {"query": qtext, "limit": _int(args.get("limit"), 12)}
                ) or {}).get("results") or []
                if hits:
                    disk_bits.append("%s -- Live browser:" % label)
                    disk_bits.extend(
                        "  - %s | %s: %s%s"
                        % (
                            h.get("name"),
                            h.get("category"),
                            "/".join(h.get("path") or []),
                            "" if h.get("is_loadable") else " (not loadable)",
                        )
                        for h in hits
                    )
                else:
                    disk_bits.append("%s: (no Live browser matches)" % label)

        if not disk_bits:
            return "live_library search needs a 'query' (or a 'queries' list)."
        header = (
            "Matches from the disk Samples folder and Live's browser:"
            if browser_online
            else "Matches from the disk Samples folder only -- Live's browser is unavailable "
                 "(the LiveActionsRS engine is offline), so packs, presets and plug-ins are not searched:"
        )
        return "\n".join([header] + disk_bits)

    if fn_name == "live_analyze_audio":
        wav_path = str(args.get("path") or args.get("wav_path") or "")
        if not wav_path:
            return "ERROR: Provide 'path' to the audio file."
        max_sec = _float(args.get("max_seconds"), 600.0)
        try:
            from audio_analysis import analyze_audio
            res = analyze_audio(wav_path, max_seconds=max_sec)
            return json.dumps(res, indent=2)
        except Exception as e:
            return f"Audio analysis failed: {e}"

    if fn_name == "live_compare_audio":
        path_a = str(args.get("path_a") or "")
        path_b = str(args.get("path_b") or "")
        if not path_a or not path_b:
            return "ERROR: Provide both 'path_a' and 'path_b'."
        max_sec = _float(args.get("max_seconds"), 600.0)
        try:
            from audio_analysis import compare_audio
            res = compare_audio(path_a, path_b, max_seconds=max_sec)
            headline = res.get("delta", {}).get("headline", "Comparison complete")
            return f"Comparison Headline: {headline}\n\n" + json.dumps(res.get("delta", {}), indent=2)
        except Exception as e:
            return f"Audio comparison failed: {e}"

    if fn_name in ("live_record_audio", "live_record_and_analyze"):
        seconds = _float(args.get("seconds"), 4.0)
        ffmpeg_bin = str(settings.get("ffmpeg_path") or "ffmpeg")
        samples_dir = str(settings_store.samples_dir(settings))
        out_path = args.get("out_path")
        track_idx = args.get("track_index")
        scene_idx = args.get("scene_index")
        start_play = args.get("start_playback", True)

        prev_solo = None
        try:
            from audio_record import record_audio
            # Orchestrate with Live if bridge is connected
            if bridge and getattr(bridge, "call_live", None):
                if track_idx is not None:
                    tr_info = bridge.call_live("read_track", {"track_index": track_idx})
                    if isinstance(tr_info, dict) and tr_info.get("ok"):
                        prev_solo = tr_info.get("solo", False)
                    bridge.call_live("update_track", {"track_index": track_idx, "solo": True})
                if scene_idx is not None:
                    bridge.call_live("playback", {"action": "fire_scene", "scene_index": scene_idx})
                elif start_play:
                    bridge.call_live("playback", {"action": "play"})

            rec_file = record_audio(
                seconds=seconds,
                out_path=out_path,
                samples_dir=samples_dir,
                ffmpeg_path=ffmpeg_bin,
            )

            if fn_name == "live_record_and_analyze":
                from audio_analysis import analyze_audio
                analysis = analyze_audio(rec_file)
                return f"Captured {seconds:.1f}s to {rec_file}\n\nAnalysis:\n" + json.dumps(analysis, indent=2)

            return f"Successfully captured {seconds:.1f}s of audio to: {rec_file}"
        except Exception as exc:
            return f"Audio recording failed: {exc}"
        finally:
            if bridge and getattr(bridge, "call_live", None):
                if track_idx is not None and prev_solo is not None:
                    try:
                        bridge.call_live("update_track", {"track_index": track_idx, "solo": prev_solo})
                    except Exception:
                        pass
                if start_play or scene_idx is not None:
                    try:
                        bridge.call_live("playback", {"action": "stop"})
                    except Exception:
                        pass

    if fn_name == "als_summary":
        from als_tools import als_summary
        return json.dumps(als_summary(str(args.get("path") or "")), indent=2)

    if fn_name == "als_list_tracks":
        from als_tools import als_list_tracks
        return json.dumps(als_list_tracks(str(args.get("path") or "")), indent=2)

    if fn_name == "als_extract_midi":
        from als_tools import als_extract_midi
        return json.dumps(als_extract_midi(str(args.get("path") or ""), _int(args.get("track_index"), 0), _int(args.get("clip_index"), 0)), indent=2)

    if fn_name == "als_diff":
        from als_tools import als_diff
        return json.dumps(als_diff(str(args.get("path_a") or ""), str(args.get("path_b") or "")), indent=2)

    if fn_name == "als_find_unfinished":
        from als_tools import als_find_unfinished
        return json.dumps(als_find_unfinished(str(args.get("path") or "")), indent=2)

    if fn_name == "live_generate_euclidean":
        from algorithmic_generators import generate_euclidean_rhythm
        pulses = _int(args.get("pulses"), 4)
        steps = _int(args.get("steps"), 16)
        rotate = _int(args.get("rotate"), 0)
        pitch = _int(args.get("pitch"), 36)
        vel = _int(args.get("velocity"), 100)
        dur = _float(args.get("step_duration"), 0.25)
        bars = _int(args.get("bars"), 1)
        humanize = _float(args.get("humanize"), 0.0)
        notes = generate_euclidean_rhythm(pulses, steps, rotate, pitch, vel, dur, bars, humanize)
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        if not bridge or not getattr(bridge, "call_live", None):
            return f"Generated {len(notes)} Euclidean notes, but Bridge is offline:\n" + json.dumps(notes, indent=2)
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": True, "notes": notes}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Generated Euclidean rhythm ({pulses}/{steps}, pitch {pitch}, {len(notes)} hits) into track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write Euclidean rhythm to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_generate_chords":
        from algorithmic_generators import generate_voiced_progression
        prog = args.get("progression") or "ii-V-I"
        key = str(args.get("key") or "C")
        beats = _float(args.get("beats_per_chord"), 4.0)
        style = str(args.get("style") or "drop2")
        center = _int(args.get("center_pitch"), 60)
        vel = _int(args.get("velocity"), 85)
        strum = _float(args.get("strum"), 0.0)
        notes, names = generate_voiced_progression(prog, key=key, beats_per_chord=beats, style=style, center_pitch=center, velocity=vel, strum=strum)
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        if not bridge or not getattr(bridge, "call_live", None):
            return f"Voiced progression {names} generated ({len(notes)} notes), but Bridge is offline:\n" + json.dumps(notes, indent=2)
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": True, "notes": notes}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Wrote {len(names)} voiced chords ({', '.join(names)}) with '{style}' voicings ({len(notes)} notes) into track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write chord progression to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_generate_walking_bass":
        from algorithmic_generators import generate_walking_bass
        prog = args.get("progression") or "ii-V-I-I"
        key = str(args.get("key") or "C")
        beats = _float(args.get("beats_per_chord"), 4.0)
        octave = _int(args.get("octave"), 1)
        ghost = bool(args.get("ghost", True))
        vel = _int(args.get("velocity"), 95)
        notes = generate_walking_bass(prog, key=key, beats_per_chord=beats, octave=octave, ghost=ghost, velocity=vel)
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        if not bridge or not getattr(bridge, "call_live", None):
            return f"Generated {len(notes)} walking bass notes, but Bridge is offline:\n" + json.dumps(notes, indent=2)
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": True, "notes": notes}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Generated {len(notes)} walking bass notes under '{prog}' into track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write walking bass to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_transform_clip":
        from algorithmic_generators import transform_clip_notes
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        op = str(args.get("op") or "invert")
        amount = _float(args.get("amount"), 0.0)
        axis = _int(args.get("axis")) if args.get("axis") is not None else None
        if not bridge or not getattr(bridge, "call_live", None):
            return "ERROR: Bridge is not connected to transform clip."
        clip_data = bridge.call_live("read_clip", {"track_index": track_idx, "slot_index": slot_idx, "include": ["notes"]})
        if not isinstance(clip_data, dict) or not clip_data.get("ok"):
            return f"Failed to read clip on track {track_idx + 1}, slot {slot_idx + 1}: {clip_data}"
        raw_notes = clip_data.get("notes") or []
        if not raw_notes:
            return f"No notes found in clip on track {track_idx + 1}, slot {slot_idx + 1}."
        transformed = transform_clip_notes(raw_notes, op=op, amount=amount, axis=axis)
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": True, "notes": transformed}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Applied '{op}' transformation to {len(transformed)} notes on track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write transformed notes to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_transform_selected_notes":
        from algorithmic_generators import transform_clip_notes
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        op = str(args.get("op") or "invert")
        amount = _float(args.get("amount"), 0.0)
        axis = _int(args.get("axis")) if args.get("axis") is not None else None
        if not bridge or not getattr(bridge, "call_live", None):
            return "ERROR: Bridge is not connected to transform selected notes."
        sel = bridge.call_live("read_selected_notes", {"track_index": track_idx, "slot_index": slot_idx})
        if not isinstance(sel, dict) or not sel.get("ok"):
            return f"Failed to read selected notes on track {track_idx + 1}, slot {slot_idx + 1}: {sel}"
        raw_notes = sel.get("notes") or []
        if not raw_notes:
            return (
                f"No notes are selected in the MIDI editor for track {track_idx + 1}, slot {slot_idx + 1}. "
                "Select notes in Live's piano roll first, or use live_transform_clip to transform the whole clip."
            )
        transformed = transform_clip_notes(raw_notes, op=op, amount=amount, axis=axis)
        # Remove only the originally-selected notes by their own exact
        # pitch/time footprint (never a whole-clip clear) before writing the
        # transformed set back. This reuses the same remove_notes_extended /
        # add_new_notes primitives every other note tool here relies on,
        # instead of the tuple-based replace_selected_notes LOM call --
        # writeNotes()'s own comment in live-actions-bridge.js documents that
        # API as triggering Live's MPE/velocity-deviation warning dialog.
        for n in raw_notes:
            bridge.call_live("remove_notes", {
                "track_index": track_idx, "slot_index": slot_idx,
                "from_pitch": n.get("pitch", 0), "pitch_span": 1,
                "from_time": n.get("start_time", 0), "time_span": max(0.01, n.get("duration") or 0.25),
            })
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": False, "notes": transformed}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Applied '{op}' transformation to {len(transformed)} selected note(s) on track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write transformed notes to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_write_drum_grid":
        from algorithmic_generators import parse_drum_grid
        grid = str(args.get("grid") or "")
        step_beats = _float(args.get("step_beats"), 0.25)
        swing = _float(args.get("swing"), 0.0)
        track_idx = _int(args.get("track_index"), 0)
        slot_idx = _int(args.get("slot_index"), 0)
        notes = parse_drum_grid(grid, step_beats=step_beats, swing=swing)
        if not notes:
            return "No valid drum notes parsed from grid text."
        if not bridge or not getattr(bridge, "call_live", None):
            return f"Parsed {len(notes)} drum notes, but Bridge is offline:\n" + json.dumps(notes, indent=2)
        res = bridge.call_live("write_notes", {"track_index": track_idx, "slot_index": slot_idx, "replace": True, "notes": notes}, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Parsed ASCII drum grid and wrote {len(notes)} drum hits into track {track_idx + 1}, slot {slot_idx + 1}."
        return f"Failed to write drum grid to track {track_idx + 1}, slot {slot_idx + 1}: {res}"

    if fn_name == "live_analyze_mix":
        if not bridge or not getattr(bridge, "call_live", None):
            return "ERROR: Live Actions Bridge is not connected."
        set_data = bridge.call_live("read_set", {"include": ["tracks", "mixer", "devices"]})
        if not isinstance(set_data, dict) or not set_data.get("ok"):
            return f"Failed to read set state: {set_data}"
        from mix_checker import analyze_mix_heuristics
        report = analyze_mix_heuristics(set_data.get("set") or {})
        lines = [f"=== Mix Health Audit: {report['headline']} ==="]
        if report["critical_issues"]:
            lines.append("\nCRITICAL ISSUES:")
            lines.extend(f"  [!] {iss}" for iss in report["critical_issues"])
        if report["warnings"]:
            lines.append("\nWARNINGS:")
            lines.extend(f"  [-] {w}" for w in report["warnings"])
        if report["recommendations"]:
            lines.append("\nRECOMMENDATIONS:")
            lines.extend(f"  [*] {rec}" for rec in report["recommendations"])
        if not report["critical_issues"] and not report["warnings"]:
            lines.append("All gain staging, low-end centering, and master limiter checks passed.")
        return "\n".join(lines)

    if fn_name == "live_list_recipes":
        from recipes import list_recipes
        cat = args.get("category")
        recs = list_recipes(category=cat, capabilities=live_capabilities(settings))
        return json.dumps({"ok": True, "total": len(recs), "recipes": recs}, indent=2)

    if fn_name == "live_apply_recipe":
        from recipes import apply_recipe
        rec_id = str(args.get("recipe_id") or "")
        overrides = args.get("overrides") or {}
        res = apply_recipe(
            rec_id, overrides=overrides, bridge=bridge, capabilities=live_capabilities(settings)
        )
        return mv_json(res, fn_name)

    if fn_name == "live_session_diff":
        if not bridge or not getattr(bridge, "call_live", None):
            return "ERROR: Live Actions Bridge is not connected."
        prev_snap = args.get("previous")
        if not isinstance(prev_snap, dict):
            return "ERROR: 'previous' must be a valid snapshot dictionary."
        curr_snap = bridge.call_live("session_snapshot", {"include_clips": True, "include_devices": True})
        if not isinstance(curr_snap, dict) or not curr_snap.get("ok"):
            return f"Failed to capture current session snapshot: {curr_snap}"
        from session_verifier import compute_session_diff
        # `prev_snap` is whatever the model captured earlier from live_session_snapshot's own
        # reply, which already went through model_view (1-based, no raw `path`) on the way out --
        # convert curr_snap the same way so the two sides are shape-comparable before diffing.
        diff_res = compute_session_diff(prev_snap, model_view(curr_snap, fn_name))
        return json.dumps(diff_res, indent=2)

    if bridge is None or not getattr(bridge, "call_live", None):
        return (
            "ERROR: Live Actions Bridge is not connected. "
            "Please ensure Ableton Live is running with 'Live Actions Bridge.amxd' loaded on an audio track."
        )

    if fn_name == "live_add_shaped_automation":
        from algorithmic_generators import generate_shaped_automation
        track_ref: dict[str, Any] = {}
        if args.get("track_index") is not None:
            track_ref["track_index"] = _int(args.get("track_index"), 0)
        elif args.get("track_name"):
            track_ref["track_name"] = str(args.get("track_name"))
        else:
            track_ref["track_index"] = 0
        s_idx = _int(args.get("slot_index"), 0)
        param_name = str(args.get("parameter_name") or "")
        dev_idx = _int(args.get("device_index"), 0)
        shape = str(args.get("shape") or "sine")
        cycles = _float(args.get("cycles"), 1.0)
        min_v = _float(args.get("min_value"), 0.0)
        max_v = _float(args.get("max_value"), 1.0)
        points = _int(args.get("points"), 32)
        length = args.get("length")
        t_idx = track_ref.get("track_index")
        if length is None:
            clip_data = bridge.call_live("read_clip", {**track_ref, "slot_index": s_idx, "include": ["timing"]})
            if not isinstance(clip_data, dict) or not clip_data.get("ok"):
                return f"Failed to read clip length for {track_ref}, slot {s_idx + 1}: {clip_data}"
            length = clip_data.get("length") or 4.0
            t_idx = clip_data.get("track_index", t_idx)
        length = float(length)
        envelope = generate_shaped_automation(shape, cycles, min_v, max_v, points, length)
        res = bridge.call_live(
            "set_clip_automation",
            {
                **track_ref,
                "slot_index": s_idx,
                "parameter_name": param_name,
                "device_index": dev_idx,
                "envelope_data": envelope,
            },
            timeout=12.0,
        )
        if isinstance(res, dict):
            t_idx = res.get("track_index", t_idx)
        track_label = f"track {t_idx + 1}" if isinstance(t_idx, int) else str(track_ref.get("track_name") or "?")
        if isinstance(res, dict) and res.get("ok"):
            return f"Wrote a {shape} automation curve ({res.get('points_added', len(envelope))} points, {cycles} cycle(s)) for '{param_name}' on {track_label}, slot {s_idx + 1}."
        return f"Failed to write shaped automation for '{param_name}' on {track_label}, slot {s_idx + 1}: {res}"

    if fn_name == "live_create_drum_pattern":
        from algorithmic_generators import create_drum_pattern_notes
        t_idx = _int(args.get("track_index"), 0)
        s_idx = _int(args.get("slot_index"), 0)
        pat = args.get("pattern") or {}
        if not isinstance(pat, dict) or not pat:
            return "ERROR: 'pattern' must be a dictionary mapping voice names to step strings."
        def_vel = _int(args.get("default_velocity"), 100)
        bpb = _float(args.get("beats_per_bar"), 4.0)
        len_b = _float(args.get("length_beats")) if args.get("length_beats") is not None else None
        notes, clip_len = create_drum_pattern_notes(pat, default_velocity=def_vel, beats_per_bar=bpb, length_beats=len_b)
        if not notes:
            return "No drum notes generated from pattern."
        clip_name = str(args.get("name") or "Drum Pattern")
        write_payload = {
            "track_index": t_idx,
            "slot_index": s_idx,
            "name": clip_name,
            "length_beats": clip_len,
            "replace": True,
            "notes": notes,
        }
        res = bridge.call_live("write_notes", write_payload, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Successfully created drum pattern clip '{clip_name}' ({len(notes)} notes, length={clip_len} beats) on track {t_idx + 1} slot {s_idx + 1}."
        return str(res)

    if fn_name == "live_create_chord_progression":
        from algorithmic_generators import create_chord_progression_notes
        t_idx = _int(args.get("track_index"), 0)
        s_idx = _int(args.get("slot_index"), 0)
        chords = args.get("chords") or []
        key_sig = str(args.get("key") or "C")
        vc = str(args.get("voicing") or "triad")
        bpc = args.get("beats_per_chord", 4.0)
        len_b = _float(args.get("length_beats")) if args.get("length_beats") is not None else None
        octave = _int(args.get("base_octave"), 3)
        vel = _int(args.get("velocity"), 85)
        notes, clip_len = create_chord_progression_notes(
            chords, key=key_sig, voicing=vc, beats_per_chord=bpc,
            length_beats=len_b, base_octave=octave, velocity=vel
        )
        if not notes:
            return "No chord notes generated from progression."
        clip_name = str(args.get("name") or f"Chords {key_sig}")
        write_payload = {
            "track_index": t_idx,
            "slot_index": s_idx,
            "name": clip_name,
            "length_beats": clip_len,
            "replace": True,
            "notes": notes,
        }
        res = bridge.call_live("write_notes", write_payload, timeout=14.0)
        if isinstance(res, dict) and res.get("ok"):
            return f"Successfully created chord progression clip '{clip_name}' ({len(notes)} notes, length={clip_len} beats, key='{key_sig}', voicing='{vc}') on track {t_idx + 1} slot {s_idx + 1}."
        return str(res)

    if fn_name == "live_edit_track":
        op = str(args.get("op") or "").lower()
        t_idx = _int(args.get("track_index"), 0)
        if op == "delete":
            res = bridge.call_live("delete", {"type": "track", "track_index": t_idx}, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "duplicate":
            res = bridge.call_live("duplicate", {"type": "track", "track_index": t_idx}, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "rename":
            new_name = str(args.get("name") or "")
            res = bridge.call_live("update_track", {"track_index": t_idx, "name": new_name}, timeout=10.0)
            return mv_json(res, fn_name)
        else:
            return f"Invalid op '{op}'. Must be 'delete', 'duplicate', or 'rename'."

    if fn_name == "live_edit_clip":
        op = str(args.get("op") or "").lower()
        t_idx = _int(args.get("track_index"), 0)
        s_idx = _int(args.get("slot_index"), 0)
        if op == "delete":
            res = bridge.call_live("delete", {"type": "clip", "track_index": t_idx, "slot_index": s_idx}, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "duplicate":
            payload = {"type": "clip", "track_index": t_idx, "slot_index": s_idx}
            if "target_slot_index" in args:
                payload["to_slot"] = _int(args.get("target_slot_index"))
            res = bridge.call_live("duplicate", payload, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "rename":
            new_name = str(args.get("name") or "")
            res = bridge.call_live("update_clip", {"track_index": t_idx, "slot_index": s_idx, "name": new_name}, timeout=10.0)
            return mv_json(res, fn_name)
        else:
            return f"Invalid op '{op}'. Must be 'delete', 'duplicate', or 'rename'."

    if fn_name == "live_edit_scene":
        op = str(args.get("op") or "").lower()
        sc_idx = _int(args.get("scene_index"), 0)
        if op == "delete":
            res = bridge.call_live("delete", {"type": "scene", "scene_index": sc_idx}, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "duplicate":
            res = bridge.call_live("duplicate", {"type": "scene", "scene_index": sc_idx}, timeout=10.0)
            return mv_json(res, fn_name)
        elif op == "rename":
            new_name = str(args.get("name") or "")
            res = bridge.call_live("update_scene", {"scene_index": sc_idx, "name": new_name}, timeout=10.0)
            return mv_json(res, fn_name)
        else:
            return f"Invalid op '{op}'. Must be 'delete', 'duplicate', or 'rename'."

    action = fn_name.replace("live_", "")
    if action == "update_set":
        action = "update_set"
    if action == "set_tempo":
        action = "update_set"
    if action == "run_action":
        action = "run_tool"
        args = {"tool_id": args.get("tool_id"), "payload": args.get("payload") or {}}

    timeouts = {
        "create_device": 22.0,
        "load_device": 22.0,
        "library": 20.0,
        "read_set": 14.0,
        "read_track": 12.0,
        "read_device": 12.0,
        "live_api": 12.0,
        "api": 12.0,
        "detect_key": 16.0,
        "capture_midi": 10.0,
        "back_to_arranger": 10.0,
        "re_enable_automation": 10.0,
        "crossfader": 10.0,
        "set_crossfader": 10.0,
        "create_take_lane": 10.0,
        "fold_state": 10.0,
        "set_fold_state": 10.0,
        "groove_pool": 10.0,
        "duplicate_loop": 10.0,
        "undo": 8.0,
        "redo": 8.0,
        "jump_to_time": 8.0,
        "set_overdub": 8.0,
        "read_arrangement_length": 8.0,
        "move_arrangement_clip": 12.0,
        "read_arrangement_notes": 12.0,
        "write_arrangement_notes": 14.0,
        "remove_arrangement_notes": 12.0,
        "read_take_lanes": 10.0,
        "update_take_lane": 10.0,
        "create_take_lane_clip": 12.0,
        "batch_tracks": 10.0,
        "stop_all_clips": 8.0,
        "tap_tempo": 8.0,
        "continue_playing": 8.0,
        "scrub": 8.0,
        "jump_cue": 8.0,
        "set_punch": 8.0,
        "set_cue_volume": 8.0,
        "move_device": 10.0,
        "read_drum_pads": 12.0,
        "update_drum_pad": 10.0,
        "focus_view": 8.0,
        "session_snapshot": 14.0,
        "inspect_plugin": 10.0,
        "map_rack_magnitude": 12.0,
        "read_link_status": 8.0,
        "get_selected": 8.0,
        "clear_clip_envelopes": 8.0,
        "set_clip_automation": 12.0,
    }
    timeout = timeouts.get(action, 10.0)
    res = bridge.call_live(action, args, timeout=timeout)
    if not isinstance(res, dict):
        return str(res)
    if res.get("live_version"):
        live_version.record(res["live_version"])
    if not res.get("ok"):
        not_applied = res.get("not_applied") or res.get("params_skipped")
        if res.get("error"):
            err = res["error"]
            if not_applied:
                err += " (not applied: " + ", ".join(not_applied) + ")"
        elif not_applied:
            # No `error` key -- `message` here is the bridge's success-shaped summary
            # (e.g. "Updated device 'Simpler'"), not a description of the failure.
            # Build the real reason from what was actually skipped instead of
            # printing that success text under an ERROR prefix.
            err = "Could not apply: " + ", ".join(not_applied)
        else:
            err = res.get("message") or "Unknown error"
        return f"ERROR from Live Actions Bridge: {err}"

    if fn_name == "live_get_selected" and isinstance(res, dict) and res.get("ok"):
        sel = res.get("selected", {})
        trk = sel.get("track") or {}
        scn = sel.get("scene") or {}
        dev = sel.get("device") or {}
        clp = sel.get("clip") or {}
        lines = ["Current Live GUI Selection:"]
        if trk and trk.get("name"):
            lines.append(f"  - Track: {live_track_label(trk)} ({trk.get('kind')})")
        else:
            lines.append("  - Track: (none)")
        if scn and scn.get("name") is not None:
            scn_idx = scn.get("index")
            scn_n = (scn_idx + 1) if isinstance(scn_idx, int) else "?"
            lines.append(f"  - Scene: [{scn_n}] '{scn.get('name')}'")
        if dev and dev.get("name"):
            dev_idx = dev.get("index")
            dev_n = (dev_idx + 1) if isinstance(dev_idx, int) else "?"
            lines.append(f"  - Device: [{dev_n}] '{dev.get('name')}' ({dev.get('class_name')})")
        if clp and clp.get("name") is not None:
            lines.append(f"  - Clip: '{clp.get('name')}' ({clp.get('length')} beats, midi={clp.get('is_midi')})")
        return "\n".join(lines)

    # (live_library used to merge its disk results with the bridge's palLibrary
    # stub here. It now answers entirely from disk + engine E2 and returns
    # before reaching the bridge, so there is nothing left to merge.)

    if "set" in res and isinstance(res.get("set"), dict):
        s = res["set"]
        tracks = s.get("tracks") or []
        t_summaries = []
        for t in tracks:
            slots_with_clips = [(sl["index"] + 1) for sl in t.get("clip_slots") or [] if sl.get("has_clip")]
            clips_str = f"clips on slots {slots_with_clips}" if slots_with_clips else "empty"
            devices = t.get("devices") or []
            dev_names = [d.get("name") or "?" for d in devices]
            if len(dev_names) > 6:
                dev_str = ", ".join(dev_names[:6]) + f" (+{len(dev_names) - 6} more)"
            elif dev_names:
                dev_str = ", ".join(dev_names)
            else:
                dev_str = "(none)"
            t_summaries.append(
                f"  - {live_track_label(t)} | {t.get('kind')} | devices: {dev_str} | {clips_str}"
            )
        tracks_text = "\n".join(t_summaries) if t_summaries else "  (No tracks)"
        tracks_header = (
            "Track and slot numbers below are exactly what Live's own UI shows (1-based) -- "
            "Live track 1 is the first track. Numbers inside track NAMES are just text the user "
            "typed and do NOT indicate position -- never infer a number from a name.\n"
        )
        scale = s.get("scale") or {}
        scale_txt = scale.get("label") or "(off)"
        extra = ""
        if s.get("returns"):
            extra += "\nReturns: " + ", ".join(r.get("name", "?") for r in s["returns"])
        if s.get("locators"):
            extra += "\nLocators: " + ", ".join(
                "%s@%s" % (c.get("name"), c.get("time")) for c in s["locators"]
            )
        if s.get("tracks_truncated"):
            extra += (
                f"\n(Track list truncated to {len(tracks)} of {s.get('track_count')} total -- "
                "ask about a specific track by index for one outside this list.)"
            )
        return (
            f"{live_version.describe()} | Live Set: '{s.get('name')}' | Tempo: {s.get('tempo')} BPM | "
            f"Sig: {s.get('time_signature')} | Scale: {scale_txt} | Playing: {s.get('is_playing')}\n"
            f"Tracks ({s.get('track_count')} total). {tracks_header}{tracks_text}{extra}"
        )
    if "message" in res:
        text = str(res["message"])
        skipped = res.get("params_skipped") or res.get("not_applied")
        if skipped:
            text += "\nCould not set:\n" + "\n".join(f"  - {s}" for s in skipped)
        handled = {"ok", "message", "params_skipped", "not_applied"}
        display = model_view(res, fn_name)
        for k, v in display.items():
            if k in handled:
                continue
            if isinstance(v, list):
                if not v:
                    continue
                items = [
                    str(item.get("name")) if isinstance(item, dict) and "name" in item else str(item)
                    for item in v
                ]
                shown = items[:12]
                text += f"\n{k}:\n" + "\n".join(f"  - {it}" for it in shown)
                if len(items) > 12:
                    text += f"\n  (+{len(items) - 12} more)"
            elif isinstance(v, dict):
                text += f"\n{k}: {json.dumps(v)}"
            else:
                text += f"\n{k}: {v}"
        return text
    return mv_json(res, fn_name)


# ── Knowledge helpers ──────────────────────────────────────────────────────────

def _read_text(path: Path, limit: int) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n\n[truncated]"
    return text


def _sample_load_gate_text(live_ver: dict[str, Any]) -> str:
    """Resolve whether `SimplerDevice.replace_sample` (Live 12.4+) exists in the
    running build into a stated fact, instead of a fixed claim the model has to
    guess about or ask the user to confirm. See app/live_version.py."""
    if not live_ver.get("known"):
        return (
            "Live's version has not been read yet -- `live_connect` reports it. Do not guess "
            "a version, and do not refuse a sample-load on version grounds before reading it."
        )
    major, minor, patch = live_ver.get("major"), live_ver.get("minor"), live_ver.get("patch")
    desc = f"Ableton Live {major}.{minor}.{patch}"
    if (major, minor) >= (12, 4):
        return (
            f"{desc} is running. `SimplerDevice.replace_sample` exists in this build -- the "
            "`sample` param on `live_update_device` / `live_create_device`, and `p<note>/sample` "
            "on a Drum Rack pad, work. Never tell the user to drag a file in by hand."
        )
    return (
        f"{desc} is running, so `SimplerDevice.replace_sample` does not exist here -- the "
        "`sample` param will not load. Use `live_create_clip` with `sample_file` on an audio "
        "track instead, or `live_load_browser_item` if the browser engine is online."
    )


def build_system_prompt(
    settings: dict[str, Any],
    live_line: str,
    bridge_online: bool = False,
    e2_online: bool = False,
    tts_online: bool = False,
    live_ver: dict[str, Any] | None = None,
) -> str:
    """Assemble Genius's system prompt.

    `e2_online` is threaded exactly like `bridge_online` and for the same
    reason: what Genius can actually do depends on which engines are answering
    right now, and a prompt that asserts a fixed answer will confidently promise
    (or refuse) browser work that doesn't match reality. Engine E2 is the
    LiveActionsRS Remote Script; it can be off while the OSC bridge is fine.
    `tts_online` is the same idea with a purely local answer: it is just "has the
    user saved a TTS profile", since without one there is nothing to generate with.
    `live_ver` is the same idea again: the shape `live_version.current()` returns, so
    a version-gated capability (SimplerDevice.replace_sample, Live 12.4+) is stated
    as a resolved fact about the build that's actually running, not a fixed claim
    the model has to accept, question, or ask the user to confirm. Named `live_ver`
    rather than `live_version` to avoid shadowing the `live_version` module import
    used a few lines below for `.describe()`.
    """
    live_ver = live_ver if live_ver is not None else {"known": False}
    sample_load_gate = _sample_load_gate_text(live_ver)
    pinned_tts = str(settings.get("active_tts_profile") or "").strip()
    tts_pin_note = (
        f" A profile is pinned in Settings: '{pinned_tts}' is the ONLY voice `live_tts_vocal` may use "
        "right now -- a different `profile` name or a `voice` override is refused, not substituted."
        if pinned_tts else ""
    )
    skill = _read_text(GENIUS_DIR / "skills" / "live-actions-genius" / "SKILL.md", MAX_SKILL_CHARS)
    knowledge = Path(str(settings.get("knowledge_dir") or ""))
    samples = Path(str(settings.get("samples_dir") or ""))
    library = _read_text(knowledge / "INDEX.md", MAX_INDEX_CHARS)
    copied_index = _read_text(GENIUS_DIR / "indexes" / "INDEX.md", MAX_INDEX_CHARS)
    if not library:
        library = copied_index

    active_agent, _allowed_tools = agent_registry.resolve_active(settings)
    agent_persona = None
    if active_agent:
        agent_persona = active_agent["body"].strip()
        if len(agent_persona) > MAX_AGENT_CHARS:
            agent_persona = agent_persona[:MAX_AGENT_CHARS] + "\n\n[truncated]"

    live_control_section = (
        "\n\n## Live control (via the Live Actions Bridge)\n"
        "You control Ableton through `live_*` tools. This app is independent of Producer Pal: do not call "
        "producer-pal__ppal-* — those MCP tools are not wired here.\n"
        "- Call `live_connect` first when the ask touches the Live Set.\n"
        "- Numbering (v1.0.32): every `*_number` field (track_number, slot_number, scene_number, "
        "device_number, clip_number, ...) is exactly what Live's own UI shows -- Live's track 1 is "
        "track_number 1. Never shift by one in either direction; do not compute track_number-1 or "
        "track_index+1 yourself, the bridge does that translation. A `*_index` key is never a valid "
        "argument to a live_* tool and will come back as an error telling you the matching `*_number` "
        "name to use instead -- `live_api` is the one exception, since it addresses Live's Object Model "
        "directly and stays 0-based there, matching the LOM docs. Return tracks use `return_letter` "
        "(A, B, C...), never a number. The master track uses `track_type=\"master\"`, not a track number. "
        "Digits inside a track's NAME (e.g. \"3-Instrument Rack\") are free text the user typed and do "
        "not indicate position -- never infer a number from a name; `track_name` is still accepted "
        "wherever a tool takes track_number, as an alternative addressing method. Always call "
        "`live_read_set` (include tracks) before you change anything, even if you think you already "
        "know the numbers from earlier in the conversation -- the set can change between turns. If the "
        "user says an action hit the wrong track, re-read the set before retrying rather than guessing a "
        "different number. In your reply, name the track the way Live shows it (e.g. \"Live track 3 "
        "\\\"Bass\\\"\") so a mismatch is caught immediately instead of costing another turn.\n"
        "- Tool output is ground truth: quote or closely paraphrase what a live_* tool actually returned. "
        "Never invent a \"raw result\", a value, a device/parameter name, or a count that didn't come back "
        "from a tool call. If a tool errored or returned nothing useful, say so plainly rather than filling "
        "the gap with a plausible-sounding guess.\n"
        "- Native devices: `live_create_device` (Drum Rack, Drift, Simpler, Reverb, EQ Eight, Scale, Arpeggiator…), "
        "Live 12.3+ only. Omit device_name to list insertable native device names. "
        + (
            "For VST/AU, Max for Live devices and browser presets use `live_load_browser_item` (find them first "
            "with `live_browse` or `live_library` search). "
            if e2_online
            else "You cannot add VST/AU, Max for Live devices, or browser presets — that needs the browser engine, "
            "which is offline. "
        )
        + "Already-present VST/AU: `live_inspect_plugin` then `live_read_device` "
        "(include params) and `live_update_device` for Live-visible knobs only. Do not invent parameter names; "
        "use names the inspect/read returned. Label results LOM-visible only (wavetable/mod-matrix may be missing). "
        "`presets[]` is a catalog, not a load command.\n"
        "- Tracks / returns / scenes / clips / notes / routing / sends / mixer / locators / scale / playback / "
        "select / duplicate / delete / library search / context / raw LOM (`live_api`) are all available.\n"
        "- Drum kits: `live_create_device` Drum Rack, `live_find_samples` or `live_library` to find a real absolute "
        "path for each drum sound, then `live_update_device` (or bundle into the same `live_create_device` call) "
        "with params named `p<note>/sample` set to that path (C1=36 kick, D1=38 snare, D#1=39 clap, F#1=42 hat) — "
        f"this actually loads the sample onto the pad. {sample_load_gate} "
        "`live_write_notes` writes the pattern.\n"
        + (
            "- Vocals and audio files (both run on the desktop host, not in Live): `live_tts_vocal` generates a "
            f"SPOKEN vocal WAV from text with the user's saved TTS profile,{tts_pin_note} and `live_audio_op` runs ffmpeg edits "
            "on any file (trim, fades, gain, normalize, convert, reverse, pitch & time-stretch, echo, chorus, "
            "tremolo, vibrato, EQ, bitcrush, and tone/noise/silence generators -- call it with no `operation` to "
            "list them). Two things never to get wrong: TTS models SPEAK, they do not sing, so never promise a "
            "sung result; and the length of a generation is a RESULT of the text and speed, not something you "
            "set, so quote the durationSec that came back and use `live_audio_op` trim/silence if an exact "
            "length is wanted. Generating bills the user's own API key, so the app asks them to approve each "
            "call -- if they decline, report it and stop. To get the finished file into Live: `live_update_device` "
            "with a param named `sample` (a Simpler on the track), the same `sample` param bundled into "
            "`live_create_device` Simpler, or `live_create_clip` with sample_file (an audio track).\n"
            if tts_online
            else "- You cannot generate vocals: no TTS profile is saved, so `live_tts_vocal` is not available. "
            "If the user asks for one, tell them to add a profile in Preferences > TTS Vocal Profiles "
            "(provider + API key + voice ID). `live_audio_op` still works for ffmpeg edits on existing files.\n"
        )
        + 
        "- When asked to make a beat/melody/chords: do it. Do not stop after reading the set.\n"
        "- What key/scale/mode is this in: call `live_detect_key`, never guess it from `live_read_clip` note data — "
        "it runs the actual Krumhansl-Schmuckler correlation, eyeballing pitches is not reliable. "
        "If asked why it picked a mode (e.g. 'why Dorian, not C Major') or the result says 'close call', "
        "explain using the tool's own signals — which pitch anchors the bass, lands on downbeats, or the "
        "phrase resolves to — not a fabricated rationale; a real tie should be reported as a tie.\n"
        "- Recording a Session scene into the Arrangement timeline (not a new Session scene — that's "
        "live_create_scene capture=true): `live_record_to_arrangement` op=start with scene_index, optionally "
        "duration_beats to auto-stop; op=stop to end it explicitly. Never blocks — always returns immediately.\n"
        "- Arrangement timeline editing: `live_duplicate_to_arrangement` directly copies a Session clip into the Arrangement timeline "
        "at a specific beat position (destination_time); `live_read_arrangement_clips` (or live_read_track include=['arrangement-clips']) "
        "inspects all clips on the Arrangement timeline with start/end beats and length; `live_update_arrangement_clip` renames, colors, "
        "or mutes an Arrangement clip; `live_delete` type='arrangement_clip' removes a timeline clip.\n"
        "- Real-time VU/peak metering: `live_read_meter` reads output_meter_left, output_meter_right, and output_meter_level "
        "(0.0-1.0) while audio is playing on any track, return track, or master bus.\n"
        "- Rack macros: `live_read_macros` inspects all macro parameters on a Rack device; `live_update_macro` sets macro "
        "values by name or index (with native value or normalized 0.0-1.0).\n"
        "- Surgical note removal: `live_remove_notes` deletes notes in a bounded pitch/time region without erasing the whole clip.\n"
        "- Audio analysis & Ears: `live_analyze_audio` measures true peak (dBTP), integrated/short-term LUFS, 10-band spectrum, "
        "spectral centroid (brightness), transient punch (band crest dB), and stereo width. `live_compare_audio` compares before/after "
        "to evaluate tuning deltas with a headline.\n"
        "- Real-time loopback recording: `live_record_audio` captures Live's playback output via Windows loopback (Voicemeeter/virtual cable); "
        "`live_record_and_analyze` captures and measures in a single step for closed-loop sound design / parameter adjustment.\n"
        "- Algorithmic MIDI Generators: `live_generate_euclidean` generates Bjorklund Euclidean rhythms directly into a clip slot; "
        "`live_generate_chords` writes voiced progressions with voice leading (styles: drop2, close, open, shell, rootless, spread); "
        "`live_generate_walking_bass` writes jazz walking basslines with chromatic approaches; `live_transform_clip` applies motif transformations "
        "(invert around pitch axis, retrograde, retrograde inversion, augment, diminish, transpose, humanize); "
        "`live_write_drum_grid` writes ASCII text drum patterns into clip notes.\n"
        "- Offline .als Project Tools: `als_summary` (quick project overview), `als_list_tracks` (all tracks/clips/devices), "
        "`als_extract_midi` (extract clip notes from .als XML without opening Live), `als_diff` (compare two project versions), "
        "and `als_find_unfinished` (lint unfinished project indicators: uncolored clips, default names, soloed tracks, empty slots).\n"
        "- M4L Production Shortcuts: `live_capture_midi` (retrieves Live's retrospective capture buffer), `live_back_to_arranger` "
        "(re-links playback to arrangement), `live_re_enable_automation` (re-arms overridden automation), `live_set_crossfader` "
        "(sets master crossfader value/curve), `live_create_take_lane` (creates take lane on track), `live_set_fold_state` (track/mixer unfold), "
        "`live_groove_pool` (inspects or applies groove pool presets), and `live_duplicate_loop` (doubles loop length duplicating notes).\n"
        "- Song Globals, Diagnostics & Note-Selection Editing (v1.0.39): `live_set_loop_region` (arrangement loop brace on/off + start/length), "
        "`live_set_groove_amount` / `live_set_swing` (global groove pool amount / swing amount), `live_nudge` (momentary tempo nudge up/down), "
        "`live_set_appointed_device` (appoints a device as the active control-surface target), `live_set_automation_record` "
        "(Session View automation recording on/off); `live_read_param_range` (a parameter's min/max, quantization, enum items, display value -- "
        "check this before guessing a legal value) and `live_set_param_raw` (writes the raw underlying value directly, bypassing display-string "
        "parsing); `live_show_message` (posts to Live's own status bar), `live_read_dialog` (reads/dismisses a modal dialog that's blocking the "
        "UI -- try this if another live_* call times out unexpectedly), `live_read_cpu` (audio engine CPU usage), `live_view_control` "
        "(show/hide/focus a Live UI view); `live_read_selected_notes` / `live_transform_selected_notes` (read or transform only the notes "
        "currently selected in the MIDI editor, not the whole clip -- ask the user to select notes first if none come back).\n"
        "- Heuristic Mix Checker: `live_analyze_mix` performs structural mix checks (low-end clashing under 120Hz, stereo panning on bass, "
        "fader headroom >0dB, missing master limiter, soloed/muted anomalies).\n"
        "- Transport & Timeline Utilities: `live_undo` (undoes last action in Live), `live_redo` (redoes last undone action), "
        "`live_jump_to_time` (moves arrangement playhead to beat position without playback), `live_set_overdub` (toggles arrangement/session overdub recording), "
        "and `live_read_arrangement_length` (queries total arrangement duration in beats).\n"
        "- Arrangement Timeline Note Manipulation & Clip Moving: `live_read_arrangement_notes` (reads MIDI notes directly from an arrangement clip), "
        "`live_write_arrangement_notes` (writes or appends MIDI notes into an arrangement clip), `live_remove_arrangement_notes` "
        "(surgically deletes notes in a pitch/time bounding box from an arrangement clip), and `live_move_arrangement_clip` "
        "(repositions an arrangement clip to a new start time or track).\n"
        "- Take Lane Deep Management: `live_read_take_lanes` (lists all take lanes on an arrangement track), `live_update_take_lane` "
        "(renames an existing take lane), and `live_create_take_lane_clip` (creates an empty MIDI clip directly on a take lane).\n"
        "- Batch Operations & Global Transport (v1.0.20): `live_batch_tracks` (unarm_all, unmute_all, unsolo_all, solo_exclusive), "
        "`live_stop_all_clips` (stops all playing session clips), `live_tap_tempo` (tap tempo), `live_continue_playing` "
        "(resumes playback from playhead), `live_scrub` (scrubs forward/backward by beats), `live_jump_cue` (next/prev locator jump), "
        "`live_set_punch` (punch-in/out toggles), and `live_set_cue_volume` (headphone/preview volume).\n"
        "- Device Reordering, Drum Pads & View Focus (v1.0.20): `live_move_device` (repositions device in chain), `live_read_drum_pads` "
        "(enumerates Drum Rack pad names, mutes, solos, chains), `live_update_drum_pad` (renames, mutes, or solos individual drum pads), "
        "`live_focus_view` (focuses Session, Arrangement, Detail, Clip, or Device view, with draw_mode and follow_mode), "
        "and `live_update_clip` / `live_update_track` now support launch modes, quantization, velocity sensitivity, audio gain, "
        "pitch shift, warp modes, RAM mode, track monitoring, delay ms, and crossfade routing.\n"
        "- Verification Loop & Session Diffing (v1.0.21): `live_session_snapshot` (captures deep JSON set state: tempo, tracks, volumes, pans, clips, devices) "
        "and `live_session_diff` (compares previous snapshot with current Live state to compute exact path deltas and verify mutations).\n"
        "- Ableton Link & Sync Status (v1.0.21): `live_read_link_status` (discovers is_link_enabled, num_peers, quantum, start_stop_sync, tempo_sync).\n"
        "- Declarative Genre Recipe Engine (v1.0.21): `live_list_recipes` (lists 14 embedded production recipes) and `live_apply_recipe` "
        "(automatically builds multi-step track/device/clip sequences across tech-house, reese bass, 808 subs, lofi jazz/neo-soul chords, and parallel racks).\n"
        "- Deep Plugin & Device Discovery (v1.0.21): `live_inspect_plugin` (introspects native/VST/AU/M4L devices on tracks, discovering true class names, total parameters, and factory/user VST presets).\n"
        "- Rack Magnitude Mapping (v1.0.23): `live_map_rack_magnitude` traverses an Audio or MIDI Effect Rack's chains and nested devices, auto-detects Dry/Wet or Mix/Amount blend parameters, renames Macro 1 to 'Magnitude', binds/maps them, and optionally scales wetness via `value_normalized` (0.0–1.0).\n"
        "- Clip Lifecycle, Groove & Automation (v1.0.25): "
        "`live_set_clip_follow_action` / `live_get_clip_follow_action` (follow actions A/B, chance, time, enabled); "
        "`live_set_clip_launch_mode` (trigger/gate/toggle/repeat, launch quantization, legato); "
        "`live_set_clip_fades` (audio clip fade-in/out start+end in beats); "
        "`live_set_clip_markers` (start/end markers and loop start/end times); "
        "`live_manage_warp_markers` (get/add/delete warp markers by beat_time on audio clips); "
        "`live_set_clip_automation` (write staircase envelope to a named parameter from {time,value} data); "
        "`live_get_clip_automation` (check has_envelopes flag); "
        "`live_commit_groove` (bake quantize groove permanently into MIDI notes via quantize grid + amount); "
        "`live_add_shaped_automation` (generate sine/triangle/saw/square/random shaped envelope and write it to a named parameter). "
        "Notes (live_write_notes / live_write_arrangement_notes) now accept `probability` (0.0–1.0) and `velocity_deviation` (–127 to +127) per note. "
        "`live_move_device` now supports relative movement via `direction='left'|'right'`.\n"
        "- `live_api` is the Genius Live API equivalent. Use specialized tools first.\n"
        "- `live_context` is production habits, not manuals.\n"
        "- 4 bars in 4/4 = length_beats 16. Velocities: kick 110-120, snare 100-115, hats 75-105.\n"
        + (
            "- Live's browser (the library panel on the left of Live) is available: `live_browse` walks it "
            "(Sounds, Drums, Instruments, Audio/MIDI Effects, Max for Live, Plug-ins, Clips, Samples, "
            "User Library, Packs), `live_library` search finds items across it, `live_preview_browser_item` "
            "auditions one without touching the Set, and `live_load_browser_item` loads it onto a track. "
            "Only items reported `loadable` can be loaded — a folder cannot. Prefer the category+path a browse "
            "or search actually returned over a guessed path.\n"
            "- Cannot: stem separation.\n"
            if e2_online
            else "- Cannot: add VST/AU from browser, stem separation, or anything "
            "needing Live's browser (packs, plug-in insertion) — the browser engine (LiveActionsRS) is offline. "
            "Do not offer to browse, audition, or load presets/plug-ins while it is. "
            "Already-present VST/AU knobs: "
            "`live_inspect_plugin` / `live_read_device` / `live_update_device` (LOM-visible only). "
            "Do the native half for the rest, then hand off with a citation.\n"
        )
        + (
            "Status: LIVE ACTIONS BRIDGE ONLINE — live_* tools are ready."
            if bridge_online
            else "Status: BRIDGE OFFLINE — drop Live Actions Bridge.amxd on an audio track."
        )
        + (
            " Browser engine ONLINE — Live's library is readable and loadable."
            if e2_online
            else " Browser engine OFFLINE — to enable it, in Live open Preferences > Link/Tempo/MIDI and set a free"
            ' Control Surface slot to "LiveActionsRS", then restart Live.'
        )
        + " " + live_version.describe() + "."
    )

    library_section = (
        "\n\n## Genius knowledge library\n"
        "Answer how-to from the local library before general knowledge. There are two knowledge sources, in "
        "this order: the knowledge database first, then the user's own Knowledge folder (their notes and "
        "manuals).\n"
        "1. The INDEX below is the Decide-first map. Match the ask to a topic.\n"
        "2. Try `library_db_search` FIRST for anything it plausibly covers: beat-making recipes by genre, "
        "preset-rack breakdowns, mix engineering (gain, pan, EQ curves), Vital sound design, beginner music "
        "theory, and notes on Ableton remote-control projects. It is real FTS5 search with real citations "
        "(doc title + section). The user may have added datasets of their own — topic='?' lists everything, "
        "always check that list before assuming a topic doesn't exist.\n"
        "3. Fall back to the Knowledge folder (`library_search`, then `library_read`) when the database has "
        "nothing on the ask. It may be empty: if neither source covers the question, say so and answer from "
        "general knowledge, clearly labelled as such.\n"
        "4. Cite document + section either way, and say which source (database topic vs. Knowledge folder) "
        "the answer came from when it matters. After the reading: do the native Live half with `live_*`.\n"
    )

    stock_persona = (
        "You are Genius inside Live Actions — Live control plus the studio library, running through "
        "the Live Actions Bridge. You are an expert music producer "
        "and music theorist: harmony, arrangement, sound design, mixing/mastering, genre convention, "
        "and the Ableton Live / Max for Live stack. Ground music-knowledge answers in the knowledge "
        "database and the user's library below rather than general knowledge alone, and control Ableton "
        "Live 12 when the ask touches the Live Set.\n"
    )

    return (
        (agent_persona + "\n" if agent_persona else stock_persona)
        + live_control_section
        + library_section
        + "\nLive Actions bridge status: "
        + (live_line or "unknown")
        + "\nKnowledge folder: "
        + (str(knowledge) if knowledge else "(not set)")
        + "\nKnowledge database: "
        + str(genius_db.db_root(settings))
        + "\nAbleton Samples folder: "
        + (str(samples) if samples else "(not set)")
        + "\nWhen asked about samples, kits, or one-shots, look in the Samples folder first.\n"
        + "\n--- Genius skill ---\n"
        + (skill or "(skill file missing)")
        + "\n\n--- Library INDEX ---\n"
        + (library or "(INDEX.md not found)")
        # Last, deliberately: these are the user's own standing instructions and
        # are supposed to outrank the stock style guidance above, so they sit
        # closest to the conversation rather than being buried mid-prompt.
        + custom_instructions.prompt_block(settings, current_live_set(live_line))
    )


# ── xAI API helpers ────────────────────────────────────────────────────────────

def extract_output_text(payload: dict[str, Any]) -> str:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for block in item.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    chunks.append(str(block.get("text") or ""))
    if chunks:
        return "".join(chunks).strip()
    choice = (payload.get("choices") or [{}])[0]
    if isinstance(choice, dict):
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def _extract_tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool call requests from a /responses payload."""
    calls: list[dict[str, Any]] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "function_call":
            calls.append(item)
    # Also handle chat/completions format
    choice = (payload.get("choices") or [{}])[0]
    if isinstance(choice, dict):
        for tc in choice.get("message", {}).get("tool_calls") or []:
            if isinstance(tc, dict):
                fn = tc.get("function") or {}
                calls.append({
                    "type": "function_call",
                    "call_id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "arguments": fn.get("arguments", "{}"),
                })
    return calls


def _api_error(code: Any, detail: str, url: str = "", model: str = "") -> RuntimeError:
    """An HTTP error as one readable sentence. A JSON error body (the useful Google / xAI ones) is passed
    through as before; a web page (any status) or an empty 404/405 means the address itself is wrong, and says where.
    503 (provider overloaded) and 429 (usage limit) get a short plain sentence instead of the JSON dump: the key
    is fine in both cases, and the fix is to wait or switch key/model in the chat header."""
    name = str(model or "").strip() or "This model"
    if str(code) == "503":
        return RuntimeError("%s is overloaded at the provider right now. Your key is fine. Try again in a minute, "
                            "or pick another key/model at the top of the chat." % name)
    if str(code) == "429":
        return RuntimeError("This key has hit its usage limit%s. Wait a bit, or pick another key/model at the top "
                            "of the chat." % ((" for " + model) if model else ""))
    text = str(detail or "").strip()
    is_page = text[:9].lower() == "<!doctype" or text[:5].lower() == "<html"
    if is_page or (not text and str(code) in ("404", "405")):
        where = (" from " + url) if url else ""
        what = "the server answered with a web page" if is_page else "the server sent no details"
        return RuntimeError("API %s%s: %s, not an API reply -- the endpoint address is probably wrong for this key. "
                            "Check Preferences -> AI provider -> Model & endpoint." % (code, where, what))
    return RuntimeError("API %s: %s" % (code, text[:400]))


def _post_json(url: str, api_key: str, body: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise _api_error(exc.code, detail, url, str(body.get("model") or "")) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach %s (%s)" % (url, exc.reason)) from exc
    return json.loads(raw)


# ── Real-time SSE Streaming Round Helper ────────────────────────────────────────

def _stream_round(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    cancel_event: threading.Event | None = None,
    on_thinking: Callable[[str], None] | None = None,
    on_content: Callable[[str], None] | None = None,
    timeout: int = 120,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Stream a chat/completions request from xAI/OpenAI/Gemini with tool calling,
    Gemini thought_signature (extra_content) preservation, and real-time reasoning extraction.
    Returns (accumulated_content, accumulated_tool_calls).
    """
    payload_copy = dict(payload)
    payload_copy["stream"] = True

    req = urllib.request.Request(
        url,
        data=json.dumps(payload_copy).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )

    content_parts: list[str] = []
    tool_calls_map: dict[Any, dict[str, Any]] = {}
    tool_calls_order: list[Any] = []

    def _tool_call_key(tc: dict[str, Any]) -> Any:
        """Accumulate by index when the provider sends one (the normal
        case); fall back to the call's own id when it doesn't (some
        providers omit index for a single, unambiguous call); a NEW id at
        an already-seen index starts a new entry instead of corrupting the
        old one, since index defaulting to a bare 0 used to collapse
        multiple parallel calls with no explicit index into one garbled
        entry. With neither index nor id, a continuation chunk keeps
        appending to whatever call was most recently touched."""
        idx = tc.get("index")
        if idx is not None:
            key = ("idx", idx)
            existing = tool_calls_map.get(key)
            tc_id = tc.get("id")
            if existing is not None and tc_id and existing.get("call_id") and existing["call_id"] != tc_id:
                key = ("id", tc_id)
            return key
        tc_id = tc.get("id")
        if tc_id:
            return ("id", tc_id)
        if tool_calls_order:
            return tool_calls_order[-1]
        return ("idx", 0)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                if cancel_event and cancel_event.is_set():
                    raise RuntimeError("Generation stopped by user.")

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue

                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except Exception:
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}

                # 1. Stream reasoning / thinking tokens live to UI
                reasoning = delta.get("reasoning_content") or delta.get("thought")
                if reasoning and on_thinking:
                    on_thinking(reasoning)

                # 2. Stream content tokens live to UI
                content = delta.get("content")
                if content:
                    content_parts.append(content)
                    if on_content:
                        on_content(content)

                # 3. Accumulate tool call chunks (including Google Gemini thought_signature extra_content)
                for tc in delta.get("tool_calls") or []:
                    key = _tool_call_key(tc)
                    if key not in tool_calls_map:
                        tool_calls_map[key] = {
                            "type": "function_call",
                            "call_id": tc.get("id", ""),
                            "name": tc.get("function", {}).get("name", ""),
                            "arguments": "",
                            "extra_content": tc.get("extra_content") or {},
                        }
                        tool_calls_order.append(key)
                    if tc.get("id"):
                        tool_calls_map[key]["call_id"] = tc["id"]
                    if tc.get("extra_content"):
                        tool_calls_map[key]["extra_content"] = tc["extra_content"]
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        tool_calls_map[key]["name"] = fn["name"]
                    if fn.get("arguments"):
                        tool_calls_map[key]["arguments"] += fn["arguments"]

                # If extra_content came at delta level (Gemini 3.x), ensure first call gets it
                if delta.get("extra_content") and tool_calls_order:
                    first_k = tool_calls_order[0]
                    if not tool_calls_map[first_k].get("extra_content"):
                        tool_calls_map[first_k]["extra_content"] = delta["extra_content"]

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise _api_error(exc.code, detail, url, str(payload.get("model") or "")) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach %s (%s)" % (url, exc.reason)) from exc

    assembled_calls = [tool_calls_map[k] for k in tool_calls_order]
    return "".join(content_parts), assembled_calls


def _stream_round_anthropic(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    cancel_event: threading.Event | None = None,
    on_thinking: Callable[[str], None] | None = None,
    on_content: Callable[[str], None] | None = None,
    timeout: int = 120,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Stream a /v1/messages request from Anthropic Claude with tool_use and thinking extraction.
    Returns (accumulated_content, accumulated_tool_calls).
    """
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )

    content_parts: list[str] = []
    tool_calls_map: dict[int, dict[str, Any]] = {}

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                if cancel_event and cancel_event.is_set():
                    raise RuntimeError("Generation stopped by user.")

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue

                data_str = line[5:].strip()
                if not data_str:
                    continue

                try:
                    event_data = json.loads(data_str)
                except Exception:
                    continue

                evt_type = event_data.get("type") or ""

                if evt_type == "content_block_start":
                    idx = event_data.get("index", 0)
                    cb = event_data.get("content_block") or {}
                    if cb.get("type") == "tool_use":
                        tool_calls_map[idx] = {
                            "type": "function_call",
                            "call_id": cb.get("id") or f"call_{idx}",
                            "name": cb.get("name") or "",
                            "arguments": "",
                        }

                elif evt_type == "content_block_delta":
                    idx = event_data.get("index", 0)
                    delta = event_data.get("delta") or {}
                    d_type = delta.get("type") or ""
                    if d_type == "text_delta":
                        txt = delta.get("text") or ""
                        if txt:
                            content_parts.append(txt)
                            if on_content:
                                on_content(txt)
                    elif d_type == "thinking_delta":
                        thk = delta.get("thinking") or ""
                        if thk and on_thinking:
                            on_thinking(thk)
                    elif d_type == "input_json_delta":
                        part = delta.get("partial_json") or ""
                        if idx in tool_calls_map:
                            tool_calls_map[idx]["arguments"] += part

                elif evt_type == "message_stop":
                    break

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError("Anthropic API %s: %s" % (exc.code, detail[:400])) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach %s (%s)" % (url, exc.reason)) from exc

    assembled_calls = [tool_calls_map[k] for k in sorted(tool_calls_map.keys())]
    return "".join(content_parts), assembled_calls


# ── Main ask function with function-calling loop ───────────────────────────────

def _ask_genius_anthropic(
    settings: dict[str, Any],
    messages: list[dict[str, str]],
    live_line: str,
    bridge: Any = None,
    cancel_event: threading.Event | None = None,
    on_tool_call: Callable[[str, str], None] | None = None,
    on_thinking: Callable[[str], None] | None = None,
    on_content: Callable[[str], None] | None = None,
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """Execute multi-turn tool calling loop against Anthropic Claude /v1/messages."""
    api_key = str(settings.get("api_key") or "").strip()
    base = str(settings.get("api_base") or "https://api.anthropic.com/v1").rstrip("/")
    model = str(settings.get("model") or "claude-sonnet-5-5")

    bridge_online = bool(bridge and getattr(bridge, "last_pong", 0) > 0 and (time.time() - bridge.last_pong) < 15.0)
    e2_online = rs_online(settings)
    tts_ok = tts_available(settings)
    system = build_system_prompt(
        settings, live_line, bridge_online=bridge_online, e2_online=e2_online, tts_online=tts_ok,
        live_ver=live_version.current(),
    )

    active_agent, allowed = agent_registry.resolve_active(settings)
    anthropic_tools = []
    for t in LIVE_TOOLS:
        if allowed is not None and t["name"] not in allowed and t["name"] not in agent_registry.CORE_TOOLS:
            continue
        if t["name"] in E2_TOOLS and not e2_online:
            continue
        if t["name"] in TTS_TOOLS and not tts_ok:
            continue
        anthropic_tools.append({
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("parameters") or {"type": "object", "properties": {}},
        })

    anth_messages: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        if role == "system":
            continue
        anth_messages.append({"role": role, "content": m.get("content", "")})
    if not anth_messages:
        anth_messages.append({"role": "user", "content": "Hello"})

    endpoint = base + "/messages"
    error_counts: dict[tuple[str, str], int] = {}
    force_final = False

    for _loop in range(MAX_TOOL_LOOPS):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Generation stopped by user.")

        if not force_final and _loop == MAX_TOOL_LOOPS - 1:
            # Last round: force a text answer instead of racing to the hard
            # raise below. A long multi-step ask (e.g. "fix the whole mix")
            # can legitimately need many tool calls; this guarantees the turn
            # still ends in a real reply instead of "reached the tool-call limit".
            force_final = True
            anth_messages.append({
                "role": "user",
                "content": (
                    "You're at the tool-call limit for this turn. Do not call any more tools -- "
                    "summarize what you've done so far and finish your answer now."
                ),
            })

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "system": system,
            "messages": anth_messages,
            "stream": True,
        }
        if not force_final:
            payload["tools"] = anthropic_tools

        content, tool_calls = _stream_round_anthropic(
            endpoint,
            api_key,
            payload,
            cancel_event=cancel_event,
            on_thinking=on_thinking,
            on_content=on_content,
        )

        if not tool_calls:
            if not content.strip():
                raise RuntimeError("Empty reply from the model.")
            return content.strip()

        # Build Anthropic assistant message with tool_use blocks
        assistant_content: list[dict[str, Any]] = []
        if content.strip():
            assistant_content.append({"type": "text", "text": content})
        for tc in tool_calls:
            raw_args = tc["arguments"] or "{}"
            try:
                parsed_args = json.loads(raw_args)
            except Exception:
                parsed_args = {}
            assistant_content.append({
                "type": "tool_use",
                "id": tc["call_id"],
                "name": tc["name"],
                "input": parsed_args,
            })
        anth_messages.append({"role": "assistant", "content": assistant_content})

        # Execute tools and build tool_result blocks inside a single user message
        tool_results_content: list[dict[str, Any]] = []
        for tc in tool_calls:
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Generation stopped by user.")

            fn_name = tc["name"]
            call_id = tc["call_id"]
            raw_args = tc["arguments"] or "{}"
            args_invalid = False
            try:
                args = json.loads(raw_args)
            except Exception:
                args = {}
                args_invalid = True

            if on_tool_call:
                friendly = fn_name.replace("live_", "").replace("_", " ")
                on_tool_call(fn_name, f"-> Live Actions: {friendly}...")

            if args_invalid:
                result_text = f"ERROR: {fn_name} received invalid arguments JSON: {raw_args[:200]!r}"
            elif allowed is not None and fn_name not in allowed and fn_name not in agent_registry.CORE_TOOLS:
                # The model can still emit a call for a tool we didn't offer in this
                # turn's schema (some providers don't hard-enforce the function list,
                # and live_control_section's prose describes every tool regardless of
                # which agent is active) -- refuse it here too, not just at the schema.
                persona = active_agent["title"] if active_agent else "the active agent"
                result_text = (
                    f"ERROR: {fn_name} is turned off for {persona}. Switch agents in the chat "
                    "top bar, or enable this tool for this agent in Settings, to use it."
                )
            else:
                try:
                    result_text = call_live_tool(bridge, fn_name, args, settings=settings, confirm=confirm)
                except Exception as exc:
                    result_text = f"ERROR: {fn_name} failed: {exc}"

            if on_tool_call:
                if result_text.startswith("ERROR"):
                    on_tool_call(fn_name, f"[Error] {result_text[:120]}")
                else:
                    friendly = fn_name.replace("live_", "").replace("_", " ")
                    on_tool_call(fn_name, f"[Done] {friendly}")

            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": call_id,
                "content": result_text or "(no output)",
            })

            # Loop guard: see the matching comment in _ask_genius_openai --
            # the same tool failing with the same error twice means a third
            # attempt won't help, so stop offering tools and force a final answer.
            if result_text.startswith("ERROR"):
                err_key = (fn_name, result_text)
                error_counts[err_key] = error_counts.get(err_key, 0) + 1
                if error_counts[err_key] >= 2:
                    force_final = True
                    tool_results_content.append({
                        "type": "text",
                        "text": (
                            f"STOP: {fn_name} has now failed with the same error twice in this turn. "
                            "Do not call it again. Answer using what you already know, and say plainly "
                            "which part you could not complete."
                        ),
                    })

        anth_messages.append({"role": "user", "content": tool_results_content})

    raise RuntimeError("Genius reached the tool-call limit without a final answer. Try rephrasing.")


def _ask_genius_openai(
    settings: dict[str, Any],
    messages: list[dict[str, str]],
    live_line: str,
    bridge: Any = None,
    cancel_event: threading.Event | None = None,
    on_tool_call: Callable[[str, str], None] | None = None,
    on_thinking: Callable[[str], None] | None = None,
    on_content: Callable[[str], None] | None = None,
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """Execute multi-turn tool calling loop against OpenAI/xAI/Gemini /chat/completions."""
    api_key = str(settings.get("api_key") or "").strip()
    base  = str(settings.get("api_base") or "https://api.x.ai/v1").rstrip("/")
    model = str(settings.get("model") or "grok-4.6")

    bridge_online = bool(bridge and getattr(bridge, "last_pong", 0) > 0 and (time.time() - bridge.last_pong) < 15.0)
    e2_online = rs_online(settings)
    tts_ok = tts_available(settings)
    system = build_system_prompt(
        settings, live_line, bridge_online=bridge_online, e2_online=e2_online, tts_online=tts_ok,
        live_ver=live_version.current(),
    )

    active_agent, allowed = agent_registry.resolve_active(settings)
    tools_for_chat = []
    for t in LIVE_TOOLS:
        if allowed is not None and t["name"] not in allowed and t["name"] not in agent_registry.CORE_TOOLS:
            continue
        if t["name"] in E2_TOOLS and not e2_online:
            continue
        if t["name"] in TTS_TOOLS and not tts_ok:
            continue
        tools_for_chat.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {}),
            },
        })

    conv_messages: list[dict[str, Any]] = [{"role": "system", "content": system}] + list(messages)
    endpoint = base + "/chat/completions"
    error_counts: dict[tuple[str, str], int] = {}
    force_final = False

    for _loop in range(MAX_TOOL_LOOPS):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Generation stopped by user.")

        if not force_final and _loop == MAX_TOOL_LOOPS - 1:
            # Last round: force a text answer instead of racing to the hard
            # raise below. A long multi-step ask (e.g. "fix the whole mix")
            # can legitimately need many tool calls; this guarantees the turn
            # still ends in a real reply instead of "reached the tool-call limit".
            force_final = True
            conv_messages.append({
                "role": "user",
                "content": (
                    "You're at the tool-call limit for this turn. Do not call any more tools -- "
                    "summarize what you've done so far and finish your answer now."
                ),
            })

        payload = {
            "model": model,
            "messages": conv_messages,
            "tools": tools_for_chat,
            "tool_choice": "none" if force_final else "auto",
        }

        content, tool_calls = _stream_round(
            endpoint,
            api_key,
            payload,
            cancel_event=cancel_event,
            on_thinking=on_thinking,
            on_content=on_content,
        )

        if not tool_calls:
            if not content.strip():
                raise RuntimeError("Empty reply from the model.")
            return content.strip()

        # Generate each call's id exactly once, here, and store it back on
        # `tc` -- both loops below (building the assistant message and
        # building each tool-result message) then read the SAME id off `tc`
        # instead of separately computing a fallback (a prior mismatch:
        # f"call_{i}" here vs a flat "call_0" below meant two parallel calls
        # missing a real id from the API both got tagged tool_call_id
        # "call_0", leaving the second with no matching assistant call_id --
        # most OpenAI-compatible APIs reject that outright).
        for i, tc in enumerate(tool_calls):
            if not tc.get("call_id"):
                tc["call_id"] = f"call_{i}"

        # Build assistant tool_calls message, preserving Google thought_signature (extra_content)
        assistant_calls = []
        is_gemini = "generativelanguage.googleapis.com" in base or "gemini" in model.lower()
        for tc in tool_calls:
            call_obj: dict[str, Any] = {
                "id": tc["call_id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": tc["arguments"],
                },
            }
            if tc.get("extra_content"):
                call_obj["extra_content"] = tc["extra_content"]
            elif is_gemini:
                # Gemini 3.x mandatory signature fallback per Google API docs
                call_obj["extra_content"] = {
                    "google": {"thought_signature": "context_engineering_is_the_way_to_go"}
                }
            assistant_calls.append(call_obj)

        conv_messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": assistant_calls,
        })

        # Execute each tool call
        for tc in tool_calls:
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Generation stopped by user.")

            fn_name = tc["name"]
            call_id = tc["call_id"]
            raw_args = tc["arguments"] or "{}"
            args_invalid = False
            try:
                args = json.loads(raw_args)
            except Exception:
                args = {}
                args_invalid = True

            if on_tool_call:
                friendly = fn_name.replace("live_", "").replace("_", " ")
                on_tool_call(fn_name, f"-> Live Actions: {friendly}...")

            if args_invalid:
                result_text = f"ERROR: {fn_name} received invalid arguments JSON: {raw_args[:200]!r}"
            elif allowed is not None and fn_name not in allowed and fn_name not in agent_registry.CORE_TOOLS:
                # The model can still emit a call for a tool we didn't offer in this
                # turn's schema (some providers don't hard-enforce the function list,
                # and live_control_section's prose describes every tool regardless of
                # which agent is active) -- refuse it here too, not just at the schema.
                persona = active_agent["title"] if active_agent else "the active agent"
                result_text = (
                    f"ERROR: {fn_name} is turned off for {persona}. Switch agents in the chat "
                    "top bar, or enable this tool for this agent in Settings, to use it."
                )
            else:
                try:
                    result_text = call_live_tool(bridge, fn_name, args, settings=settings, confirm=confirm)
                except Exception as exc:
                    result_text = f"ERROR: {fn_name} failed: {exc}"

            if on_tool_call:
                if result_text.startswith("ERROR"):
                    on_tool_call(fn_name, f"[Error] {result_text[:120]}")
                else:
                    on_tool_call(fn_name, f"[Done] {fn_name.replace('live_', '').replace('_', ' ')}")

            conv_messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": result_text or "(no output)",  # never send an empty tool message -- some providers reject it
            })

            # Loop guard: the same tool returning the exact same error twice
            # means retrying it a third time is not going to help -- stop
            # offering tools and force a final answer from what's known so far,
            # instead of grinding through MAX_TOOL_LOOPS on a stuck call.
            if result_text.startswith("ERROR"):
                err_key = (fn_name, result_text)
                error_counts[err_key] = error_counts.get(err_key, 0) + 1
                if error_counts[err_key] >= 2:
                    force_final = True
                    conv_messages.append({
                        "role": "user",
                        "content": (
                            f"STOP: {fn_name} has now failed with the same error twice in this turn. "
                            "Do not call it again. Answer using what you already know, and say plainly "
                            "which part you could not complete."
                        ),
                    })

    raise RuntimeError("Genius reached the tool-call limit without a final answer. Try rephrasing.")


def ask_genius(
    settings: dict[str, Any],
    messages: list[dict[str, str]],
    live_line: str,
    bridge: Any = None,
    cancel_event: threading.Event | None = None,
    on_tool_call: Callable[[str, str], None] | None = None,
    on_thinking: Callable[[str], None] | None = None,
    on_content: Callable[[str], None] | None = None,
    confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> str:
    """
    Send a chat request with native live_* Live-control tools available.
    Supports OpenAI-compatible providers (xAI, OpenAI, Gemini) and Anthropic Claude natively.
    Streams reasoning/thinking tokens live to the UI so the user sees progress in real-time.
    Runs a function-calling loop: model calls tools → we execute them via bridge → model continues.
    """
    if cancel_event and cancel_event.is_set():
        raise RuntimeError("Generation stopped by user.")

    api_key = str(settings.get("api_key") or "").strip()
    if not api_key:
        raise RuntimeError("No API key. Open Settings and paste your API key.")

    base = str(settings.get("api_base") or "https://api.x.ai/v1").rstrip("/")
    provider = str(settings.get("provider") or "").lower()

    is_anthropic = (
        provider == "anthropic"
        or "anthropic.com" in base
        or api_key.startswith("sk-ant-")
    )

    if is_anthropic:
        return _ask_genius_anthropic(
            settings,
            messages,
            live_line,
            bridge=bridge,
            cancel_event=cancel_event,
            on_tool_call=on_tool_call,
            on_thinking=on_thinking,
            on_content=on_content,
            confirm=confirm,
        )

    return _ask_genius_openai(
        settings,
        messages,
        live_line,
        bridge=bridge,
        cancel_event=cancel_event,
        on_tool_call=on_tool_call,
        on_thinking=on_thinking,
        on_content=on_content,
        confirm=confirm,
    )


def test_key(settings: dict[str, Any]) -> str:
    api_key = str(settings.get("api_key") or "").strip()
    if not api_key:
        raise RuntimeError("Paste an API key first.")
    base = str(settings.get("api_base") or "https://api.x.ai/v1").rstrip("/")
    model = str(settings.get("model") or "")
    provider = str(settings.get("provider") or "").lower()

    is_anthropic = (
        provider == "anthropic"
        or "anthropic.com" in base
        or api_key.startswith("sk-ant-")
    )

    if is_anthropic:
        url = base + "/messages"
        body = json.dumps({
            "model": model or "claude-haiku-4-5-20251001",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError("API %s: %s" % (exc.code, detail[:400])) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Could not reach %s (%s)" % (url, exc.reason)) from exc
        data = json.loads(raw)
        for block in data.get("content") or []:
            if block.get("type") == "text":
                return block.get("text", "").strip() or "Key accepted."
        return "Key accepted."

    # OpenAI-compatible /chat/completions:
    data = _post_json(
        base + "/chat/completions",
        api_key,
        {"model": model or "grok-4.6", "messages": [{"role": "user", "content": "Reply with the single word: ok"}]},
        timeout=60,
    )
    text = extract_output_text(data)
    return text or "Key accepted."
