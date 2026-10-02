"""Live Actions settings. API key lives in AppData, not in the project folder."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# LIVE_ACTIONS_INSTANCE lets a second copy of the app (e.g. a git worktree) run
# beside the main one. Unset -- the normal case -- every value below is exactly
# what it always was. Only [A-Za-z0-9_-] survives, so the name is safe to embed
# in a folder name and a Win32 mutex/event name.
INSTANCE = "".join(
    ch for ch in os.environ.get("LIVE_ACTIONS_INSTANCE", "").strip() if ch.isalnum() or ch in "_-"
)
INSTANCE_PORT_OFFSET = 100 if INSTANCE else 0


def instance_suffix() -> str:
    """'' for the main instance, '-<name>' for a named one."""
    return f"-{INSTANCE}" if INSTANCE else ""


APP_DATA = Path(os.environ.get("APPDATA", str(Path.home()))) / f"Live Actions{instance_suffix()}"
SETTINGS_PATH = APP_DATA / "settings.json"

DEFAULTS: dict[str, Any] = {
    "api_key": "",
    "api_base": "https://api.x.ai/v1",
    "model": "grok-4.6",
    # "api_key"/"api_base"/"model" above stay the resolved *active* values --
    # genius_client.py only ever reads those three flat fields, unchanged. The
    # multi-key UI in Settings keeps them in sync with whichever api_keys entry
    # is active_api_key_id, so no other module needs to know api_keys exists.
    "api_keys": [],
    "active_api_key_id": "",
    "tools_dir": str(ROOT / "tools"),
    # Your own notes and manuals (.md / .txt / .pdf) for Genius to read. Ships empty.
    "knowledge_dir": str(ROOT / "knowledge"),
    # The bundled knowledge database (see database/README.md). Point it elsewhere to use your own.
    "music_db_dir": str(ROOT / "database"),
    "samples_dir": str(Path.home() / "Documents" / "Live Actions" / "Samples"),
    "plugin_docs_dir": "",     # optional folder of plugin manuals; "" = not used
    "listen_port": 11925 + INSTANCE_PORT_OFFSET,
    "bridge_port": 11924 + INSTANCE_PORT_OFFSET,
    # Engine E2 (LiveActionsRS Remote Script). Live's browser panel is only
    # reachable from a Remote Script -- never from the M4L bridge -- so the
    # browser tools talk to this port instead of bridge_port. Deliberately not
    # 9877, so a user also running the third-party AbletonMCP script keeps both.
    "rs_port": 11926 + INSTANCE_PORT_OFFSET,
    "tts_profiles": [],
    # Name of the one TTS profile every generation must use, or "" for the old
    # behaviour (Genius/the Tool screen may pick/name any saved profile). See
    # tts_vocal._pick_profile / genius_client._resolve_tts_profile.
    "active_tts_profile": "",
    "tts_output_dir": "",
    "audio_sample_output_dir": "",
    "ffmpeg_path": "",
    "tool_prefs": {},
    "enabled_agents": [],      # list[str] of slugs; order drives the chat switcher
    "active_agent": "",        # slug currently driving Genius; "" = stock Genius
    "agent_tool_prefs": {},    # {slug: {tool_name: bool}} -- full resolved map per agent
    # Genius custom instructions (see app/custom_instructions.py). The preset
    # library is global so house rules are reusable; ci_bindings records which
    # preset each Live Set last used, keyed by a slug of the Set name.
    "custom_instructions": [],  # [{id, name, body, created, updated}]
    "ci_bindings": {},          # {live_set_slug: preset_id}
    "theme": "risograph-art-studio",   # WebView2 shell only: slug of web/css/themes/<slug>.css
}


def default_settings() -> dict[str, Any]:
    return dict(DEFAULTS)


def load_settings() -> dict[str, Any]:
    data = default_settings()
    env_key = os.environ.get("XAI_API_KEY", "").strip()
    if env_key:
        data["api_key"] = env_key
    if SETTINGS_PATH.is_file():
        try:
            saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved = {}
        if isinstance(saved, dict):
            for key, value in saved.items():
                if key in DEFAULTS:
                    data[key] = value
            if not saved.get("knowledge_dir") and saved.get("library_index"):
                old = Path(str(saved["library_index"]))
                data["knowledge_dir"] = str(old.parent if old.suffix.lower() == ".md" else old)
    # Migration: a settings.json saved before the multi-key vault existed has a
    # flat api_key but an empty api_keys list -- surface that key as a saved
    # entry instead of letting it silently vanish behind the new Saved Keys UI.
    if not data.get("api_keys") and str(data.get("api_key") or "").strip():
        entry = {
            "id": "imported-legacy",
            "label": "Imported key",
            "provider": "",
            "api_key": str(data.get("api_key") or ""),
            "api_base": str(data.get("api_base") or DEFAULTS["api_base"]),
            "model": str(data.get("model") or DEFAULTS["model"]),
        }
        data["api_keys"] = [entry]
        data["active_api_key_id"] = "imported-legacy"
    return data


def save_settings(data: dict[str, Any]) -> Path:
    APP_DATA.mkdir(parents=True, exist_ok=True)
    out = default_settings()
    for key in DEFAULTS:
        if key in data:
            out[key] = data[key]
    payload = json.dumps(out, indent=2)
    tmp = SETTINGS_PATH.with_name(SETTINGS_PATH.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    # Windows refuses the rename while anything else (an antivirus or backup scan, an indexer) has settings.json
    # open. Those holds last milliseconds, so wait them out instead of losing the user's edit.
    for attempt in range(10):
        try:
            os.replace(tmp, SETTINGS_PATH)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.03)
    return SETTINGS_PATH


def tools_dir(settings: dict[str, Any] | None = None) -> Path:
    cfg = settings if settings is not None else load_settings()
    path = Path(str(cfg.get("tools_dir") or DEFAULTS["tools_dir"]))
    return path


def knowledge_dir(settings: dict[str, Any] | None = None) -> Path:
    cfg = settings if settings is not None else load_settings()
    return Path(str(cfg.get("knowledge_dir") or DEFAULTS["knowledge_dir"]))


def knowledge_index_path(settings: dict[str, Any] | None = None) -> Path:
    return knowledge_dir(settings) / "INDEX.md"


def samples_dir(settings: dict[str, Any] | None = None) -> Path:
    cfg = settings if settings is not None else load_settings()
    return Path(str(cfg.get("samples_dir") or DEFAULTS["samples_dir"]))


def music_db_dir(settings: dict[str, Any] | None = None) -> Path:
    cfg = settings if settings is not None else load_settings()
    return Path(str(cfg.get("music_db_dir") or DEFAULTS["music_db_dir"]))
