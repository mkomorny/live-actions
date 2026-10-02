"""Genius's two host tools: live_tts_vocal and live_audio_op.

Both pipelines already existed (tts_vocal.py, audio_sample/) and are tested in their own
modules. What is new in v1.2.0 is that Genius can reach them, so these tests are about the
reaching: the spend guard, the capability gate, and the argument translation -- plus the
v1.1.0 lesson that a host tool must answer with `bridge=None`, since neither needs Live.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audio_sample  # noqa: E402
import genius_client  # noqa: E402
import tts_vocal  # noqa: E402
from genius_client import call_live_tool  # noqa: E402

PROFILE = {
    "name": "Lead Voice",
    "provider": "cartesia",
    "api_key": "sk_car_test",
    "voice_id": "lead-voice-id",
}
SETTINGS = {"tts_profiles": [PROFILE]}

PROFILE_B = {
    "name": "Narrator",
    "provider": "cartesia",
    "api_key": "sk_car_test_2",
    "voice_id": "narrator-voice-id",
}
SETTINGS_PINNED = {"tts_profiles": [PROFILE, PROFILE_B], "active_tts_profile": "Lead Voice"}


def _no_network():
    """Any provider call is a real charge -- these tests must never make one."""
    return mock.patch.object(
        tts_vocal.urllib.request, "urlopen",
        side_effect=AssertionError("a paid TTS request was made"),
    )


class CapabilityGateTests(unittest.TestCase):
    def test_tts_available_follows_the_saved_profiles(self) -> None:
        self.assertFalse(genius_client.tts_available({}))
        self.assertFalse(genius_client.tts_available({"tts_profiles": []}))
        self.assertTrue(genius_client.tts_available(SETTINGS))

    def test_no_profile_explains_where_to_add_one(self) -> None:
        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi"}, settings={})
        self.assertIn("No TTS profile", out)
        self.assertIn("TTS Vocal Profiles", out)

    def test_an_unknown_profile_name_is_an_error_not_a_substitution(self) -> None:
        # tts_vocal._pick_profile falls back to the first profile, which is right for a
        # dropdown and wrong for a model that can invent a name: generating in the wrong
        # voice and charging for it is worse than failing.
        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi", "profile": "Nope"}, settings=SETTINGS)
        self.assertIn("no TTS profile named", out)
        self.assertIn("Nope", out)
        self.assertIn("Lead Voice", out)


class PinnedProfileTests(unittest.TestCase):
    """Settings > TTS Vocal Profiles > pin a profile as the only voice used."""

    def test_a_pinned_profile_is_used_even_with_no_profile_named(self) -> None:
        with _no_network():
            seen: dict = {}

            def confirm(kind, detail):
                seen.update(detail)
                return False

            call_live_tool(None, "live_tts_vocal", {"text": "hi"}, settings=SETTINGS_PINNED, confirm=confirm)
        self.assertEqual(dict(seen["rows"])["Profile"], "Lead Voice")

    def test_requesting_a_different_profile_while_pinned_is_an_error_naming_the_pin(self) -> None:
        with _no_network():
            out = call_live_tool(
                None, "live_tts_vocal", {"text": "hi", "profile": "Narrator"}, settings=SETTINGS_PINNED
            )
        self.assertIn("ERROR", out)
        self.assertIn("Lead Voice", out)
        self.assertIn("pinned", out)

    def test_a_voice_override_is_ignored_and_the_dialog_shows_the_pinned_voice(self) -> None:
        seen: dict = {}

        def confirm(kind, detail):
            seen.update(detail)
            return False

        with _no_network():
            call_live_tool(
                None, "live_tts_vocal", {"text": "hi", "voice": "some-other-voice-id"},
                settings=SETTINGS_PINNED, confirm=confirm,
            )
        self.assertEqual(dict(seen["rows"])["Voice"], PROFILE["voice_id"])

    def test_a_stale_pin_is_a_clear_error(self) -> None:
        stale = {"tts_profiles": [PROFILE], "active_tts_profile": "Ghost"}
        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi"}, settings=stale)
        self.assertIn("ERROR", out)
        self.assertIn("Ghost", out)

    def test_the_system_prompt_states_a_pin_when_one_is_set(self) -> None:
        unpinned = genius_client.build_system_prompt(SETTINGS, "unknown", tts_online=True)
        self.assertNotIn("pinned", unpinned.lower())
        pinned = genius_client.build_system_prompt(SETTINGS_PINNED, "unknown", tts_online=True)
        self.assertIn("Lead Voice", pinned)
        self.assertIn("pinned", pinned.lower())


class SpendGuardTests(unittest.TestCase):
    def test_declining_generates_nothing(self) -> None:
        asked: list[tuple] = []

        def confirm(kind, detail):
            asked.append((kind, detail))
            return False

        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "Hello from the studio"},
                                 settings=SETTINGS, confirm=confirm)
        self.assertIn("declined", out)
        self.assertIn("Do not retry", out)
        self.assertEqual(len(asked), 1)

    def test_the_question_shows_what_is_being_approved(self) -> None:
        seen: dict = {}

        def confirm(kind, detail):
            seen.update(detail)
            seen["kind"] = kind
            return False

        with _no_network():
            call_live_tool(None, "live_tts_vocal",
                           {"text": "Hello from the studio", "speed": "1.2"},
                           settings=SETTINGS, confirm=confirm)
        self.assertEqual(seen["kind"], genius_client.CONFIRM_KINDS["live_tts_vocal"])
        rows = dict(seen["rows"])
        self.assertEqual(rows["Text"], "Hello from the studio")
        self.assertEqual(rows["Profile"], "Lead Voice")
        self.assertEqual(rows["Provider"], "cartesia")
        self.assertEqual(rows["Speed"], "1.2")
        self.assertIn("billed", seen["body"])

    def test_no_confirm_callback_denies(self) -> None:
        # A front-end that forgot to wire the dialog must not become a front-end that
        # spends silently.
        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi"}, settings=SETTINGS)
        self.assertIn("cannot ask the user to approve", out)

    def test_a_broken_dialog_denies_rather_than_killing_the_turn(self) -> None:
        def confirm(kind, detail):
            raise RuntimeError("window is gone")

        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi"},
                                 settings=SETTINGS, confirm=confirm)
        self.assertIn("could not ask the user", out)
        self.assertIn("window is gone", out)

    def test_empty_text_never_reaches_the_dialog(self) -> None:
        calls: list = []

        def confirm(kind, detail):
            calls.append(kind)
            return True

        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "   "},
                                 settings=SETTINGS, confirm=confirm)
        self.assertIn("ERROR", out)
        self.assertEqual(calls, [])

    def test_over_long_text_never_reaches_the_dialog(self) -> None:
        calls: list = []

        def confirm(kind, detail):
            calls.append(kind)
            return True

        with _no_network():
            out = call_live_tool(None, "live_tts_vocal",
                                 {"text": "x" * (tts_vocal.MAX_TEXT_CHARS + 1)},
                                 settings=SETTINGS, confirm=confirm)
        self.assertIn("limit is %d" % tts_vocal.MAX_TEXT_CHARS, out)
        self.assertEqual(calls, [])


class ApprovedGenerationTests(unittest.TestCase):
    """What an approved call reports back. tts_vocal.run is stubbed -- its own pipeline is
    covered by test_tts_vocal; what matters here is what Genius is told afterwards."""

    def _run(self, result: dict, args: dict | None = None) -> str:
        with mock.patch.object(tts_vocal, "run", return_value=result) as run:
            out = call_live_tool(None, "live_tts_vocal", args or {"text": "Hello from the studio"},
                                 settings=SETTINGS, confirm=lambda k, d: True)
        self.fields = run.call_args[0][0]
        return out

    def test_reports_path_and_the_real_duration(self) -> None:
        out = self._run({"ok": True, "message": "Generated.", "path": r"C:\x\TTS-Sample-4.wav",
                         "durationSec": 2.37, "cacheHit": False, "provider": "cartesia", "voice": "v1"})
        self.assertIn(r"C:\x\TTS-Sample-4.wav", out)
        self.assertIn("2.37 s", out)
        self.assertIn("new generation", out)

    def test_says_it_is_speech_not_singing(self) -> None:
        out = self._run({"ok": True, "message": "Generated.", "path": "x.wav", "durationSec": 3.0,
                         "cacheHit": False, "provider": "cartesia", "voice": "v1"})
        self.assertIn("SPEECH, not singing", out)
        self.assertIn("trim", out)

    def test_points_at_both_routes_into_live(self) -> None:
        out = self._run({"ok": True, "message": "Generated.", "path": "x.wav", "durationSec": 3.0,
                         "cacheHit": False, "provider": "cartesia", "voice": "v1"})
        self.assertIn("live_update_device", out)
        self.assertIn("live_create_clip", out)

    def test_a_missing_duration_is_admitted_not_invented(self) -> None:
        out = self._run({"ok": True, "message": "Generated.", "path": "x.wav", "durationSec": None,
                         "cacheHit": True, "provider": "cartesia", "voice": "v1"})
        self.assertIn("unknown", out)
        self.assertIn("from cache", out)

    def test_overrides_are_forwarded_to_the_pipeline(self) -> None:
        self._run(
            {"ok": True, "message": "Generated.", "path": "x.wav", "durationSec": 1.0,
             "cacheHit": False, "provider": "cartesia", "voice": "v2"},
            {"text": "hey", "voice": "v2", "speed": "0.8", "language": "en"},
        )
        self.assertEqual(self.fields["voice"], "v2")
        self.assertEqual(self.fields["speed"], "0.8")
        self.assertEqual(self.fields["language"], "en")
        self.assertEqual(self.fields["profile"], "Lead Voice")

    def test_a_failure_is_reported_as_a_failure(self) -> None:
        out = self._run({"ok": False, "message": "Cartesia TTS 401: bad key"})
        self.assertIn("TTS generation failed", out)
        self.assertIn("401", out)


class AudioOpDiscoveryTests(unittest.TestCase):
    def test_no_operation_lists_every_op_with_its_fields(self) -> None:
        out = call_live_tool(None, "live_audio_op", {}, settings={})
        for op in audio_sample.describe_ops():
            self.assertIn(op["id"], out)
        self.assertIn("start=", out)          # trim's own field names, not invented ones
        self.assertIn("semitones=", out)
        self.assertIn("needs no input_file", out)

    def test_describe_ops_matches_the_registry(self) -> None:
        from audio_sample.ops import registry
        described = {o["id"] for o in audio_sample.describe_ops()}
        self.assertEqual(described, set(registry.OPS_BY_ID))


class AudioOpDispatchTests(unittest.TestCase):
    def test_params_are_namespaced_for_the_shared_runner(self) -> None:
        # The Tool screen submits `trim__start`; Genius sends {"start": "0"}. One code path
        # serves both, so the translation has to be exact or the op silently uses defaults.
        with mock.patch.object(audio_sample, "run",
                               return_value={"ok": True, "message": "Trimmed.", "path": "out.wav"}) as run:
            call_live_tool(None, "live_audio_op",
                           {"operation": "trim", "input_file": "in.wav", "params": {"start": "0", "end": "10"}},
                           settings={})
        fields = run.call_args[0][0]
        self.assertEqual(fields["operation"], "trim")
        self.assertEqual(fields["input_file"], "in.wav")
        self.assertEqual(fields["trim__start"], "0")
        self.assertEqual(fields["trim__end"], "10")

    def test_a_hyphenated_op_id_is_namespaced_with_an_underscore(self) -> None:
        with mock.patch.object(audio_sample, "run",
                               return_value={"ok": True, "message": "Shifted.", "path": "out.wav"}) as run:
            call_live_tool(None, "live_audio_op",
                           {"operation": "pitch-time", "input_file": "in.wav", "params": {"semitones": "-3"}},
                           settings={})
        self.assertEqual(run.call_args[0][0]["pitch_time__semitones"], "-3")

    def test_an_unknown_operation_lists_the_real_ones(self) -> None:
        out = call_live_tool(None, "live_audio_op", {"operation": "reverb", "input_file": "x.wav"}, settings={})
        self.assertIn("Unknown operation", out)
        self.assertIn("bitcrush", out)

    def test_params_must_be_an_object(self) -> None:
        out = call_live_tool(None, "live_audio_op",
                             {"operation": "trim", "input_file": "x.wav", "params": "start=0"}, settings={})
        self.assertIn("must be an object", out)

    def test_a_missing_input_file_is_reported(self) -> None:
        out = call_live_tool(None, "live_audio_op", {"operation": "trim"}, settings={})
        self.assertIn("input", out.lower())


class BridgeIndependenceTests(unittest.TestCase):
    """Both tools run on the host. Falling through to the OSC bridge would turn a perfectly
    good local result into "Live Actions Bridge is not connected" whenever the Max device is
    off a track -- the exact bug live_library had in v1.1.0."""

    def test_tts_answers_with_no_bridge(self) -> None:
        with _no_network():
            out = call_live_tool(None, "live_tts_vocal", {"text": "hi"}, settings=SETTINGS)
        self.assertNotIn("Bridge", out)

    def test_audio_op_answers_with_no_bridge(self) -> None:
        out = call_live_tool(None, "live_audio_op", {}, settings={})
        self.assertNotIn("Bridge", out)
        self.assertIn("audio operations", out)


class ToolSchemaTests(unittest.TestCase):
    def test_both_tools_are_registered(self) -> None:
        names = {t["name"] for t in genius_client.LIVE_TOOLS}
        self.assertIn("live_tts_vocal", names)
        self.assertIn("live_audio_op", names)

    def test_the_tts_description_refuses_to_promise_singing(self) -> None:
        desc = next(t for t in genius_client.LIVE_TOOLS if t["name"] == "live_tts_vocal")["description"]
        self.assertIn("do not sing", desc)
        self.assertIn("durationSec", desc)

    def test_the_device_tools_document_the_sample_param(self) -> None:
        by_name = {t["name"]: t["description"] for t in genius_client.LIVE_TOOLS}
        self.assertIn("sample", by_name["live_update_device"])
        self.assertIn("Simpler only", by_name["live_update_device"])
        self.assertIn("sample", by_name["live_create_device"])


if __name__ == "__main__":
    unittest.main()
