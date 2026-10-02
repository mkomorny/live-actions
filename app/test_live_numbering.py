"""Tests for live_numbering.py -- 1-based model args <-> 0-based bridge args."""

from __future__ import annotations

import unittest

from live_numbering import (
    ModelArgError,
    args_from_model,
    live_track_label,
    model_view,
    mv_json,
    parse_live_number,
)


class ParseLiveNumberTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_live_number("track_number", 1), 0)
        self.assertEqual(parse_live_number("track_number", 9), 8)

    def test_rejects_zero(self):
        with self.assertRaises(ModelArgError):
            parse_live_number("track_number", 0)

    def test_rejects_negative(self):
        with self.assertRaises(ModelArgError):
            parse_live_number("track_number", -1)

    def test_rejects_bool(self):
        with self.assertRaises(ModelArgError):
            parse_live_number("track_number", True)

    def test_rejects_non_integer(self):
        with self.assertRaises(ModelArgError):
            parse_live_number("track_number", "1")
        with self.assertRaises(ModelArgError):
            parse_live_number("track_number", 1.5)

    def test_maximum(self):
        with self.assertRaises(ModelArgError):
            parse_live_number("scene_number", 5, maximum=4)
        self.assertEqual(parse_live_number("scene_number", 4, maximum=4), 3)


class ArgsFromModelRoundTripTests(unittest.TestCase):
    def test_track_number_round_trip(self):
        out = args_from_model("live_read_track", {"track_number": 3})
        self.assertEqual(out, {"track_index": 2})

    def test_multiple_families(self):
        out = args_from_model(
            "live_read_clip",
            {"track_number": 1, "slot_number": 4, "device_number": 2},
        )
        self.assertEqual(out, {"track_index": 0, "slot_index": 3, "device_index": 1})

    def test_to_slot_number(self):
        out = args_from_model("live_edit_clip", {"track_number": 1, "slot_number": 1, "to_slot_number": 5})
        self.assertEqual(out["to_slot"], 4)
        self.assertNotIn("to_slot_number", out)

    def test_return_letter(self):
        out = args_from_model("live_read_track", {"return_letter": "C"})
        self.assertEqual(out["return_index"], 2)

    def test_track_name_passthrough(self):
        out = args_from_model("live_read_track", {"track_name": "Bass"})
        self.assertEqual(out, {"track_name": "Bass"})

    def test_none_values_dropped(self):
        out = args_from_model("live_read_track", {"track_number": 1, "include": None})
        self.assertEqual(out, {"track_index": 0})

    def test_non_numbered_keys_pass_through(self):
        out = args_from_model("live_update_track", {"track_number": 1, "name": "Kick", "mute": True})
        self.assertEqual(out, {"track_index": 0, "name": "Kick", "mute": True})


class StrayKeyRejectionTests(unittest.TestCase):
    def test_rejects_track_index(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_read_track", {"track_index": 2})

    def test_rejects_bare_index(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_create_track", {"index": 2})

    def test_rejects_bare_slot(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_select", {"slot": "0/3"})

    def test_rejects_ids(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_update_scene", {"ids": "0,1"})

    def test_rejects_to_slot(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_edit_clip", {"to_slot": 2})

    def test_live_api_skips_all_checks(self):
        out = args_from_model("live_api", {"path": "live_set tracks 0", "property": "name"})
        self.assertEqual(out, {"path": "live_set tracks 0", "property": "name"})


class DevicePathTests(unittest.TestCase):
    def test_converts_track_device_chain(self):
        out = args_from_model("live_update_macro", {"path": "t3/d1/c2"})
        self.assertEqual(out["path"], "t2/d0/c1")

    def test_pad_note_untouched(self):
        out = args_from_model("live_select", {"device_path": "t1/d1/pC1"})
        self.assertEqual(out["device_path"], "t0/d0/pC1")

    def test_master_untouched(self):
        out = args_from_model("live_select", {"device_path": "master/d1"})
        self.assertEqual(out["device_path"], "master/d0")

    def test_rejects_zero_segment(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_update_macro", {"path": "t0/d1"})


class SpecialCaseTests(unittest.TestCase):
    def test_update_macro_no_shift(self):
        out = args_from_model("live_update_macro", {"track_number": 1, "macro_number": 1})
        self.assertEqual(out["macro"], "1")
        self.assertNotIn("macro_index", out)

    def test_map_rack_magnitude_shifts(self):
        out = args_from_model("live_map_rack_magnitude", {"track_number": 1, "macro_number": 1})
        self.assertEqual(out["macro_index"], 0)

    def test_create_track_position(self):
        out = args_from_model("live_create_track", {"type": "midi", "position_number": 1})
        self.assertEqual(out["index"], 0)

    def test_update_scene_scene_numbers(self):
        out = args_from_model("live_update_scene", {"scene_numbers": [1, 3], "name": "Verse"})
        self.assertEqual(out["ids"], "0,2")

    def test_update_scene_rejects_empty_list(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_update_scene", {"scene_numbers": []})

    def test_detect_key_track_numbers(self):
        out = args_from_model("live_detect_key", {"scope": "track", "track_numbers": [1, 3]})
        self.assertEqual(out["track_index"], "0,2")

    def test_select_track_and_slot(self):
        out = args_from_model("live_select", {"track_number": 1, "slot_number": 4})
        self.assertEqual(out["slot"], "0/3")

    def test_run_action_tracks(self):
        out = args_from_model(
            "live_run_action",
            {"tool_id": "clip-namer", "payload": {"tracks": [{"track_number": 2, "kind": "midi"}]}},
        )
        self.assertEqual(out["payload"]["tracks"], [{"path": "live_set tracks 1", "kind": "midi"}])

    def test_run_action_preserves_fields(self):
        out = args_from_model(
            "live_run_action",
            {"tool_id": "clip-namer", "payload": {"tracks": [{"track_number": 1, "kind": "midi"}], "fields": {"pattern": "x"}}},
        )
        self.assertEqual(out["payload"]["fields"], {"pattern": "x"})

    def test_run_action_return_and_master(self):
        out = args_from_model(
            "live_run_action",
            {
                "tool_id": "x",
                "payload": {"tracks": [
                    {"track_number": 1, "kind": "return"},
                    {"track_number": 1, "kind": "master"},
                ]},
            },
        )
        self.assertEqual(out["payload"]["tracks"][0]["path"], "live_set return_tracks 0")
        self.assertEqual(out["payload"]["tracks"][1]["path"], "live_set master_track")

    def test_run_action_missing_track_number(self):
        with self.assertRaises(ModelArgError):
            args_from_model("live_run_action", {"tool_id": "x", "payload": {"tracks": [{"kind": "midi"}]}})


class ModelViewTests(unittest.TestCase):
    def test_simple_index_shift(self):
        self.assertEqual(model_view({"track_index": 2}), {"track_number": 3})

    def test_negative_one_becomes_none(self):
        self.assertEqual(model_view({"device_index": -1}), {"device_number": None})

    def test_none_stays_none(self):
        self.assertEqual(model_view({"device_index": None}), {"device_number": None})

    def test_color_index_and_note_untouched(self):
        out = model_view({"color_index": 5, "note": 60})
        self.assertEqual(out, {"color_index": 5, "note": 60})

    def test_return_index_becomes_letter(self):
        self.assertEqual(model_view({"return_index": 2}), {"return_letter": "C"})

    def test_path_dropped(self):
        out = model_view({"path": "live_set tracks 0 clip_slots 1 clip", "name": "Foo"})
        self.assertEqual(out, {"name": "Foo"})

    def test_macros_index_kept(self):
        out = model_view({"macros": [{"index": 0, "name": "Magnitude"}]})
        self.assertEqual(out, {"macros": [{"index": 0, "name": "Magnitude"}]})

    def test_sends_index_dropped(self):
        out = model_view({"sends": [{"index": 0, "name": "A", "value": 0.5}]})
        self.assertEqual(out, {"sends": [{"name": "A", "value": 0.5}]})

    def test_locators_index_dropped(self):
        out = model_view({"locators": [{"index": 0, "name": "Verse"}]})
        self.assertEqual(out, {"locators": [{"name": "Verse"}]})

    def test_drum_pads_index_dropped(self):
        out = model_view({"drum_pads": [{"index": 0, "note": 60}]})
        self.assertEqual(out, {"drum_pads": [{"note": 60}]})

    def test_nested_read_set_snapshot(self):
        snapshot = {
            "ok": True,
            "tracks": [
                {"index": 0, "name": "Kick", "path": "live_set tracks 0", "color_index": 3},
                {"index": 1, "name": "Bass", "clips": [{"slot": 0, "name": "Loop"}]},
            ],
            "scenes": [{"index": 0, "name": "Intro"}],
        }
        out = model_view(snapshot)
        self.assertEqual(out["tracks"][0]["number"], 1)
        self.assertEqual(out["tracks"][0]["color_index"], 3)
        self.assertNotIn("path", out["tracks"][0])
        self.assertEqual(out["tracks"][1]["clips"][0]["slot_number"], 1)
        self.assertEqual(out["scenes"][0]["number"], 1)

    def test_soloed_track_nonstandard_key(self):
        out = model_view({"soloed_track": 2})
        self.assertEqual(out, {"soloed_track_number": 3})

    def test_does_not_mutate_input(self):
        original = {"track_index": 0}
        model_view(original)
        self.assertEqual(original, {"track_index": 0})


class MvJsonTests(unittest.TestCase):
    def test_produces_valid_json(self):
        import json

        text = mv_json({"track_index": 0, "name": "Kick"})
        parsed = json.loads(text)
        self.assertEqual(parsed, {"track_number": 1, "name": "Kick"})


class LiveTrackLabelTests(unittest.TestCase):
    def test_regular_track(self):
        self.assertEqual(live_track_label({"index": 2, "name": "Bass", "kind": ""}), 'Live track 3 "Bass"')

    def test_return_track(self):
        self.assertEqual(live_track_label({"index": 0, "name": "Reverb", "kind": "return"}), 'return A "Reverb"')

    def test_master(self):
        self.assertEqual(live_track_label({"kind": "master"}), "Master")

    def test_no_name(self):
        self.assertEqual(live_track_label({"index": 0, "kind": ""}), "Live track 1")


if __name__ == "__main__":
    unittest.main()
