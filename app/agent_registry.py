"""Selectable Genius personas ("agents"): system-prompt override + per-tool filtering.

An agent is a small Markdown file with YAML-ish frontmatter (name, title,
description, tools_default) and a body that replaces the stock Genius persona
paragraph when that agent is active. See app/genius/personas/*.md for shipped
examples and docs/plans/v1.0.42-genius-agents.md for the design.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Structural tools every agent needs regardless of its toolset -- never shown
# in the per-agent toggle UI, always sent to the model.
CORE_TOOLS = frozenset({"live_connect", "live_read_set", "live_context"})

# Curated display grouping for the other ~119 live_*/library_*/als_* tools.
# LIVE_TOOLS entries in genius_client.py are flat {"name","description",
# "parameters"} dicts with no category field, so this grouping lives here
# instead. Anything not listed falls into "Other" (see ALL_TOOL_NAMES / the
# test that guards against group rot as tools are added).
TOOL_GROUPS: dict[str, tuple[str, ...]] = {
    "Transport & playback": (
        "live_update_set", "live_playback", "live_stop_all_clips", "live_tap_tempo",
        "live_continue_playing", "live_scrub", "live_jump_cue", "live_set_punch",
        "live_set_cue_volume", "live_jump_to_time", "live_set_overdub", "live_read_link_status",
    ),
    "Undo & session state": (
        "live_undo", "live_redo", "live_session_snapshot", "live_session_diff",
    ),
    "Tracks & mixer": (
        "live_read_track", "live_update_track", "live_create_track", "live_set_crossfader",
        "live_batch_tracks", "live_set_fold_state", "live_edit_track",
    ),
    "Scenes": (
        "live_read_scene", "live_update_scene", "live_create_scene", "live_edit_scene",
    ),
    "Clips & notes": (
        "live_read_clip", "live_update_clip", "live_create_clip", "live_write_notes",
        "live_remove_notes", "live_edit_clip", "live_read_selected_notes", "live_duplicate_loop",
    ),
    "Clip behavior & automation": (
        "live_re_enable_automation", "live_clear_clip_envelopes", "live_set_clip_follow_action",
        "live_get_clip_follow_action", "live_set_clip_launch_mode", "live_set_clip_fades",
        "live_set_clip_markers", "live_manage_warp_markers", "live_set_clip_automation",
        "live_get_clip_automation", "live_add_shaped_automation", "live_set_loop_region",
        "live_set_automation_record",
    ),
    "Arrangement & take lanes": (
        "live_record_to_arrangement", "live_duplicate_to_arrangement", "live_read_arrangement_clips",
        "live_update_arrangement_clip", "live_capture_midi", "live_back_to_arranger",
        "live_create_take_lane", "live_read_arrangement_length", "live_move_arrangement_clip",
        "live_read_arrangement_notes", "live_write_arrangement_notes", "live_remove_arrangement_notes",
        "live_read_take_lanes", "live_update_take_lane", "live_create_take_lane_clip",
    ),
    "Devices & racks": (
        "live_read_device", "live_update_device", "live_create_device", "live_read_macros",
        "live_update_macro", "live_move_device", "live_read_drum_pads", "live_update_drum_pad",
        "live_inspect_plugin", "live_map_rack_magnitude", "live_set_appointed_device",
    ),
    "Groove & timing": (
        "live_groove_pool", "live_commit_groove", "live_set_groove_amount", "live_nudge",
        "live_set_swing",
    ),
    "Generation": (
        "live_generate_euclidean", "live_generate_chords", "live_generate_walking_bass",
        "live_transform_clip", "live_write_drum_grid", "live_create_drum_pattern",
        "live_create_chord_progression", "live_transform_selected_notes",
    ),
    "Analysis & metering": (
        "live_detect_key", "live_read_meter", "live_analyze_audio", "live_compare_audio",
        "live_record_audio", "live_record_and_analyze", "live_analyze_mix", "live_read_dialog",
        "live_read_cpu",
    ),
    "Library & knowledge": (
        "live_library", "live_find_samples", "library_read", "library_search",
        "library_db_search", "live_list_recipes", "live_apply_recipe",
    ),
    # Engine E2 only (the LiveActionsRS Remote Script). These are ALSO withheld
    # at runtime whenever the engine isn't answering, independently of any
    # agent's toggles -- grouping them here just lets an agent turn them off on
    # purpose, e.g. a theory persona that should never load devices.
    "Live browser (needs LiveActionsRS)": (
        "live_browse", "live_load_browser_item", "live_preview_browser_item",
    ),
    "Custom instructions": (
        "live_custom_instructions",
    ),
    "Vocals & audio files (host tools)": (
        "live_tts_vocal", "live_audio_op",
    ),
    "Project files (.als)": (
        "als_summary", "als_list_tracks", "als_extract_midi", "als_diff", "als_find_unfinished",
    ),
    "Selection & view": (
        "live_select", "live_focus_view", "live_get_selected", "live_show_message",
        "live_view_control",
    ),
    "Advanced / raw LOM": (
        "live_api", "live_run_action", "live_read_param_range", "live_set_param_raw",
        "live_delete", "live_duplicate",
    ),
}

# Every toggleable (non-core) tool name, derived from TOOL_GROUPS. Used both
# to seed a fresh agent's tool map and by the "Other" catch-all bucket at the
# UI layer -- a LIVE_TOOLS entry not in this set is not yet categorized.
ALL_TOOL_NAMES: frozenset[str] = frozenset(
    name for names in TOOL_GROUPS.values() for name in names
)

PERSONAS_DIR = Path(__file__).resolve().parent / "genius" / "personas"


def _appdata_personas_dir() -> Path:
    return Path(os.environ.get("APPDATA", str(Path.home()))) / "Live Actions" / "personas"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Minimal frontmatter parser: `key: value`, `key: [a, b]` (may span
    multiple lines up to the closing `]`), and folded `key: >` blocks.

    Deliberately not pyyaml -- this app has no requirements.txt and imports
    no yaml anywhere else, so this ~40-line parser avoids adding an implicit
    dependency for four small config files.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    meta: dict[str, Any] = {}
    i = 1
    while i < end:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            i += 1
            continue

        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()

        if rest in (">", ">-", "|", "|-"):
            i += 1
            block_lines: list[str] = []
            while i < end and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                block_lines.append(lines[i].strip())
                i += 1
            meta[key] = " ".join(l for l in block_lines if l).strip()
            continue

        if rest.startswith("["):
            buf = rest
            while not buf.rstrip().endswith("]") and i + 1 < end:
                i += 1
                buf += " " + lines[i].strip()
            inner = buf.strip()
            if inner.startswith("[") and inner.endswith("]"):
                inner = inner[1:-1]
            meta[key] = [
                item.strip().strip('"').strip("'")
                for item in inner.split(",")
                if item.strip()
            ]
            i += 1
            continue

        meta[key] = rest.strip('"').strip("'")
        i += 1

    body = "\n".join(lines[end + 1:]).strip("\n")
    return meta, body


def _scan_dir(dir_path: Path) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    if not dir_path.is_dir():
        return agents
    for path in sorted(dir_path.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_frontmatter(text)
        slug = str(meta.get("name") or path.stem).strip()
        if not slug:
            continue
        tools_default = meta.get("tools_default")
        if isinstance(tools_default, list):
            tools_default = [str(t).strip() for t in tools_default if str(t).strip()]
        else:
            tools_default = None
        agents.append({
            "slug": slug,
            "title": str(meta.get("title") or slug),
            "description": str(meta.get("description") or ""),
            "tools_default": tools_default,
            "body": body.strip(),
            "path": str(path),
        })
    return agents


def list_agents(settings: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Scan shipped + AppData persona folders. AppData entries with a
    duplicate `name` win, so a persona can be added without touching the repo
    or overridden locally without patching a shipped file."""
    by_slug: dict[str, dict[str, Any]] = {}
    for agent in _scan_dir(PERSONAS_DIR):
        by_slug[agent["slug"]] = agent
    for agent in _scan_dir(_appdata_personas_dir()):
        by_slug[agent["slug"]] = agent
    return sorted(by_slug.values(), key=lambda a: a["title"].lower())


def load_agent(settings: dict[str, Any], slug: str) -> dict[str, Any] | None:
    slug = str(slug or "").strip()
    if not slug:
        return None
    for agent in list_agents(settings):
        if agent["slug"] == slug:
            return agent
    return None


def default_tool_map(agent: dict[str, Any]) -> dict[str, bool]:
    """Seed toggles from the agent's tools_default. Absent tools_default
    means everything toggleable starts on."""
    tools_default = agent.get("tools_default")
    if tools_default:
        wanted = set(tools_default)
        return {name: (name in wanted) for name in ALL_TOOL_NAMES}
    return {name: True for name in ALL_TOOL_NAMES}


def resolve_active(settings: dict[str, Any]) -> tuple[dict[str, Any] | None, set[str] | None]:
    """Returns (agent, allowed_tool_names) for the active agent, or
    (None, None) for stock Genius. A stale active_agent not present in
    enabled_agents (or a since-deleted persona file) degrades to stock
    Genius rather than erroring."""
    active_slug = str(settings.get("active_agent") or "").strip()
    enabled_agents = settings.get("enabled_agents") or []
    if not active_slug or active_slug not in enabled_agents:
        return None, None

    agent = load_agent(settings, active_slug)
    if agent is None:
        return None, None

    stored_map = (settings.get("agent_tool_prefs") or {}).get(active_slug)
    if not isinstance(stored_map, dict):
        stored_map = {}
    default_map = default_tool_map(agent)

    allowed = {
        name for name, default_on in default_map.items()
        if bool(stored_map.get(name, default_on))
    }
    return agent, allowed
