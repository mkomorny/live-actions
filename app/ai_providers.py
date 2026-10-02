"""Chat-capable AI provider detection and model listing for Genius's Settings tab.

Separate from tts_vocal.py's own detect_provider()/list_voices(): that module is
TTS-scoped (voice endpoints, includes ElevenLabs, which has no chat API at all).
This module only covers providers genius_client.py's request pipeline can actually
talk to -- everything here is called via {api_base}/chat/completions, so a provider
only belongs in PROVIDER_DEFAULTS if its api_base is the OpenAI-Chat-Completions-
compatible one, not a provider's native/proprietary REST shape. Google's Gemini API
has both; the OpenAI-compatible one (`/v1beta/openai`) is what belongs here, not the
native `/v1beta/models/{model}:generateContent` shape.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_TIMEOUT = 6  # seconds -- detection/listing must fail fast, not hang the Settings tab

# provider key -> default OpenAI-Chat-Completions-compatible api_base.
PROVIDER_DEFAULTS: dict[str, str] = {
    "xai": "https://api.x.ai/v1",
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "anthropic": "https://api.anthropic.com/v1",
}

# Model IDs containing any of these are not chat models (embeddings, TTS, image,
# moderation, legacy completion-only, or WebSocket-only realtime/live models) --
# filtered out of the dropdown so it only shows models actually usable for Genius.
_NON_CHAT_MARKERS = (
    "embed", "whisper", "tts", "dall-e", "image", "moderation",
    "davinci-002", "babbage-002", "text-similarity", "audio",
    "-live", "-realtime", "realtime",
    "transcribe", "robotics", "computer-use",
    # Gemini families with no text-chat surface (music, video, image-only, speech, agents).
    "lyria", "veo", "imagen", "nano-banana", "native-audio", "deep-research", "antigravity", "omni", "aqa",
)

GEMINI_NATIVE_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _probe(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    """A short-timeout GET. Never raises -- failures come back as status 0."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError):
        return 0, b""


def _headers_for(provider: str, key: str) -> dict[str, str]:
    if provider == "anthropic":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    return {"Authorization": "Bearer " + key}


def detect_provider(api_key: str) -> tuple[str, str, str]:
    """Identify which provider a chat API key belongs to.

    Returns (provider, api_base, message). provider is "" when nothing matched, so
    the caller can report honestly and leave prior fields untouched. The key prefix
    only orders the guesses -- the real decision comes from a live authenticated
    probe against each candidate's /models endpoint.
    """
    key = api_key.strip()
    if not key:
        return "", "", "No API key entered."

    if key.startswith("sk-ant-"):
        order = ["anthropic", "openai", "xai", "gemini"]
    elif key.startswith("AIza") or key.startswith("AQ."):
        order = ["gemini", "xai", "openai", "anthropic"]
    elif key.startswith("xai-"):
        order = ["xai", "anthropic", "openai", "gemini"]
    elif key.startswith("sk-"):
        order = ["openai", "anthropic", "xai", "gemini"]
    else:
        order = ["xai", "gemini", "openai", "anthropic"]

    for provider in order:
        base = PROVIDER_DEFAULTS[provider]
        try:
            status, _ = _probe(base + "/models", _headers_for(provider, key))
        except Exception:
            status = 0
        if status == 200:
            return provider, base, "Detected %s." % provider
    return "", "", "No provider recognized this key (checked xAI, Gemini, OpenAI, Anthropic)."


def _is_chat_id(model_id: str) -> bool:
    return not any(marker in model_id.lower() for marker in _NON_CHAT_MARKERS)


def list_gemini_chat(api_key: str) -> list[str] | None:
    """Gemini chat models from Google's NATIVE models.list, which (unlike the OpenAI-compatible
    /models) says what each model supports. A model stays only if it takes generateContent and is
    not a known non-chat family: Live (bidiGenerateContent), Imagen/Veo (predict,
    predictLongRunning), embeddings (embedContent), Lyria, TTS, image. None when the call fails,
    so the caller can fall back to the OpenAI-compatible list."""
    key = api_key.strip()
    ids: list[str] = []
    token = ""
    for _ in range(20):  # page guard; one page of 1000 covers every key today
        url = GEMINI_NATIVE_BASE + "/models?pageSize=1000" + ("&pageToken=" + urllib.parse.quote(token) if token else "")
        status, body = _probe(url, {"x-goog-api-key": key})
        if status != 200:
            return None
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        for entry in data.get("models") or []:
            entry = entry or {}
            model_id = str(entry.get("name") or "").strip()
            if model_id.startswith("models/"):
                model_id = model_id[len("models/"):]
            methods = entry.get("supportedGenerationMethods") or []
            if model_id and "generateContent" in methods and _is_chat_id(model_id):
                ids.append(model_id)
        token = str(data.get("nextPageToken") or "")
        if not token:
            break
    return sorted(set(ids))


# A probe tool: Genius cannot work without function calling, so a model that refuses tools fails.
_PROBE_TOOL = {
    "type": "function",
    "function": {
        "name": "ping",
        "description": "Connectivity check. Never needs to be called.",
        "parameters": {"type": "object", "properties": {}},
    },
}
_PROBE_TIMEOUT = 15


def probe_chat_model(provider: str, api_key: str, api_base: str, model: str) -> str:
    """One tiny tool-enabled chat request. Returns "ok" (answered), "busy" (429/503/timeout: the
    model works, the provider or quota is the problem right now) or "broken" (anything else: no
    access, not a chat model, no tool calling, shut down)."""
    key = api_key.strip()
    p_norm = provider.strip().lower()
    base = (api_base or PROVIDER_DEFAULTS.get(p_norm, "")).rstrip("/")
    if not key or not base or not model:
        return "broken"
    if p_norm == "anthropic" or "anthropic.com" in base:
        url = base + "/messages"
        body = {"model": model, "max_tokens": 16, "messages": [{"role": "user", "content": "Reply: ok"}],
                "tools": [{"name": "ping", "description": "Connectivity check.", "input_schema": {"type": "object", "properties": {}}}]}
        headers = dict(_headers_for("anthropic", key))
    else:
        url = base + "/chat/completions"
        body = {"model": model, "max_tokens": 16, "messages": [{"role": "user", "content": "Reply: ok"}], "tools": [_PROBE_TOOL]}
        headers = dict(_headers_for("openai", key))
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_PROBE_TIMEOUT) as resp:
            return "ok" if resp.status == 200 else "broken"
    except urllib.error.HTTPError as exc:
        return "busy" if exc.code in (429, 503) else "broken"
    except (TimeoutError, OSError):  # URLError and socket timeouts are OSErrors
        return "busy"


def list_models(provider: str, api_key: str, api_base: str = "") -> list[str]:
    """Return sorted chat-capable model ids for a provider, via GET {api_base}/models."""
    key = api_key.strip()
    p_norm = provider.strip().lower()
    base = (api_base or PROVIDER_DEFAULTS.get(p_norm, "")).rstrip("/")
    if not key or not base:
        return []
    if p_norm == "gemini" or "generativelanguage.googleapis.com" in base:
        native = list_gemini_chat(key)
        if native is not None:
            return native

    is_anthropic = p_norm == "anthropic" or "anthropic.com" in base
    headers = _headers_for("anthropic" if is_anthropic else "openai", key)
    status, body = _probe(base + "/models", headers)

    if status != 200:
        if is_anthropic:
            # Anthropic fallback catalog if /models endpoint is restricted
            return ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-4-5-20251001"]
        return []

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []

    ids: list[str] = []
    for entry in data.get("data") or []:
        model_id = str((entry or {}).get("id") or "").strip()
        if not model_id:
            continue
        # Strip Google's "models/" prefix for clean OpenAI-compatible IDs
        if model_id.startswith("models/"):
            model_id = model_id[len("models/"):]
        if not _is_chat_id(model_id):
            continue
        ids.append(model_id)

    # If anthropic returned empty list from /models, provide standard defaults
    if is_anthropic and not ids:
        return ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-4-5-20251001"]

    return sorted(set(ids))
