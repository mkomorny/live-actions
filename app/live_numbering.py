"""Live Actions -- 1-based/0-based numbering translation between the model and the bridge.

Every positional field the model (Genius/xAI/Gemini/Claude) sees is 1-based,
exactly as Live's own UI shows it: Live's track 1 is track_number 1, not 0.
The bridge and live-actions-pal.js stay 0-based internally, matching the Live
Object Model -- live_api is the only surface where a raw 0-based LOM index is
still expected from the model, since it addresses the LOM directly.

This module is the single place that translates between the two directions:
  args_from_model()  1-based model args  -> 0-based dict for call_live()
  model_view()/mv_json()  0-based bridge result -> 1-based dict/JSON for display

See docs/plans/v1.0.32-phase4-numbering-and-lom-fixes.md (Master Plan S1.1)
for the full design this implements.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

# ── Errors ───────────────────────────────────────────────────────────────────


class ModelArgError(Exception):
    """A model-supplied tool-call argument failed 1-based validation, or used
    a raw 0-based/internal key that must never reach the model surface."""


# ── Constants ────────────────────────────────────────────────────────────────

# `<family>_number` (1-based, model-facing) -> `<family>_index` (0-based, bridge-facing).
_INDEX_FAMILIES = (
    "track", "slot", "scene", "device", "clip", "arrangement_clip",
    "take_lane", "groove", "source_track", "source_clip", "target_track",
    "to_track", "target_slot", "new_device", "param",
)

# Raw 0-based / internal keys the model must never send directly.
_STRAY_KEYS = ("index", "slot", "ids", "to_slot")

_RETURN_LETTERS = "ABCDEFGHIJKL"

# model_view(): keys whose value is a position but is never renamed/shifted.
_NEVER_TOUCH = {"color_index", "note"}
# model_view(): parent container key -> what happens to a plain "index" key inside it.
_DROP_INDEX_PARENTS = {"sends", "locators", "drum_pads"}
_KEEP_INDEX_PARENTS = {"macros"}
# model_view(): non-"*_index"-suffixed keys that are still 0-based positions.
_NONSTANDARD_INDEX_KEYS = {
    "soloed_track": "soloed_track_number",
    "source_slot": "source_slot_number",
}

_PATH_SEG_RE = re.compile(r"^([tdcr])(\d+)$", re.IGNORECASE)


# ── Model -> bridge (args_from_model) ───────────────────────────────────────


def parse_live_number(key: str, value: Any, maximum: int | None = None) -> int:
    """Validate a 1-based *_number value and convert it to a 0-based index.

    Rejects bool (a Python bool is an int; a stray True/False is a coding
    mistake, not a real number 1), 0, negative numbers, and non-integers,
    with a message telling the model numbers start at 1 exactly as Live
    shows them -- never a bare "invalid value" that invites guessing ±1.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelArgError(
            f"{key} must be a whole number -- numbers start at 1 exactly as shown in Live."
        )
    if value < 1:
        raise ModelArgError(
            f"{key}={value} is invalid -- numbers start at 1 exactly as shown in Live."
        )
    if maximum is not None and value > maximum:
        raise ModelArgError(
            f"{key}={value} is out of range -- Live only shows {maximum} here."
        )
    return value - 1


def _return_letter_to_index(key: str, value: Any) -> int:
    if not isinstance(value, str) or len(value) != 1 or value.upper() not in _RETURN_LETTERS:
        raise ModelArgError(
            f"{key} must be a single letter A-L, matching Live's Return A/B/C... labels."
        )
    return _RETURN_LETTERS.index(value.upper())


def _convert_device_path(raw: str) -> str:
    """'t3/d1/c2/pC1' (1-based t/d/c) -> 't2/d0/c1/pC1' (0-based). A p<note>
    or p<number> drum-pad segment is never touched -- it names a pad, not a
    position."""
    parts = raw.split("/")
    out_parts = []
    for part in parts:
        m = _PATH_SEG_RE.match(part)
        if not m:
            out_parts.append(part)
            continue
        prefix, num = m.group(1), int(m.group(2))
        if num < 1:
            raise ModelArgError(
                f"Path segment '{part}' is invalid -- numbers start at 1 exactly as shown in Live."
            )
        out_parts.append(f"{prefix}{num - 1}")
    return "/".join(out_parts)


def args_from_model(fn_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Translate a model-facing (1-based) tool-call args dict into the
    0-based dict the bridge / pal.js dispatch expects.

    Raises ModelArgError on a stray 0-based key or an invalid *_number.
    live_api is the one tool skipped entirely -- it addresses the LOM
    directly and is documented to the model as 0-based.
    """
    if fn_name == "live_api":
        return dict(args)

    out: dict[str, Any] = {}

    for key, value in args.items():
        if value is None:
            continue

        if key in _STRAY_KEYS:
            raise ModelArgError(
                f"'{key}' is not a valid argument -- use the matching *_number field instead (e.g. track_number)."
            )
        if key.endswith("_index"):
            hint = key[: -len("_index")]
            raise ModelArgError(
                f"'{key}' is not a valid argument -- use '{hint}_number' instead (1-based, exactly as Live shows it)."
            )

        if key == "track_name":
            out[key] = value
            continue

        matched_family = None
        for fam in _INDEX_FAMILIES:
            if key == fam + "_number":
                matched_family = fam
                break
        if matched_family:
            out[matched_family + "_index"] = parse_live_number(key, value)
            continue

        if key == "to_slot_number":
            out["to_slot"] = parse_live_number(key, value)
            continue

        if key == "return_letter":
            out["return_index"] = _return_letter_to_index(key, value)
            continue

        out[key] = value

    # --- per-tool special cases, applied after the generic pass above ----------
    if fn_name == "live_update_macro" and "macro_number" in args:
        n = args["macro_number"]
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ModelArgError(
                "macro_number must be a whole number starting at 1, matching Live's Macro 1..16 labels."
            )
        out["macro"] = str(n)  # pal.js's own macro lookup already skips "Device On" -- no shift here.

    if fn_name == "live_map_rack_magnitude" and "macro_number" in args:
        out["macro_index"] = parse_live_number("macro_number", args["macro_number"])

    if fn_name == "live_create_track" and "position_number" in args:
        out["index"] = parse_live_number("position_number", args["position_number"])

    if fn_name == "live_update_scene" and "scene_numbers" in args:
        nums = args["scene_numbers"]
        if not isinstance(nums, list) or not nums:
            raise ModelArgError("scene_numbers must be a non-empty array of 1-based scene numbers.")
        out["ids"] = ",".join(str(parse_live_number("scene_numbers[]", n)) for n in nums)

    if fn_name == "live_detect_key" and "track_numbers" in args:
        nums = args["track_numbers"]
        if not isinstance(nums, list) or not nums:
            raise ModelArgError("track_numbers must be a non-empty array of 1-based track numbers.")
        out["track_index"] = ",".join(str(parse_live_number("track_numbers[]", n)) for n in nums)

    if fn_name == "live_select" and "track_number" in args and "slot_number" in args:
        t = parse_live_number("track_number", args["track_number"])
        s = parse_live_number("slot_number", args["slot_number"])
        out["slot"] = f"{t}/{s}"
        out.pop("track_index", None)
        out.pop("slot_index", None)

    if fn_name == "live_run_action" and isinstance(args.get("payload"), dict) and "tracks" in args["payload"]:
        raw_tracks = args["payload"]["tracks"]
        if not isinstance(raw_tracks, list):
            raise ModelArgError("payload.tracks must be an array of {track_number, kind}.")
        built = []
        for entry in raw_tracks:
            if not isinstance(entry, dict) or "track_number" not in entry:
                raise ModelArgError("Each payload.tracks[] entry needs a track_number and a kind.")
            kind = str(entry.get("kind") or "midi").lower()
            n = parse_live_number("track_number", entry["track_number"])
            if kind == "return":
                path = f"live_set return_tracks {n}"
            elif kind == "master":
                path = "live_set master_track"
            else:
                path = f"live_set tracks {n}"
            built.append({"path": path, "kind": kind})
        out["payload"] = dict(args["payload"])
        out["payload"]["tracks"] = built

    for path_key in ("path", "device_path"):
        if path_key in out and isinstance(out[path_key], str):
            out[path_key] = _convert_device_path(out[path_key])

    return out


# ── Bridge -> model (model_view / mv_json) ──────────────────────────────────


def _mv_walk(node: Any, parent_key: str | None) -> Any:
    if isinstance(node, list):
        return [_mv_walk(item, parent_key) for item in node]
    if not isinstance(node, dict):
        return node

    result: dict[str, Any] = {}
    for key, value in node.items():
        if key in _NEVER_TOUCH:
            result[key] = _mv_walk(value, key)
            continue

        if key == "path" and isinstance(value, str) and value.startswith("live_set"):
            continue  # raw LOM paths are dropped from model-facing output

        if key == "return_index":
            result["return_letter"] = (
                _RETURN_LETTERS[value] if isinstance(value, int) and 0 <= value < len(_RETURN_LETTERS) else None
            )
            continue

        if key == "index" and parent_key in _KEEP_INDEX_PARENTS:
            result[key] = value
            continue
        if key == "index" and parent_key in _DROP_INDEX_PARENTS:
            continue

        if key in _NONSTANDARD_INDEX_KEYS and (value is None or isinstance(value, int)):
            new_key = _NONSTANDARD_INDEX_KEYS[key]
            result[new_key] = None if value in (None, -1) else value + 1
            continue

        if (key == "index" or key.endswith("_index")) and (value is None or isinstance(value, int)):
            new_key = "number" if key == "index" else key[: -len("_index")] + "_number"
            result[new_key] = None if value in (None, -1) else value + 1
            continue

        if key == "slot" and isinstance(value, int):
            result["slot_number"] = value + 1
            continue

        result[key] = _mv_walk(value, key)
    return result


def model_view(obj: Any, fn_name: str = "") -> Any:
    """Deep-copy `obj`, converting 0-based index/slot fields to 1-based
    *_number fields for model-facing display.

    fn_name is accepted for future per-tool overrides and logging; the
    current conversion rules are generic across every tool except live_api,
    whose raw results callers must not pass through this at all.
    """
    return _mv_walk(copy.deepcopy(obj), parent_key=None)


def mv_json(obj: Any, fn_name: str = "", **json_kwargs: Any) -> str:
    kwargs = {"indent": 2}
    kwargs.update(json_kwargs)
    return json.dumps(model_view(obj, fn_name), **kwargs)


def live_track_label(track: dict[str, Any]) -> str:
    """'Live track 3 "Bass"' / 'return A "Reverb"' / 'Master' from a raw
    (0-based) track dict with index/kind/name."""
    kind = str(track.get("kind") or track.get("track_type") or "").lower()
    name = track.get("name")
    if kind == "master":
        return "Master"
    if kind == "return":
        idx = track.get("index", track.get("return_index"))
        letter = _RETURN_LETTERS[idx] if isinstance(idx, int) and 0 <= idx < len(_RETURN_LETTERS) else "?"
        return f'return {letter} "{name}"' if name else f"return {letter}"
    idx = track.get("index")
    n = idx + 1 if isinstance(idx, int) else "?"
    return f'Live track {n} "{name}"' if name else f"Live track {n}"
