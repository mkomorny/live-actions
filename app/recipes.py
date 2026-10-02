"""Declarative Genre Recipe Engine for Live Actions Helper / Live Actions Genius.

Ported from Pantani/ableton-mind (ADR-0007).
Contains 14 multi-step production recipes across drums, bass, chords, racks,
mixing, arrangements, and live performance.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

RECIPES_DIR = Path(__file__).resolve().parent / "recipes"
PLACEHOLDER_RE = re.compile(r"\{\{([^}]+)\}\}")


def dotted_get(obj: Any, path: str) -> Any:
    """Resolve a dot-separated path on dicts/objects, e.g. 'kick.track.index'."""
    parts = path.strip().split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif hasattr(cur, p):
            cur = getattr(cur, p)
        else:
            return None
    return cur


def resolve_value(val: Any, bindings: dict[str, Any]) -> Any:
    """Recursively resolve {{placeholder}} templates against a bindings dict."""
    if isinstance(val, str):
        # Whole string replacement preserves original types (numbers, dicts, etc.)
        whole_match = re.match(r"^\{\{([^}]+)\}\}$", val.strip())
        if whole_match:
            res = dotted_get(bindings, whole_match.group(1))
            return res if res is not None else val
        
        # Inline string replacement
        def _replace_match(m):
            v = dotted_get(bindings, m.group(1))
            return str(v) if v is not None else ""

        return PLACEHOLDER_RE.sub(_replace_match, val)

    if isinstance(val, list):
        return [resolve_value(item, bindings) for item in val]

    if isinstance(val, dict):
        return {k: resolve_value(v, bindings) for k, v in val.items()}

    return val



# Capabilities satisfied by the OSC bridge alone, with no companion engine.
# "browser" is deliberately absent: it needs engine E2 (the LiveActionsRS
# Remote Script), which may or may not be running right now, so it is supplied
# per call via `capabilities` rather than baked in here.
#
# Callers pass the live set; genius_client.py is the one that knows whether E2
# is answering. Keeping that out of this module avoids an import cycle and
# keeps recipe gating testable without a socket.
AVAILABLE_CAPABILITIES: set[str] = set()


def _resolve_capabilities(capabilities: set[str] | None) -> set[str]:
    return AVAILABLE_CAPABILITIES if capabilities is None else set(capabilities)


def _missing_requirements(recipe: dict[str, Any], capabilities: set[str] | None = None) -> list[str]:
    available = _resolve_capabilities(capabilities)
    return [r for r in (recipe.get("requires") or []) if r not in available]


def list_recipes(
    category: str | None = None, capabilities: set[str] | None = None
) -> list[dict[str, Any]]:
    """Enumerate all available embedded recipes, optionally filtered by category."""
    if not RECIPES_DIR.exists():
        return []

    results = []
    for file_path in RECIPES_DIR.glob("**/*.json"):
        if file_path.name == "recipe-schema.json":
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rec_cat = str(data.get("category") or "")
            if category and rec_cat.lower() != category.lower():
                continue
            missing = _missing_requirements(data, capabilities)
            results.append({
                "id": data.get("id") or str(file_path.relative_to(RECIPES_DIR).with_suffix("")).replace("\\", "/"),
                "name": data.get("name") or file_path.stem,
                "category": rec_cat,
                "version": data.get("version", "1.0"),
                "description": data.get("description", ""),
                "tags": data.get("tags", []),
                "inputs": list((data.get("inputs") or {}).keys()),
                "available": not missing,
                "missing_requirements": missing,
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: (x["category"], x["name"]))


def load_recipe(recipe_id: str) -> dict[str, Any] | None:
    """Load a specific recipe definition by ID."""
    clean_id = recipe_id.strip().replace("\\", "/")
    if clean_id.endswith(".json"):
        clean_id = clean_id[: -len(".json")]
    target = RECIPES_DIR / f"{clean_id}.json"
    if not target.exists():
        # Search by filename
        for p in RECIPES_DIR.glob("**/*.json"):
            if p.name == "recipe-schema.json":
                continue
            if p.stem == clean_id or p.stem == clean_id.split("/")[-1]:
                target = p
                break
    if not target.exists():
        return None
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_recipe(
    recipe_id: str,
    overrides: dict[str, Any] | None = None,
    bridge: Any = None,
    capabilities: set[str] | None = None,
) -> dict[str, Any]:
    """Execute a declarative recipe step-by-step through the Live Actions Bridge."""
    overrides = overrides or {}
    recipe = load_recipe(recipe_id)
    if not recipe:
        return {
            "applied": False,
            "error": f"Recipe '{recipe_id}' not found.",
            "steps": 0,
            "completed": 0,
        }

    missing = _missing_requirements(recipe, capabilities)
    if missing:
        return {
            "applied": False,
            "error": (
                f"Recipe '{recipe.get('id', recipe_id)}' needs the Remote Script companion (engine E2), "
                f"which is not answering right now: {', '.join(missing)}. In Live, set a free Control Surface "
                'slot to "LiveActionsRS" (Preferences > Link/Tempo/MIDI) and restart Live.'
            ),
            "recipe_id": recipe.get("id", recipe_id),
            "steps": 0,
            "completed": 0,
        }

    # Initialize bindings with default inputs overridden by caller args
    bindings: dict[str, Any] = {}
    inputs_def = recipe.get("inputs") or {}
    for key, spec in inputs_def.items():
        if key in overrides:
            bindings[key] = overrides[key]
        else:
            bindings[key] = spec.get("default")

    # A recipe that declares a `track_number` input addresses Live's own
    # 1-based numbering (S1.1) -- reject the old 0-based `track_index`
    # override outright rather than silently reinterpreting it, and bind
    # the 0-based `track_index` the step templates below still use.
    if "track_number" in inputs_def:
        if "track_index" in overrides:
            return {
                "applied": False,
                "error": "Use 'track_number' (1-based, matching Live's own track numbers), not 'track_index', for this recipe's target track.",
                "recipe_id": recipe.get("id", recipe_id),
                "steps": len(recipe.get("steps") or []),
                "completed": 0,
            }
        track_number = bindings.get("track_number")
        if isinstance(track_number, bool) or not isinstance(track_number, int) or track_number < 1:
            return {
                "applied": False,
                "error": f"track_number must be a whole number starting at 1, exactly as Live shows it -- got {track_number!r}.",
                "recipe_id": recipe.get("id", recipe_id),
                "steps": len(recipe.get("steps") or []),
                "completed": 0,
            }
        bindings["track_index"] = track_number - 1

    steps = recipe.get("steps") or []
    completed = 0
    warnings: list[str] = []
    created_tracks: list[dict[str, Any]] = []
    last_track_ref: dict[str, Any] | None = None  # most recent track.upsert binding -- browser.load_item's default target

    if not bridge or not getattr(bridge, "call_live", None):
        return {
            "applied": False,
            "error": "Live Actions Bridge is not connected. Connect the bridge to apply recipes in Ableton.",
            "recipe_id": recipe.get("id", recipe_id),
            "steps": len(steps),
            "completed": 0,
            "bindings": bindings,
        }

    def track_ref_for_step(args: dict[str, Any]) -> dict[str, Any]:
        """Resolve which track a browser.load_item/device.set_parameter step
        targets: the step's own explicit reference, else the most recent
        track.upsert binding -- never a bare, unstated track 0."""
        if str(args.get("track_type") or "").lower() == "master":
            return {"track_type": "master"}
        if args.get("track_index") is not None:
            return {"track_index": int(args["track_index"])}
        if args.get("track_name"):
            return {"track_name": str(args["track_name"])}
        if last_track_ref is not None:
            return dict(last_track_ref)
        raise RuntimeError(
            "no target track: this step needs track_index/track_type/track_name, "
            "or a track.upsert step must run first"
        )

    for i, step in enumerate(steps):
        op = str(step.get("op") or "")
        raw_args = step.get("args") or {}
        resolved_args = resolve_value(raw_args, bindings)
        let_var = step.get("let")
        is_optional = bool(resolved_args.get("optional"))

        try:
            res: dict[str, Any] = {}

            if op == "track.upsert":
                # Find track by name or create
                trk_name = str(resolved_args.get("name") or "Track")
                trk_type = str(resolved_args.get("type") or "midi")
                set_info = bridge.call_live("read_set", {"include": ["tracks"]})
                found_idx = None
                if isinstance(set_info, dict):
                    tracks = (set_info.get("set") or {}).get("tracks") or []
                    for t in tracks:
                        if str(t.get("name") or "").lower() == trk_name.lower():
                            found_idx = t.get("index")
                            break
                was_created = False
                if found_idx is None:
                    create_res = bridge.call_live("create_track", {"name": trk_name, "type": trk_type})
                    if isinstance(create_res, dict) and create_res.get("ok"):
                        found_idx = create_res.get("track_index")
                        was_created = True
                    else:
                        raise RuntimeError(f"could not create track '{trk_name}': {create_res}")
                res = {"track": {"index": found_idx, "name": trk_name}}
                last_track_ref = {"track_index": found_idx}
                if was_created:
                    created_tracks.append({"index": found_idx, "name": trk_name})

            elif op == "clip.create_midi":
                t_idx = int(resolved_args.get("track_index") or 0)
                s_idx = int(resolved_args.get("clip_slot_index") or 0)
                dur = float(resolved_args.get("length_beats") or 4.0)
                name = str(resolved_args.get("name") or "")
                res = bridge.call_live("create_clip", {
                    "track_index": t_idx,
                    "slot_index": s_idx,
                    "length": dur,
                    "name": name,
                })

            elif op == "clip.add_notes":
                t_idx = int(resolved_args.get("track_index") or 0)
                s_idx = int(resolved_args.get("clip_slot_index") or 0)
                notes_in = resolved_args.get("notes") or []
                norm_notes = []
                for n in notes_in:
                    start_val = n.get("start") if "start" in n else n.get("start_time", 0.0)
                    norm_notes.append({
                        "pitch": int(n.get("pitch") or 60),
                        "start_time": float(start_val),
                        "duration": float(n.get("duration") or 0.25),
                        "velocity": int(n.get("velocity") or 100),
                        "mute": bool(n.get("mute", False)),
                    })
                res = bridge.call_live("write_notes", {
                    "track_index": t_idx,
                    "slot_index": s_idx,
                    "notes": norm_notes,
                    "replace": False,
                })

            elif op == "device.set_parameter":
                track_ref = track_ref_for_step(resolved_args)
                param_name = str(resolved_args.get("parameter_name") or "")
                val = resolved_args.get("value")
                device_name = resolved_args.get("device_name")
                if device_name:
                    # Resolve by name at call time instead of trusting a
                    # hardcoded ordinal device_index -- robust to whatever
                    # position browser.load_item actually landed the device
                    # at (including a track the step had to fall back to).
                    track_info = bridge.call_live("read_track", {**track_ref, "include": ["devices"]})
                    devices = (track_info.get("devices") or []) if isinstance(track_info, dict) else []
                    d_idx = None
                    for d in devices:
                        if str(d.get("name") or "").lower() == str(device_name).lower():
                            d_idx = d.get("index")
                            break
                    if d_idx is None:
                        raise RuntimeError(f"device '{device_name}' not found on track {track_ref}")
                else:
                    d_idx = int(resolved_args.get("device_index") or 0)
                res = bridge.call_live("update_device", {
                    **track_ref,
                    "device_index": d_idx,
                    "params": [{"name": param_name, "value": val}],
                })
                skipped = res.get("params_skipped") if isinstance(res, dict) else None
                if skipped:
                    raise RuntimeError(f"parameter '{param_name}' was not applied: {skipped}")

            elif op == "transport.set_tempo":
                bpm = float(resolved_args.get("bpm") or resolved_args.get("tempo") or 120.0)
                res = bridge.call_live("update_set", {"tempo": bpm})

            elif op == "browser.load_item":
                # Best-effort native device loading matching browser path --
                # the device name is the folder segment right after the
                # top-level browser category (path[1]), e.g.
                # ["instruments", "Drift", "Init"] -> "Drift". path[-1] is
                # the leaf preset/subfolder name, which create_device can't
                # load anyway (no Browser/BrowserItem class in this LOM --
                # only a real native device shell, until the E2 companion).
                path_parts = resolved_args.get("path") or []
                if len(path_parts) < 2:
                    raise RuntimeError(f"browser.load_item path needs at least [category, device_name]: {path_parts}")
                device_name = path_parts[1]
                track_ref = track_ref_for_step(resolved_args)
                res = bridge.call_live("create_device", {**track_ref, "name": device_name})

            if isinstance(res, dict) and res.get("ok") is False:
                raise RuntimeError(f"{op} failed: {res.get('error') or res}")

            if let_var:
                bindings[let_var] = res

            completed += 1

        except Exception as exc:
            if is_optional:
                warnings.append(f"Step {i + 1} ({op}) skipped (optional): {exc}")
                completed += 1
                continue
            return {
                "applied": False,
                "created_tracks": created_tracks,
                "warnings": warnings,
                "recipe_id": recipe.get("id", recipe_id),
                "steps": len(steps),
                "completed": completed,
                "failed_step": i + 1,
                "error": f"Step {i + 1} ({op}) failed: {exc}",
                "bindings": bindings,
            }

    result = {
        "applied": True,
        "recipe_id": recipe.get("id", recipe_id),
        "steps": len(steps),
        "completed": completed,
        "bindings": bindings,
        "created_tracks": created_tracks,
        "message": f"Successfully applied recipe '{recipe.get('name', recipe_id)}' ({completed}/{len(steps)} steps).",
    }
    if warnings:
        result["warnings"] = warnings
    return result
