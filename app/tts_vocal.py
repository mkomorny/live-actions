"""AI TTS vocal generation: profile -> HTTPS -> ffmpeg -> WAV.

No Max/Live involvement — this runs entirely on the Python host. Keys, provider
choice, and raw audio bytes never cross the OSC bridge into Max.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

MAX_TEXT_CHARS = 2000

_LOCKS_GUARD = threading.Lock()
_INFLIGHT: dict[str, threading.Lock] = {}

_FRIENDLY_LOCK = threading.Lock()
_FRIENDLY_RE = re.compile(r"^TTS-Sample-(\d+)\.wav$", re.IGNORECASE)


class TtsError(RuntimeError):
    """A generation failure with a message safe to show in the Log pane / footer."""


def _cache_key(provider: str, voice_id: str, text: str, gen_settings: dict[str, Any]) -> str:
    payload = json.dumps(
        {"provider": provider, "voice": voice_id, "text": text, "settings": gen_settings},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _inflight_lock(cache_key: str) -> threading.Lock:
    with _LOCKS_GUARD:
        lock = _INFLIGHT.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _INFLIGHT[cache_key] = lock
        return lock


def _resolve_ffmpeg(settings: dict[str, Any]) -> str:
    configured = str(settings.get("ffmpeg_path") or "").strip()
    if configured:
        return configured
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise TtsError("ffmpeg not found. Set ffmpeg_path in Settings.")


def _openai_speech(profile: dict[str, Any], text: str) -> bytes:
    api_key = str(profile.get("api_key") or "").strip()
    if not api_key:
        raise TtsError('Profile "%s" has no API key.' % profile.get("name", "?"))
    model = str(profile.get("model") or "tts-1")
    voice = str(profile.get("voice_id") or "alloy")
    gen_settings = profile.get("settings") or {}
    body: dict[str, Any] = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "wav",
    }
    if gen_settings.get("speed"):
        body["speed"] = gen_settings["speed"]
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise TtsError("OpenAI TTS %s: %s" % (exc.code, detail[:400])) from exc
    except urllib.error.URLError as exc:
        raise TtsError("Could not reach OpenAI (%s)" % (exc.reason,)) from exc


def _xai_speech(profile: dict[str, Any], text: str) -> bytes:
    api_key = str(profile.get("api_key") or "").strip()
    if not api_key:
        raise TtsError('Profile "%s" has no API key.' % profile.get("name", "?"))
    voice = str(profile.get("voice_id") or "eve")
    gen_settings = profile.get("settings") or {}
    body: dict[str, Any] = {
        "text": text,
        "voice_id": voice,
        "language": str(gen_settings.get("language") or "auto"),
        "output_format": {"codec": "wav", "sample_rate": 48000},
    }
    if gen_settings.get("speed"):
        body["speed"] = gen_settings["speed"]
    req = urllib.request.Request(
        "https://api.x.ai/v1/tts",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise TtsError("xAI TTS %s: %s" % (exc.code, detail[:400])) from exc
    except urllib.error.URLError as exc:
        raise TtsError("Could not reach xAI (%s)" % (exc.reason,)) from exc

    if content_type.startswith("audio/"):
        return raw
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw
    audio_b64 = payload.get("audio")
    if not audio_b64:
        raise TtsError("xAI TTS response had no audio field.")
    return base64.b64decode(audio_b64)


def _cartesia_speech(profile: dict[str, Any], text: str) -> bytes:
    api_key = str(profile.get("api_key") or "").strip()
    if not api_key:
        raise TtsError('Profile "%s" has no API key.' % profile.get("name", "?"))
    voice = str(profile.get("voice_id") or "").strip()
    if not voice:
        raise TtsError(
            'Profile "%s" has no Cartesia voice ID. Use "↻ Refresh voices" or paste one from the Cartesia dashboard.'
            % profile.get("name", "?")
        )
    model = str(profile.get("model") or _CARTESIA_DEFAULT_MODEL)
    gen_settings = profile.get("settings") or {}

    body: dict[str, Any] = {
        "model_id": model,
        "transcript": text,
        "voice": voice,
        "output_format": {
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 48000,
        },
    }

    # Cartesia has no "auto" language — filter out the literal xAI default that
    # would otherwise flow through unchanged from a profile repointed off xAI.
    language = str(gen_settings.get("language") or "").strip()
    if language and language.lower() != "auto":
        body["language"] = language

    # Range-checked locally (not clamped) so an out-of-range value fails fast and
    # never produces a cache key that differs from an in-range one that would
    # generate byte-identical audio — see the note in the plan doc for why.
    speed = gen_settings.get("speed")
    if speed:
        try:
            value = float(speed)
        except (TypeError, ValueError):
            raise TtsError('Speed "%s" is not a number.' % (speed,)) from None
        low, high = _CARTESIA_SPEED_RANGE
        if not (low <= value <= high):
            raise TtsError(
                "Cartesia speed must be between %s and %s; got %s." % (low, high, value)
            )
        body["generation_config"] = {"speed": value}

    req = urllib.request.Request(
        "https://api.cartesia.ai/tts/bytes",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Cartesia-Version": _CARTESIA_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise TtsError("Cartesia TTS %s: %s" % (exc.code, detail[:400])) from exc
    except urllib.error.URLError as exc:
        raise TtsError("Could not reach Cartesia (%s)" % (exc.reason,)) from exc


_PROVIDERS: dict[str, Callable[[dict[str, Any], str], bytes]] = {
    "openai": _openai_speech,
    "xai": _xai_speech,
    "cartesia": _cartesia_speech,
}

_DETECT_TIMEOUT = 5  # seconds — probes must fail fast, not hang the Settings tab

# OpenAI has no voices-listing endpoint; this is its documented static voice set.
_OPENAI_VOICES = ("alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse")

# Cartesia requires an API-version date on every request and rotates it periodically.
# Verified current 2026-09-19; bump here if the API starts 400ing on an unsupported version.
_CARTESIA_VERSION = "2026-08-14"
_CARTESIA_DEFAULT_MODEL = "sonic-3.6"
_CARTESIA_SPEED_RANGE = (0.6, 1.5)  # generation_config.speed; narrower than OpenAI's 0.25-4.0


def _probe(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    """A short-timeout GET used for provider detection and voice listing.

    Never raises — network failures and HTTP errors both come back as a status code
    (0 for unreachable) so callers can treat "wrong provider" and "offline" the same way.
    """
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_DETECT_TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError):
        return 0, b""


_PROVIDER_PROBES: dict[str, Callable[[str], tuple[int, bytes]]] = {
    "xai": lambda key: _probe("https://api.x.ai/v1/tts/voices", {"Authorization": "Bearer " + key}),
    "openai": lambda key: _probe("https://api.openai.com/v1/models", {"Authorization": "Bearer " + key}),
    "elevenlabs": lambda key: _probe("https://api.elevenlabs.io/v1/voices", {"xi-api-key": key}),
    "cartesia": lambda key: _probe(
        "https://api.cartesia.ai/voices?limit=1",
        {"Authorization": "Bearer " + key, "Cartesia-Version": _CARTESIA_VERSION},
    ),
}


def detect_provider(api_key: str) -> tuple[str, str]:
    """Identify which provider an API key belongs to, and return (provider, message).

    The key's prefix only orders the guesses — OpenAI's "sk-" and ElevenLabs' "sk_" differ
    by one character, so the actual decision comes from a live authenticated probe against
    each candidate, not the prefix alone. Returns ("", reason) when nothing matches, so the
    caller can report honestly and leave the provider dropdown on its current value.
    """
    key = api_key.strip()
    if not key:
        return "", "No API key entered."

    if key.startswith("xai-"):
        order = ["xai", "openai", "cartesia", "elevenlabs"]
    elif key.startswith("sk_car"):  # must precede the "sk_" branch below — sk_car_... also matches it
        order = ["cartesia", "elevenlabs", "openai", "xai"]
    elif key.startswith("sk_"):
        order = ["elevenlabs", "cartesia", "openai", "xai"]
    elif key.startswith("sk-"):
        order = ["openai", "xai", "cartesia", "elevenlabs"]
    else:
        order = ["xai", "openai", "cartesia", "elevenlabs"]

    for provider in order:
        try:
            status, _ = _PROVIDER_PROBES[provider](key)
        except Exception:
            status = 0
        if status == 200:
            if provider == "elevenlabs":
                return provider, "Detected ElevenLabs — this build has no generation handler for it yet; provider set for reference only."
            return provider, "Detected %s." % provider
    return "", "No provider recognized this key (checked xAI, OpenAI, Cartesia, ElevenLabs)."


def list_voices(provider: str, api_key: str) -> list[dict[str, Any]]:
    """Return [{"voice_id", "name", "custom": bool}, ...] for the given provider.

    xAI custom (cloned) voices are returned only by GET /v1/custom-voices — they never
    appear in the built-in GET /v1/tts/voices list, so both are called and merged. Missing
    that would silently drop every cloned voice from the picker. Cartesia instead has one
    endpoint for both, filtered by an is_owner query param — it's called twice anyway (once
    filtered, once not) because the unfiltered call also re-returns the owned voices, so a
    dedupe pass is needed there instead of a second, genuinely disjoint endpoint.
    """
    key = api_key.strip()
    provider = provider.strip().lower()
    if not key or not provider:
        return []

    if provider == "cartesia":
        voices: list[dict[str, Any]] = []
        seen: set[str] = set()
        headers = {"Authorization": "Bearer " + key, "Cartesia-Version": _CARTESIA_VERSION}
        for url, is_custom in (
            ("https://api.cartesia.ai/voices?limit=100&is_owner=true", True),
            ("https://api.cartesia.ai/voices?limit=100", False),
        ):
            status, body = _probe(url, headers)
            if status != 200:
                continue
            try:
                data = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for entry in data.get("data") or []:
                vid = entry.get("id")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                voices.append({
                    "voice_id": vid,
                    "name": entry.get("name") or vid,
                    "custom": is_custom,
                })
        return voices

    if provider == "xai":
        voices: list[dict[str, Any]] = []
        for url, is_custom in (
            ("https://api.x.ai/v1/tts/voices", False),
            ("https://api.x.ai/v1/custom-voices", True),
        ):
            status, body = _probe(url, {"Authorization": "Bearer " + key})
            if status != 200:
                continue
            try:
                data = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for entry in data.get("voices") or []:
                voices.append({
                    "voice_id": entry.get("voice_id"),
                    "name": entry.get("name") or entry.get("voice_id"),
                    "custom": is_custom,
                })
        return voices

    if provider == "openai":
        return [{"voice_id": v, "name": v, "custom": False} for v in _OPENAI_VOICES]

    return []


def _probe_duration(ffmpeg_path: str, wav_path: Path) -> float | None:
    candidate = Path(ffmpeg_path)
    ffprobe = candidate.with_name(candidate.name.replace("ffmpeg", "ffprobe"))
    ffprobe_path = str(ffprobe) if ffprobe.is_file() else (shutil.which("ffprobe") or "")
    if not ffprobe_path:
        return None
    try:
        result = subprocess.run(
            [
                ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path),
            ],
            capture_output=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        return round(float(result.stdout.decode("utf-8", "replace").strip()), 3)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def _normalize_to_wav(raw_audio: bytes, ffmpeg_path: str, out_path: Path) -> None:
    tmp_in = out_path.with_suffix(out_path.suffix + ".src")
    tmp_out = out_path.with_name(out_path.name + ".tmp")
    tmp_in.write_bytes(raw_audio)
    try:
        result = subprocess.run(
            [
                ffmpeg_path, "-y", "-i", str(tmp_in),
                "-ar", "48000", "-ac", "1", "-acodec", "pcm_s24le",
                "-f", "wav", str(tmp_out),
            ],
            capture_output=True, timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", "replace")
            raise TtsError("ffmpeg failed: %s" % stderr[-400:])
        os.replace(tmp_out, out_path)
    finally:
        tmp_in.unlink(missing_ok=True)
        if tmp_out.exists():
            tmp_out.unlink(missing_ok=True)


def _pick_profile(fields: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any] | None:
    """Pick which saved profile a generation uses.

    A pinned profile (Settings -> TTS Vocal Profiles, the checkbox on a profile card)
    overrides any `profile` name the caller asked for -- that is the whole point of
    pinning: no caller, model or Tool-screen field, gets to pick a different voice
    while one is pinned.
    """
    profiles = settings.get("tts_profiles") or []
    if not profiles:
        return None
    pinned = str(settings.get("active_tts_profile") or "").strip()
    if pinned:
        for candidate in profiles:
            if candidate.get("name") == pinned:
                return candidate
        # Stale pin (the profile was renamed/removed outside save_tts's own
        # rename/delete bookkeeping somehow) -- refuse rather than silently
        # generating with a different, un-pinned voice.
        return None
    wanted = str(fields.get("profile") or "").strip()
    if wanted:
        for candidate in profiles:
            if candidate.get("name") == wanted:
                return candidate
    return profiles[0]


def _apply_overrides(
    profile: dict[str, Any], fields: dict[str, Any], voice_locked: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Layer per-generation Tool-screen overrides (voice/speed/language) onto a profile.

    Returns (effective_profile, gen_settings) — gen_settings is also what goes into the
    cache key, so an override always produces a distinct cache entry from the bare profile.

    `voice_locked` (a pinned profile) drops the `voice` override: pinning is meant to
    guarantee one exact voice, so it would defeat the point to still let a per-run
    `voice` field substitute a different one. Speed/language aren't "the voice" and
    stay overridable.
    """
    effective = dict(profile)
    gen_settings = dict(profile.get("settings") or {})

    voice_override = "" if voice_locked else str(fields.get("voice") or "").strip()
    if voice_override:
        effective["voice_id"] = voice_override

    speed_raw = str(fields.get("speed") or "").strip()
    if speed_raw:
        try:
            gen_settings["speed"] = float(speed_raw)
        except ValueError:
            raise TtsError('Speed "%s" is not a number.' % speed_raw)

    language_override = str(fields.get("language") or "").strip()
    if language_override:
        gen_settings["language"] = language_override

    effective["settings"] = gen_settings
    return effective, gen_settings


def _next_friendly_copy(out_dir: Path, cache_path: Path) -> Path:
    """Copy the (internally cache-keyed) generated WAV to a short, human-friendly filename.

    The hash-named file under out_dir/.cache is what makes caching possible; this copy is
    purely so the user sees "TTS-Sample-3.wav" in their sample browser, not a sha256 blob.
    Every Run produces a new numbered copy, even on a cache hit, since each click is a
    distinct sample from the user's point of view.
    """
    with _FRIENDLY_LOCK:
        highest = 0
        for existing in out_dir.glob("TTS-Sample-*.wav"):
            match = _FRIENDLY_RE.match(existing.name)
            if match:
                highest = max(highest, int(match.group(1)))
        friendly_path = out_dir / ("TTS-Sample-%d.wav" % (highest + 1))
        shutil.copyfile(cache_path, friendly_path)
        return friendly_path


def run(fields: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Generate (or return a cached) TTS WAV. Never raises — always returns a status dict."""
    text = str(fields.get("text") or "").strip()
    if not text:
        return {"ok": False, "message": "No text to generate."}
    if len(text) > MAX_TEXT_CHARS:
        return {"ok": False, "message": "Text is %d characters; limit is %d." % (len(text), MAX_TEXT_CHARS)}

    profile = _pick_profile(fields, settings)
    if profile is None:
        return {"ok": False, "message": "No TTS profiles configured. Add one in Settings."}

    provider = str(profile.get("provider") or "").strip().lower()
    handler = _PROVIDERS.get(provider)
    if handler is None:
        return {"ok": False, "message": 'Unknown provider "%s".' % (provider or "(none)")}

    try:
        voice_locked = bool(str(settings.get("active_tts_profile") or "").strip())
        effective_profile, gen_settings = _apply_overrides(profile, fields, voice_locked=voice_locked)
    except TtsError as exc:
        return {"ok": False, "message": str(exc)}

    voice_id = str(effective_profile.get("voice_id") or "")
    key = _cache_key(provider, voice_id, text, gen_settings)

    output_dir = str(settings.get("tts_output_dir") or "").strip()
    if output_dir:
        out_dir = Path(output_dir)
    else:
        import settings_store
        out_dir = settings_store.samples_dir(settings) / "TTS"

    cache_dir = out_dir / ".cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {"ok": False, "message": "Could not create output folder: %s" % exc}

    cache_path = cache_dir / ("%s.wav" % key)

    lock = _inflight_lock(key)
    with lock:
        cache_hit = cache_path.is_file()
        try:
            ffmpeg_path = _resolve_ffmpeg(settings)
            if not cache_hit:
                raw_audio = handler(effective_profile, text)
                _normalize_to_wav(raw_audio, ffmpeg_path, cache_path)
            duration = _probe_duration(ffmpeg_path, cache_path)
            friendly_path = _next_friendly_copy(out_dir, cache_path)
        except TtsError as exc:
            return {"ok": False, "message": str(exc)}
        except OSError as exc:
            return {"ok": False, "message": "Could not write output file: %s" % exc}

        return {
            "ok": True,
            "message": "Using cached generation." if cache_hit else "Generated.",
            "path": str(friendly_path),
            "durationSec": duration,
            "cacheHit": cache_hit,
            "provider": provider,
            "voice": voice_id,
        }
