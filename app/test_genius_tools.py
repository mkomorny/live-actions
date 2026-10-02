"""Contract tests for the 108 Genius live_* tools (v1.0.26 audit).

Written for the v1.0.26 Genius Live Actions audit
(docs/plans/v1.0.26-genius-live-actions-audit-fixes.md): before the Phase 1
fixes in that pass, this file failed on the C1-C4 / M2-M3 checks below --
the generators wrote stringified JSON where the bridge expected a real
list (C1), the recipe engine did the same plus sent update_device the
wrong payload shape (C2), live_add_shaped_automation had no route at all
(C3), live_analyze_mix read the wrong envelope/keys (C4), live_get_selected
always reported device index -1 (M2), and session_snapshot exposed
undefined signature fields (M3).

This does NOT touch a running Ableton Live -- it is static/offline, same
constraint as the audit itself. It cannot catch a LOM property that
doesn't exist or behaves differently than documented (LOM-VERIFY items);
only Phase 4's live matrix in Ableton can confirm those.

Run from app\\:  python -m unittest test_genius_tools
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import genius_client
import genius_db
import mix_checker
import recipes as recipes_mod
from genius_client import LIVE_TOOLS, call_live_tool

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
BRIDGE_JS = (REPO_ROOT / "bridge" / "live-actions-bridge.js").read_text(encoding="utf-8")
PAL_JS = (REPO_ROOT / "bridge" / "live-actions-pal.js").read_text(encoding="utf-8")
GENIUS_SRC = (APP_DIR / "genius_client.py").read_text(encoding="utf-8")

# Tools that never reach the bridge -- local files, xAI/audio-analysis
# helpers, or higher-level orchestration that itself calls other bridge
# actions (already covered by their own tests below). Routing verification
# doesn't apply to these.
LOCAL_ONLY_PREFIXES = ("library_", "als_")
LOCAL_ONLY_NAMES = {
    "live_context",
    "live_find_samples",
    "live_analyze_audio",
    "live_compare_audio",
    "live_record_audio",
    "live_record_and_analyze",
    "live_list_recipes",
    "live_apply_recipe",
    "live_session_diff",
    "live_analyze_mix",       # calls "read_set" itself, checked separately
    "live_add_shaped_automation",  # calls "set_clip_automation" itself, checked separately
    "live_generate_euclidean",     # calls "write_notes" itself, checked separately
    "live_generate_chords",
    "live_generate_walking_bass",
    "live_transform_clip",
    "live_write_drum_grid",
}


class FakeBridge:
    """Records every call_live() invocation and returns a plausible reply.

    Defaults are tuned so recipe/tool code paths that branch on `ok` take
    their success branch, so end-to-end flows (e.g. a full recipe) exercise
    every step instead of bailing out on the first one.
    """

    def __init__(self, overrides: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, dict, float]] = []
        self.overrides = overrides or {}

    def call_live(self, action: str, params: dict | None = None, timeout: float = 10.0):
        params = params or {}
        self.calls.append((action, params, timeout))
        if action in self.overrides:
            override = self.overrides[action]
            return override(params) if callable(override) else override
        return self._default(action, params)

    def _default(self, action: str, params: dict) -> dict:
        if action == "read_set":
            return {"ok": True, "set": {"tracks": [], "track_count": 0}}
        if action == "create_track":
            return {"ok": True, "track_index": 0, "message": "created"}
        if action == "read_clip":
            return {"ok": True, "notes": [], "length": 4.0}
        if action == "session_snapshot":
            return {"ok": True}
        return {"ok": True, "message": f"{action} applied"}

    def calls_for(self, action: str) -> list[dict]:
        return [p for (a, p, _t) in self.calls if a == action]


def _tool_names() -> list[str]:
    return [t["name"] for t in LIVE_TOOLS]


def _tool_schema(name: str) -> dict:
    for t in LIVE_TOOLS:
        if t["name"] == name:
            return t
    raise KeyError(name)


class RoutingTests(unittest.TestCase):
    """Every LIVE_TOOLS entry must resolve to *some* handler."""

    def setUp(self) -> None:
        self.python_branches = set(re.findall(r'if fn_name == "(\w+)"', GENIUS_SRC))
        # JS route names: palHandle's `name === "x"` and handleLiveCall's
        # `action === "x"` (both bridge files, since live-actions-pal.js is
        # include()-d into live-actions-bridge.js's scope at runtime).
        js_src = BRIDGE_JS + "\n" + PAL_JS
        self.js_routes = set(re.findall(r'(?:name|action) === "(\w+)"', js_src))

    def test_every_tool_name_is_unique(self) -> None:
        names = _tool_names()
        self.assertEqual(len(names), len(set(names)), "duplicate tool name in LIVE_TOOLS")

    def test_every_schema_is_well_formed(self) -> None:
        for t in LIVE_TOOLS:
            with self.subTest(tool=t["name"]):
                self.assertIn("name", t)
                self.assertIn("description", t)
                self.assertTrue(t["description"], f"{t['name']} has an empty description")
                params = t["parameters"]
                self.assertEqual(params["type"], "object")
                for req in params["required"]:
                    self.assertIn(req, params["properties"], f"{t['name']} requires undeclared property '{req}'")

    def test_every_tool_has_a_route(self) -> None:
        missing = []
        for name in _tool_names():
            if name in LOCAL_ONLY_NAMES or name.startswith(LOCAL_ONLY_PREFIXES):
                continue
            if name in self.python_branches:
                continue
            action = name.replace("live_", "")
            if action == "set_tempo":
                action = "update_set"
            if action == "run_action":
                action = "run_tool"
            if action in self.js_routes:
                continue
            missing.append(name)
        self.assertEqual(missing, [], f"tools with no Python branch and no JS route: {missing}")


class NumberingSchemaTests(unittest.TestCase):
    """v1.0.32 S1.1/S1.6: every LIVE_TOOLS schema is 1-based end to end --
    no raw *_index/index/slot/ids leak to the model as an input name, every
    *_number is a min-1 integer, and a FakeBridge whose replies are
    deliberately *_index-heavy never leaks that into the formatted string a
    tool call actually returns."""

    STRAY_KEY_NAMES = {"index", "slot", "ids"}

    def _walk_schema_keys(self, node, tool_name, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("description", "enum"):
                    continue
                if k in self.STRAY_KEY_NAMES or (k.endswith("_index") and k != "live_api"):
                    self.fail(f"{tool_name}: schema property '{path}{k}' is a raw 0-based key -- must be *_number")
                if k == "type" and v == "integer" and isinstance(node, dict) and any(
                    kk.endswith("_number") for kk in [path.rstrip(".").split(".")[-1]]
                ):
                    self.assertEqual(node.get("minimum"), 1, f"{tool_name}: '{path}' integer *_number field needs minimum:1")
                self._walk_schema_keys(v, tool_name, f"{path}{k}.")
        elif isinstance(node, list):
            for item in node:
                self._walk_schema_keys(item, tool_name, path)

    def test_no_raw_index_keys_anywhere_in_schemas(self) -> None:
        for t in LIVE_TOOLS:
            if t["name"] == "live_api":
                continue
            with self.subTest(tool=t["name"]):
                self._walk_schema_keys(t["parameters"]["properties"], t["name"])

    def _minimal_args_for(self, tool: dict) -> dict:
        params = tool["parameters"]
        props = params["properties"]
        args: dict[str, Any] = {}
        for key in params.get("required", []):
            spec = props.get(key, {})
            if key == "live_api":
                continue
            if spec.get("enum"):
                args[key] = spec["enum"][0]
            elif spec.get("type") == "integer":
                args[key] = 1
            elif spec.get("type") == "number":
                args[key] = 1.0
            elif spec.get("type") == "boolean":
                args[key] = True
            elif spec.get("type") == "array":
                item_spec = spec.get("items", {})
                if item_spec.get("type") == "integer":
                    args[key] = [1]
                elif item_spec.get("type") == "object":
                    args[key] = [{k2: (1 if v2.get("type") == "integer" else "x")
                                   for k2, v2 in item_spec.get("properties", {}).items()}]
                else:
                    args[key] = []
            elif spec.get("type") == "object":
                args[key] = {}
            else:
                args[key] = "x"
        return args

    class _IndexHeavyFakeBridge(FakeBridge):
        """Every reply is deliberately riddled with raw 0-based *_index
        fields and 'index'/'slot' keys, mimicking real bridge JSON, so the
        model-facing formatter is the only thing that could strip them."""

        def _default(self, action: str, params: dict) -> dict:
            return {
                "ok": True,
                "message": f"{action} applied",
                "track_index": 2,
                "slot_index": 1,
                "device_index": 0,
                "scene_index": 0,
                "clip_index": 3,
                "tracks": [{"index": 0, "name": "Kick", "clip_slots": [{"index": 0, "has_clip": True}]}],
                "devices": [{"index": 0, "name": "EQ Eight"}],
                "params_set": ["Volume"],
            }

    def test_fuzz_index_heavy_bridge_never_leaks_index_in_output(self) -> None:
        bridge = self._IndexHeavyFakeBridge()
        skipped_prefixes = ("library_", "als_")
        for t in LIVE_TOOLS:
            name = t["name"]
            if name == "live_api" or name.startswith(skipped_prefixes):
                continue
            args = self._minimal_args_for(t)
            with self.subTest(tool=name):
                result = _call_like_ask_genius(bridge, name, args)
                self.assertIsInstance(result, str)
                self.assertNotIn("_index", result, f"{name} leaked a raw 0-based *_index into model-facing output: {result[:200]}")


def _call_like_ask_genius(bridge: FakeBridge, name: str, args: dict) -> str:
    """Mirrors the H1 try/except around call_live_tool in ask_genius --
    call_live_tool is allowed to raise (e.g. an unrecognized chord key
    raises ValueError on purpose, per the Low-item fix, rather than
    silently defaulting to C), but the chat loop that calls it must never
    crash. This is the contract that actually matters in production."""
    try:
        return call_live_tool(bridge, name, args, settings={})
    except Exception as exc:  # noqa: BLE001 - mirrors ask_genius's own broad catch
        return f"ERROR: {name} failed: {exc}"


class NeverRaisesTests(unittest.TestCase):
    """The tool-call loop (call_live_tool wrapped as ask_genius wraps it,
    H1) must always produce a string reply, even given junk args -- wrong
    types, missing keys, or semantically invalid values."""

    def test_junk_args_never_crash_the_chat_loop(self) -> None:
        bridge = FakeBridge()
        junk_variants = [
            {},
            {"track_index": "not a number", "slot_index": None},
            {"pulses": "five", "steps": -1},
            {"notes": "not json or pal text {{{"},
            {"progression": None, "key": "H#"},
        ]
        for name in _tool_names():
            for junk in junk_variants:
                with self.subTest(tool=name, junk=junk):
                    result = _call_like_ask_genius(bridge, name, junk)
                    self.assertIsInstance(result, str)

    def test_call_live_tool_itself_never_raises_on_missing_or_mistyped_numbers(self) -> None:
        # The stricter property: bad *types* for numeric fields (the most
        # common case -- a model sending "4" vs 4, or omitting a field)
        # must not need the outer try/except at all, since _int/_float
        # degrade to a default instead of raising (H1-adjacent hardening).
        bridge = FakeBridge()
        junk_variants = [
            {},
            {"track_index": "not a number", "slot_index": None},
            {"pulses": "five", "steps": -1},
            {"notes": "not json or pal text {{{"},
        ]
        for name in _tool_names():
            for junk in junk_variants:
                with self.subTest(tool=name, junk=junk):
                    try:
                        result = call_live_tool(bridge, name, junk, settings={})
                    except Exception as exc:  # noqa: BLE001
                        self.fail(f"{name} raised {type(exc).__name__}({exc}) on junk args {junk}")
                    self.assertIsInstance(result, str)


class GeneratorPayloadTests(unittest.TestCase):
    """C1: generators must send write_notes a real list of note dicts."""

    NOTE_KEYS = {"pitch", "start_time", "duration", "velocity"}

    def _assert_real_note_list(self, bridge: FakeBridge, action: str = "write_notes") -> list[dict]:
        calls = bridge.calls_for(action)
        self.assertEqual(len(calls), 1, f"expected exactly one {action} call, got {len(calls)}")
        notes = calls[0]["notes"]
        self.assertIsInstance(notes, list, f"{action} notes payload must be a list, not {type(notes)}")
        self.assertTrue(notes, "expected at least one note")
        for n in notes:
            self.assertIsInstance(n, dict)
            self.assertTrue(self.NOTE_KEYS.issubset(n.keys()), f"note missing keys: {n}")
        return notes

    def test_euclidean_writes_list(self) -> None:
        bridge = FakeBridge()
        call_live_tool(bridge, "live_generate_euclidean", {"pulses": 4, "steps": 16, "track_number": 1, "slot_number": 1}, settings={})
        self._assert_real_note_list(bridge)

    def test_chords_write_list(self) -> None:
        bridge = FakeBridge()
        call_live_tool(bridge, "live_generate_chords", {"progression": "I-V-vi-IV", "key": "C", "track_number": 1, "slot_number": 1}, settings={})
        self._assert_real_note_list(bridge)

    def test_walking_bass_writes_list(self) -> None:
        bridge = FakeBridge()
        call_live_tool(bridge, "live_generate_walking_bass", {"progression": "ii-V-I-I", "key": "C", "track_number": 1, "slot_number": 1}, settings={})
        self._assert_real_note_list(bridge)

    def test_drum_grid_writes_list(self) -> None:
        bridge = FakeBridge()
        call_live_tool(bridge, "live_write_drum_grid", {"grid": "K: x...x...x...x...", "track_number": 1, "slot_number": 1}, settings={})
        self._assert_real_note_list(bridge)

    def test_transform_clip_writes_list(self) -> None:
        bridge = FakeBridge(overrides={
            "read_clip": {"ok": True, "notes": [
                {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
                {"pitch": 64, "start_time": 1.0, "duration": 1.0, "velocity": 100},
            ]},
        })
        call_live_tool(bridge, "live_transform_clip", {"op": "invert", "track_number": 1, "slot_number": 1}, settings={})
        self._assert_real_note_list(bridge)

    def test_invalid_key_raises_instead_of_silently_defaulting_to_c(self) -> None:
        # Low item: an unrecognized key must not silently become C.
        bridge = FakeBridge()
        with self.assertRaises(Exception):
            from algorithmic_generators import generate_voiced_progression
            generate_voiced_progression("I-V-vi-IV", key="H#")


class ShapedAutomationTests(unittest.TestCase):
    """C3: live_add_shaped_automation must reach set_clip_automation with a
    real envelope of the requested length."""

    def test_ends_in_set_clip_automation_call(self) -> None:
        bridge = FakeBridge(overrides={
            "read_clip": {"ok": True, "length": 8.0},
            "set_clip_automation": {"ok": True, "points_added": 16},
        })
        result = call_live_tool(bridge, "live_add_shaped_automation", {
            "track_number": 1, "slot_number": 1, "parameter_name": "Volume",
            "shape": "sine", "cycles": 2, "points": 16,
        }, settings={})
        calls = bridge.calls_for("set_clip_automation")
        self.assertEqual(len(calls), 1)
        envelope = calls[0]["envelope_data"]
        self.assertEqual(len(envelope), 16)
        for pt in envelope:
            self.assertIn("time", pt)
            self.assertIn("value", pt)
        self.assertNotIn("ERROR", result)

    def test_missing_length_is_read_from_clip(self) -> None:
        bridge = FakeBridge(overrides={
            "read_clip": {"ok": True, "length": 4.0},
        })
        call_live_tool(bridge, "live_add_shaped_automation", {
            "track_number": 1, "slot_number": 1, "parameter_name": "Volume", "shape": "saw",
        }, settings={})
        self.assertEqual(len(bridge.calls_for("read_clip")), 1)
        self.assertEqual(len(bridge.calls_for("set_clip_automation")), 1)


class RecipeTests(unittest.TestCase):
    """C2: recipes must send real note lists and the params:[...] shape,
    and must fail the recipe on a step that reports ok:false. S1.4 (v1.0.32):
    reese now targets Drift (Live 12 Standard substitute for Suite-only
    Operator) and marks its Operator-shaped params optional -- a
    device.set_parameter step now resolves its target by device_name via
    read_track, not a hardcoded device_index, so FakeBridge's read_track
    must actually list that device for the lookup to succeed."""

    def _bridge_with_devices(self, device_names: list[str], overrides: dict | None = None) -> "FakeBridge":
        merged = dict(overrides or {})
        merged.setdefault("read_track", {
            "ok": True,
            "devices": [{"index": i, "name": n} for i, n in enumerate(device_names)],
        })
        return FakeBridge(overrides=merged)

    def test_reese_bass_recipe_end_to_end(self) -> None:
        bridge = self._bridge_with_devices(["Drift", "Chorus-Ensemble"])
        result = recipes_mod.apply_recipe("bass/reese", bridge=bridge)
        self.assertTrue(result["applied"], result.get("error"))

        add_notes_calls = bridge.calls_for("write_notes")
        self.assertEqual(len(add_notes_calls), 1)
        notes = add_notes_calls[0]["notes"]
        self.assertIsInstance(notes, list)
        self.assertTrue(all(isinstance(n, dict) for n in notes))

        param_calls = bridge.calls_for("update_device")
        self.assertTrue(param_calls, "expected at least one update_device call")
        for call in param_calls:
            self.assertIn("params", call)
            self.assertIsInstance(call["params"], list)
            self.assertIn("name", call["params"][0])
            self.assertIn("value", call["params"][0])
            self.assertNotIn("parameter_name", call)

    def test_reese_missing_device_warns_instead_of_failing(self) -> None:
        # No "Drift" in read_track's devices -- every optional param step
        # should warn and be skipped, not abort the recipe.
        bridge = self._bridge_with_devices([])
        result = recipes_mod.apply_recipe("bass/reese", bridge=bridge)
        self.assertTrue(result["applied"], result.get("error"))
        self.assertTrue(result.get("warnings"))
        self.assertEqual(len(bridge.calls_for("update_device")), 0)

    def test_recipe_fails_when_a_step_reports_not_ok(self) -> None:
        # bass-glue's device.set_parameter steps are not optional, unlike
        # reese's Drift-substitution steps -- a real ok:false must still
        # fail the whole recipe.
        bridge = self._bridge_with_devices(
            ["Channel EQ", "Saturator", "Glue Compressor"],
            overrides={"update_device": {"ok": False, "error": "parameter not found"}},
        )
        result = recipes_mod.apply_recipe("mixing/bass-glue", bridge=bridge)
        self.assertFalse(result["applied"])
        self.assertIn("error", result)
        self.assertEqual(result["failed_step"], 2)  # first device.set_parameter step, 1-based

    def test_master_bus_targets_master_track_type(self) -> None:
        bridge = self._bridge_with_devices(["Glue Compressor", "EQ Eight", "Limiter"])
        result = recipes_mod.apply_recipe("mixing/master-bus", bridge=bridge)
        self.assertTrue(result["applied"], result.get("error"))
        for call in bridge.calls_for("create_device") + bridge.calls_for("update_device") + bridge.calls_for("read_track"):
            self.assertEqual(call.get("track_type"), "master")
            self.assertNotIn("track_index", call)

    def test_track_number_override_binds_zero_based_index(self) -> None:
        bridge = self._bridge_with_devices(["Channel EQ", "Saturator", "Glue Compressor"])
        result = recipes_mod.apply_recipe("mixing/bass-glue", overrides={"track_number": 3}, bridge=bridge)
        self.assertTrue(result["applied"], result.get("error"))
        create_calls = bridge.calls_for("create_device")
        self.assertTrue(create_calls)
        for call in create_calls:
            self.assertEqual(call.get("track_index"), 2)

    def test_track_index_override_rejected(self) -> None:
        bridge = self._bridge_with_devices(["Channel EQ", "Saturator", "Glue Compressor"])
        result = recipes_mod.apply_recipe("mixing/bass-glue", overrides={"track_index": 2}, bridge=bridge)
        self.assertFalse(result["applied"])
        self.assertIn("track_number", result["error"])

    def test_gated_recipe_fails_fast_with_no_bridge_calls(self) -> None:
        bridge = FakeBridge()
        result = recipes_mod.apply_recipe("drums/tech-house-kick", bridge=bridge)
        self.assertFalse(result["applied"])
        self.assertIn("companion", result["error"].lower())
        self.assertEqual(bridge.calls, [])


class MixCheckerTests(unittest.TestCase):
    """C4: analyze_mix_heuristics must read palReadSet's real nested shape."""

    def _set_with(self, master_devices, tracks) -> dict:
        return {
            "tracks": tracks,
            "master": {"devices": master_devices, "mixer": {"volume": 0.85}},
        }

    def test_detects_missing_limiter(self) -> None:
        report = mix_checker.analyze_mix_heuristics(self._set_with([], []))
        self.assertTrue(any("Limiter" in c for c in report["critical_issues"]))

    def test_limiter_present_clears_critical(self) -> None:
        report = mix_checker.analyze_mix_heuristics(self._set_with([{"name": "Limiter"}], []))
        self.assertFalse(any("Limiter" in c for c in report["critical_issues"]))

    def test_detects_hot_track_volume(self) -> None:
        tracks = [{
            "name": "Kick", "kind": "audio", "mute": False, "solo": False,
            "mixer": {"volume": 0.97, "pan": 0.0},
            "clip_slots": [{"index": 0, "has_clip": True}],
        }]
        report = mix_checker.analyze_mix_heuristics(self._set_with([{"name": "Limiter"}], tracks))
        self.assertTrue(any("hot" in w.lower() for w in report["warnings"]))

    def test_detects_off_center_bass(self) -> None:
        tracks = [{
            "name": "Sub Bass", "kind": "audio", "mute": False, "solo": False,
            "mixer": {"volume": 0.7, "pan": 0.5},
            "clip_slots": [{"index": 0, "has_clip": True}],
        }]
        report = mix_checker.analyze_mix_heuristics(self._set_with([{"name": "Limiter"}], tracks))
        self.assertTrue(any("panned off-center" in w for w in report["warnings"]))

    def test_detects_empty_unmuted_track_from_clip_slots(self) -> None:
        tracks = [{
            "name": "Lead", "kind": "midi", "mute": False, "solo": False,
            "mixer": {"volume": 0.6, "pan": 0.0},
            "clip_slots": [{"index": 0, "has_clip": False}, {"index": 1, "has_clip": False}],
        }]
        report = mix_checker.analyze_mix_heuristics(self._set_with([{"name": "Limiter"}], tracks))
        self.assertTrue(any("Lead" in r for r in report["recommendations"]))

    def test_healthy_set_has_no_issues(self) -> None:
        tracks = [{
            "name": "Kick", "kind": "audio", "mute": False, "solo": False,
            "mixer": {"volume": 0.7, "pan": 0.0},
            "clip_slots": [{"index": 0, "has_clip": True}],
        }]
        report = mix_checker.analyze_mix_heuristics(self._set_with([{"name": "Limiter"}], tracks))
        self.assertEqual(report["critical_issues"], [])
        self.assertEqual(report["warnings"], [])

    def test_analyze_mix_unwraps_set_envelope(self) -> None:
        # genius_client.py's live_analyze_mix handler must pass set_data["set"],
        # not the {ok, set} envelope itself, to analyze_mix_heuristics (C4).
        bridge = FakeBridge(overrides={
            "read_set": {"ok": True, "set": self._set_with([{"name": "Limiter"}], [])},
        })
        result = call_live_tool(bridge, "live_analyze_mix", {}, settings={})
        self.assertIn("Mix Health Audit", result)
        self.assertNotIn("Master track lacks a brickwall Limiter", result)


class SelectedAndSnapshotTests(unittest.TestCase):
    """M2/M3: these are LOM-shaped bugs that can only be fully proven live;
    this just confirms the Python side no longer chokes on the corrected
    JS field names it now expects (signature_numerator/denominator,
    tracks_truncated) and passes through pending/not_applied info."""

    def test_live_get_selected_formats_without_device_index_field_errors(self) -> None:
        bridge = FakeBridge(overrides={
            "get_selected": {"ok": True, "selected": {
                "track": {"index": 0, "name": "Kick", "kind": "audio"},
                "scene": {"index": 0, "name": "Scene 1"},
                "device": {"index": 2, "name": "EQ Eight", "class_name": "Eq8"},
                "clip": None,
            }},
        })
        result = call_live_tool(bridge, "live_get_selected", {}, settings={})
        self.assertIn("EQ Eight", result)

    def test_not_applied_is_surfaced_on_failure(self) -> None:
        bridge = FakeBridge(overrides={
            "set_punch": {"ok": False, "message": "Punch settings: unchanged", "not_applied": ["punch_in"]},
        })
        result = call_live_tool(bridge, "live_set_punch", {"punch_in": True}, settings={})
        self.assertIn("punch_in", result)

    def test_not_applied_is_surfaced_on_partial_success(self) -> None:
        # palUpdateClip keeps ok:true on a partial write so name/color/etc.
        # still land even when one LOM-VERIFY field fails; not_applied must
        # still reach the user rather than reading as a clean success.
        bridge = FakeBridge(overrides={
            "update_clip": {"ok": True, "message": "Updated clip at track 0, slot 0 (some fields not applied)", "not_applied": ["warp_mode"]},
        })
        result = call_live_tool(bridge, "live_update_clip", {"track_number": 1, "slot_number": 1, "warp_mode": "complex_pro"}, settings={})
        self.assertIn("Could not set", result)
        self.assertIn("warp_mode", result)


class TrackAddressingTests(unittest.TestCase):
    """v1.0.28 track-addressing fixes, relabeled for v1.0.32's 1-based
    numbering (S1.1): the read_set track summary must self-document Live's
    own 1-based numbering convention and include device names (root cause
    of the C1/H8 wrong-track bug), a {ok, message, X} response must not
    silently drop X, and track_name must reach the bridge payload
    unmodified for a tool routed through the generic dispatcher."""

    def test_track_summary_shows_live_track_labels_and_devices(self) -> None:
        bridge = FakeBridge(overrides={
            "read_set": {"ok": True, "set": {
                "name": "Test Set", "tempo": 120.0, "time_signature": "4/4", "is_playing": False,
                "track_count": 2,
                "tracks": [
                    {"index": 0, "name": "1-Safe House Kit", "kind": "midi",
                     "devices": [{"name": "Drum Rack"}], "clip_slots": []},
                    {"index": 2, "name": "3-Instrument Rack", "kind": "midi",
                     "devices": [{"name": "Instrument Rack"}, {"name": "Small Hall"}], "clip_slots": []},
                ],
            }},
        })
        result = call_live_tool(bridge, "live_read_set", {"include": ["tracks"]}, settings={})
        self.assertIn('Live track 1 "1-Safe House Kit"', result)
        self.assertIn('Live track 3 "3-Instrument Rack"', result)
        self.assertNotIn("track_index", result)
        self.assertIn("Drum Rack", result)
        self.assertIn("Instrument Rack", result)
        self.assertIn("Small Hall", result)

    def test_message_response_does_not_drop_extra_keys(self) -> None:
        bridge = FakeBridge(overrides={
            "create_device": {"ok": True, "message": "Native devices insert_device can add by name",
                               "devices": ["Drum Rack", "Instrument Rack", "Reverb"]},
        })
        result = call_live_tool(bridge, "live_create_device", {}, settings={})
        self.assertIn("Drum Rack", result)
        self.assertIn("Instrument Rack", result)
        self.assertIn("Reverb", result)

    def test_track_name_reaches_bridge_payload(self) -> None:
        bridge = FakeBridge()
        call_live_tool(bridge, "live_read_track", {"track_name": "Bass"}, settings={})
        calls = bridge.calls_for("read_track")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("track_name"), "Bass")

    def test_shaped_automation_forwards_track_name_not_a_hardcoded_index(self) -> None:
        bridge = FakeBridge(overrides={
            "read_clip": {"ok": True, "length": 4.0, "track_index": 2},
            "set_clip_automation": {"ok": True, "points_added": 8, "track_index": 2},
        })
        result = call_live_tool(bridge, "live_add_shaped_automation", {
            "track_name": "3-Instrument Rack", "slot_number": 1, "parameter_name": "Volume", "shape": "sine",
        }, settings={})
        read_calls = bridge.calls_for("read_clip")
        set_calls = bridge.calls_for("set_clip_automation")
        self.assertEqual(read_calls[0].get("track_name"), "3-Instrument Rack")
        self.assertNotIn("track_index", read_calls[0])
        self.assertEqual(set_calls[0].get("track_name"), "3-Instrument Rack")
        self.assertIn("track 3", result)


class GeniusDbTests(unittest.TestCase):
    """Bundled topics and their aliases must resolve, a user's own dataset
    folder must be discovered by name, and db_search must not render an empty
    citation body for datasets whose search.py returns "snippet" instead of
    "content"."""

    def test_bundled_topics_resolve(self) -> None:
        for key in ("ableton_god_producer", "mixology_db", "music_theory", "Ableton Racks Labeled"):
            self.assertIsNotNone(genius_db.resolve_topic(key), key)

    def test_every_bundled_topic_ships_with_its_database(self) -> None:
        for key, (folder, _desc) in genius_db.TOPICS.items():
            self.assertTrue((genius_db.DEFAULT_DB_ROOT / folder / "search.py").is_file(), key)
            self.assertTrue((genius_db.DEFAULT_DB_ROOT / folder / (folder + ".db")).is_file(), key)

    def test_a_users_own_dataset_folder_is_discovered(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "My Notes").mkdir()
            (root / "My Notes" / "search.py").write_text("# stub\n", encoding="utf-8")
            (root / "no_search_here").mkdir()
            self.assertEqual(genius_db.resolve_topic("my_notes", root), ("My Notes", "your own dataset"))
            self.assertIsNone(genius_db.resolve_topic("no_search_here", root))
            self.assertIn("my_notes", genius_db.list_topics(root))

    def test_db_search_falls_back_to_snippet_field(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "surge"
            folder.mkdir(parents=True)
            (folder / "search.py").write_text("# stub\n", encoding="utf-8")
            fake_result = [{
                "chunk_uid": "x", "doc_title": "9 User Manual", "category": "manual",
                "section_title": "Oscillators", "snippet": ">>> oscillator <<< generates a waveform",
                "rank": -0.1,
            }]
            with patch("genius_db.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = json.dumps(fake_result)
                mock_run.return_value.stderr = ""
                result = genius_db.db_search({"music_db_dir": str(root)}, "surge", "oscillator", limit=1)
        self.assertIn("generates a waveform", result)  # regression guard: this used to render as "" (empty body)


if __name__ == "__main__":
    unittest.main()
