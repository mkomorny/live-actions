"""Adapter for the "audio-sample" Live Actions host tool.

tools/audio-sample/tool.json flattens all 17 ops from ops/registry.py into one
field form, gated by `showIf` on a single "operation" select (see
make_tool_json.py in the `ffmpeg tools` repo, which generates that manifest —
this module is its runtime counterpart and must stay in sync with it: the
category-prefixed display names and the field-id namespacing scheme
(`field_prefix`) are duplicated here on purpose, byte-for-byte, so a name
generated on one side always resolves on the other).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import settings_store

from .ops import registry

FIELD_SEP = "__"

# Must match make_tool_json.py's SHORT_CATEGORY exactly.
_SHORT_CATEGORY: dict[str, str] = {
    "Trim, Fades & Levels": "Trim, Fades & Levels",
    "Convert": "Convert",
    "Reverse, Pitch & Time": "Reverse, Pitch & Time",
    "Effects (100% wet)": "Effects",
    "Generators (no input file)": "Generators",
}


def field_prefix(op_id: str) -> str:
    return op_id.replace("-", "_") + FIELD_SEP


def _display_name(op: dict[str, Any]) -> str:
    short = _SHORT_CATEGORY.get(op["category"], op["category"])
    return "%s — %s" % (short, op["name"])


_BY_DISPLAY_NAME: dict[str, dict[str, Any]] = {_display_name(op).lower(): op for op in registry.ALL_OPS}


def _resolve_op(raw: str) -> dict[str, Any] | None:
    key = (raw or "").strip()
    if not key:
        return None
    return _BY_DISPLAY_NAME.get(key.lower()) or registry.OPS_BY_ID.get(key)


def _op_fields(op: dict[str, Any], submitted: dict[str, Any]) -> dict[str, Any]:
    """Un-namespace this op's fields, driven by the op's own spec (not what was submitted).

    Iterating the op's field list — rather than filtering the submitted dict — guarantees
    every key the op expects is present (backfilled from its own default if a manifest is
    stale), and means a stale namespaced value left over from a different operation is
    never read, since we only ever look for keys under this op's own prefix.
    """
    prefix = field_prefix(str(op["id"]))
    out: dict[str, Any] = {}
    for spec in op.get("fields") or []:
        field_id = str(spec["id"])
        raw = submitted.get(prefix + field_id)
        out[field_id] = str(raw) if raw is not None else str(spec.get("default") or "")
    return out


def run(fields: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Host handler for the "audio-sample" tool. Never raises."""
    raw_op = str(fields.get("operation") or "").strip()
    if not raw_op:
        return {"ok": False, "message": "Pick an operation first."}
    op = _resolve_op(raw_op)
    if op is None:
        return {"ok": False, "message": 'Unknown operation "%s". Pick one from the Operation list.' % raw_op}

    needs_input = bool(op.get("needs_input", True))
    input_path = str(fields.get("input_file") or "").strip() or None
    if needs_input and not input_path:
        return {"ok": False, "message": 'Pick an input audio file for "%s".' % op["name"]}
    if not needs_input:
        input_path = None  # generators ignore a stale hidden input_file value

    cfg = dict(settings)
    if not str(cfg.get("audio_sample_output_dir") or "").strip():
        cfg["audio_sample_output_dir"] = str(settings_store.samples_dir(settings) / "Audio Samples")

    out_dir = Path(cfg["audio_sample_output_dir"])
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {"ok": False, "message": "Could not create the output folder %s: %s" % (out_dir, exc)}

    try:
        result = op["run"](input_path, _op_fields(op, fields), cfg)
    except Exception as exc:  # an op must never take the app down; this is the last backstop
        result = {"ok": False, "message": "Unexpected error: %s" % exc}

    message = str(result.get("message") or "")
    result["message"] = "%s — %s" % (op["name"], message) if message else op["name"]
    return result


def describe_ops() -> list[dict[str, Any]]:
    """Every op as plain data: what it is, whether it needs an input file, and its fields.

    Exists so callers that are not the Tool screen (Genius's `live_audio_op`) can list the
    operations without reaching into `registry.ALL_OPS` and re-deriving the field/prefix
    scheme themselves -- the duplication warning in this module's header is about exactly
    that kind of second implementation drifting.
    """
    out: list[dict[str, Any]] = []
    for op in registry.ALL_OPS:
        fields = []
        for spec in op.get("fields") or []:
            field: dict[str, Any] = {
                "id": str(spec["id"]),
                "label": str(spec.get("label") or spec["id"]),
                "default": str(spec.get("default") or ""),
            }
            if spec.get("options"):
                field["options"] = [str(o) for o in spec["options"]]
            if spec.get("hint"):
                field["hint"] = str(spec["hint"])
            fields.append(field)
        out.append({
            "id": str(op["id"]),
            "name": str(op["name"]),
            "category": str(op["category"]),
            "description": str(op.get("description") or ""),
            "needs_input": bool(op.get("needs_input", True)),
            "fields": fields,
        })
    return out


def run_op(op_id: str, input_path: str | None, params: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Run one op from un-namespaced field names -- the shape a caller that isn't a form has.

    Re-namespaces onto `run()` rather than calling `op["run"]` directly so both entry points
    share one output-folder resolution, one last-resort error backstop, and one message format.
    """
    op = _resolve_op(op_id)
    if op is None:
        known = ", ".join(sorted(registry.OPS_BY_ID))
        return {"ok": False, "message": 'Unknown operation "%s". Known operations: %s' % (op_id, known)}
    prefix = field_prefix(str(op["id"]))
    fields: dict[str, Any] = {"operation": str(op["id"]), "input_file": input_path or ""}
    for key, value in (params or {}).items():
        fields[prefix + str(key)] = value
    return run(fields, settings)
