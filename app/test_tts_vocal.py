"""tts_vocal: the Cartesia request contract, profile/override handling, and the real profile -> WAV pipeline.

The Cartesia part pins exactly what Cartesia's live documentation for POST /tts/bytes asked for when it was
checked (2026-09-20): `Cartesia-Version: 2026-08-14`, `model_id`, `transcript`, `voice` (string id),
`output_format` = wav / pcm_f32le / 48000, optional `language`, `generation_config.speed` in [0.6, 1.5].
No test here touches the network: urllib's `urlopen` is replaced. The pipeline tests run the real ffmpeg
(found on PATH) on a synthesized float WAV and are skipped if ffmpeg is missing.
"""

from __future__ import annotations

import io
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import wave
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_vocal  # noqa: E402

KEY = "sk_car_unit-test-key-0123456789"
FFMPEG = shutil.which("ffmpeg")


def float_wav(seconds: float = 0.5, rate: int = 48000) -> bytes:
    """What Cartesia returns for wav + pcm_f32le: a WAVE_FORMAT_IEEE_FLOAT (3) mono file."""
    n = int(seconds * rate)
    data = b"".join(struct.pack("<f", 0.3 * math.sin(2 * math.pi * 220 * i / rate)) for i in range(n))
    fmt = struct.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(data)) + data
    return b"RIFF" + struct.pack("<I", len(body)) + body


class FakeResponse:
    def __init__(self, payload: bytes = b"AUDIO", status: int = 200) -> None:
        self._payload, self.status = payload, status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc) -> None:
        return None


def profile(**over) -> dict:
    p = {"name": "Cartesia", "provider": "cartesia", "api_key": KEY, "voice_id": "voice-uuid-1", "settings": {}}
    p.update(over)
    return p


def call(prof: dict, text: str = "Hello there", payload: bytes = b"AUDIO"):
    """Run _cartesia_speech with urlopen faked; return (bytes, the Request it was given, its parsed JSON body)."""
    seen: list = []

    def fake(req, timeout=None):
        seen.append((req, timeout))
        return FakeResponse(payload)

    with mock.patch.object(tts_vocal.urllib.request, "urlopen", fake):
        out = tts_vocal._cartesia_speech(prof, text)
    req, timeout = seen[0]
    return out, req, json.loads(req.data.decode("utf-8")), timeout


class CartesiaRequestTests(unittest.TestCase):
    def test_url_method_and_headers(self):
        _, req, _, timeout = call(profile())
        self.assertEqual(req.full_url, "https://api.cartesia.ai/tts/bytes")
        self.assertEqual(req.get_method(), "POST")
        h = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(h["authorization"], "Bearer " + KEY)
        self.assertEqual(h["cartesia-version"], "2026-08-14")
        self.assertEqual(h["content-type"], "application/json")
        self.assertEqual(timeout, 120)

    def test_body_is_exactly_the_documented_minimum(self):
        _, _, body, _ = call(profile(), "Hello there")
        self.assertEqual(body, {
            "model_id": "sonic-3.6",
            "transcript": "Hello there",
            "voice": "voice-uuid-1",
            "output_format": {"container": "wav", "encoding": "pcm_f32le", "sample_rate": 48000},
        })

    def test_the_key_is_only_in_the_authorization_header(self):
        _, req, _, _ = call(profile())
        self.assertNotIn(KEY.encode(), req.data)
        self.assertNotIn(KEY, req.full_url)

    def test_returns_the_response_bytes_unchanged(self):
        out, _, _, _ = call(profile(), payload=b"\x00\x01RIFF")
        self.assertEqual(out, b"\x00\x01RIFF")

    def test_model_comes_from_the_profile(self):
        _, _, body, _ = call(profile(model="sonic-3.5"))
        self.assertEqual(body["model_id"], "sonic-3.5")

    def test_the_default_model_is_a_documented_one(self):
        self.assertIn(tts_vocal._CARTESIA_DEFAULT_MODEL, {"sonic-3.6", "sonic-3.5", "sonic-3", "sonic-latest"})
        self.assertEqual(tts_vocal._CARTESIA_VERSION, "2026-08-14")

    def test_language_auto_and_blank_are_left_out(self):
        for value in ("auto", "AUTO", "", "  ", None):
            with self.subTest(language=value):
                _, _, body, _ = call(profile(settings={"language": value}))
                self.assertNotIn("language", body)

    def test_a_real_language_is_sent(self):
        _, _, body, _ = call(profile(settings={"language": "en-GB"}))
        self.assertEqual(body["language"], "en-GB")

    def test_speed_goes_in_generation_config(self):
        _, _, body, _ = call(profile(settings={"speed": 1.2}))
        self.assertEqual(body["generation_config"], {"speed": 1.2})

    def test_speed_boundaries_are_accepted(self):
        for value in (0.6, 1.5, "0.6", "1.5"):
            with self.subTest(speed=value):
                _, _, body, _ = call(profile(settings={"speed": value}))
                self.assertEqual(body["generation_config"], {"speed": float(value)})

    def test_speed_outside_the_documented_range_is_refused_locally(self):
        for value in (0.59, 1.51, 4.0, 0.25):
            with self.subTest(speed=value), mock.patch.object(tts_vocal.urllib.request, "urlopen") as net:
                with self.assertRaises(tts_vocal.TtsError) as ctx:
                    tts_vocal._cartesia_speech(profile(settings={"speed": value}), "hi")
                self.assertIn("between 0.6 and 1.5", str(ctx.exception))
                net.assert_not_called()

    def test_a_non_numeric_speed_is_refused(self):
        with self.assertRaises(tts_vocal.TtsError) as ctx:
            tts_vocal._cartesia_speech(profile(settings={"speed": "fast"}), "hi")
        self.assertIn("not a number", str(ctx.exception))

    def test_no_speed_means_no_generation_config(self):
        _, _, body, _ = call(profile(settings={}))
        self.assertNotIn("generation_config", body)

    def test_missing_key_and_missing_voice_fail_before_any_request(self):
        with mock.patch.object(tts_vocal.urllib.request, "urlopen") as net:
            with self.assertRaises(tts_vocal.TtsError) as k:
                tts_vocal._cartesia_speech(profile(api_key="  "), "hi")
            self.assertIn("no API key", str(k.exception))
            with self.assertRaises(tts_vocal.TtsError) as v:
                tts_vocal._cartesia_speech(profile(voice_id=""), "hi")
            self.assertIn("no Cartesia voice ID", str(v.exception))
            net.assert_not_called()

    def test_http_error_becomes_a_readable_message_with_the_status(self):
        err = urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(b'{"error":"bad key"}'))
        with mock.patch.object(tts_vocal.urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(tts_vocal.TtsError) as ctx:
                tts_vocal._cartesia_speech(profile(), "hi")
        self.assertEqual(str(ctx.exception), 'Cartesia TTS 401: {"error":"bad key"}')

    def test_a_long_error_body_is_cut_to_400_characters(self):
        err = urllib.error.HTTPError("u", 500, "x", {}, io.BytesIO(b"e" * 5000))
        with mock.patch.object(tts_vocal.urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(tts_vocal.TtsError) as ctx:
                tts_vocal._cartesia_speech(profile(), "hi")
        self.assertEqual(len(str(ctx.exception)), len("Cartesia TTS 500: ") + 400)

    def test_unreachable_network_is_reported_without_the_key(self):
        with mock.patch.object(tts_vocal.urllib.request, "urlopen", side_effect=urllib.error.URLError("getaddrinfo failed")):
            with self.assertRaises(tts_vocal.TtsError) as ctx:
                tts_vocal._cartesia_speech(profile(), "hi")
        self.assertIn("Could not reach Cartesia", str(ctx.exception))
        self.assertNotIn(KEY, str(ctx.exception))


class ProviderDetectionTests(unittest.TestCase):
    def test_a_cartesia_key_is_tried_on_cartesia_first(self):
        order: list[str] = []

        def probe(name, status):
            def f(key):
                order.append(name)
                return status, b""
            return f

        probes = {n: probe(n, 200 if n == "cartesia" else 401) for n in ("xai", "openai", "elevenlabs", "cartesia")}
        with mock.patch.dict(tts_vocal._PROVIDER_PROBES, probes):
            self.assertEqual(tts_vocal.detect_provider(KEY), ("cartesia", "Detected cartesia."))
        self.assertEqual(order, ["cartesia"])

    def test_cartesia_probe_sends_the_version_header(self):
        seen = {}

        def fake_probe(url, headers):
            seen.update(url=url, headers=headers)
            return 200, b"{}"

        with mock.patch.object(tts_vocal, "_probe", fake_probe):
            tts_vocal._PROVIDER_PROBES["cartesia"](KEY)
        self.assertTrue(seen["url"].startswith("https://api.cartesia.ai/voices"))
        self.assertEqual(seen["headers"]["Cartesia-Version"], "2026-08-14")

    def test_cloned_voices_are_starred_first_and_not_duplicated(self):
        owned = {"data": [{"id": "mine", "name": "My Clone"}]}
        everyone = {"data": [{"id": "mine", "name": "My Clone"}, {"id": "stock", "name": "Stock"}, {"id": "", "name": "no id"}]}
        replies = {"is_owner=true": owned, "limit=100": everyone}

        def fake_probe(url, headers):
            return 200, json.dumps(replies["is_owner=true" if "is_owner=true" in url else "limit=100"]).encode()

        with mock.patch.object(tts_vocal, "_probe", fake_probe):
            voices = tts_vocal.list_voices("cartesia", KEY)
        self.assertEqual(voices, [
            {"voice_id": "mine", "name": "My Clone", "custom": True},
            {"voice_id": "stock", "name": "Stock", "custom": False},
        ])


class RunValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="la-tts-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.settings = {"tts_profiles": [profile()], "tts_output_dir": str(self.tmp)}

    def test_empty_and_oversized_text(self):
        self.assertFalse(tts_vocal.run({"text": "  "}, self.settings)["ok"])
        r = tts_vocal.run({"text": "x" * 2001}, self.settings)
        self.assertFalse(r["ok"])
        self.assertIn("limit is 2000", r["message"])

    def test_no_profile_and_unknown_provider(self):
        self.assertIn("No TTS profiles", tts_vocal.run({"text": "hi"}, {"tts_profiles": []})["message"])
        bad = {"tts_profiles": [profile(provider="nope")], "tts_output_dir": str(self.tmp)}
        self.assertIn('Unknown provider "nope"', tts_vocal.run({"text": "hi"}, bad)["message"])

    def test_a_bad_speed_override_is_reported_not_raised(self):
        r = tts_vocal.run({"text": "hi", "speed": "quick"}, self.settings)
        self.assertEqual((r["ok"], r["message"]), (False, 'Speed "quick" is not a number.'))

    def test_profile_is_picked_by_name_else_the_first(self):
        a, b = profile(name="A"), profile(name="B", voice_id="v-b")
        st = {"tts_profiles": [a, b]}
        self.assertEqual(tts_vocal._pick_profile({"profile": "B"}, st)["voice_id"], "v-b")
        self.assertEqual(tts_vocal._pick_profile({"profile": "missing"}, st)["name"], "A")
        self.assertEqual(tts_vocal._pick_profile({}, st)["name"], "A")

    def test_a_pinned_profile_overrides_any_requested_name(self):
        a, b = profile(name="A"), profile(name="B", voice_id="v-b")
        st = {"tts_profiles": [a, b], "active_tts_profile": "B"}
        self.assertEqual(tts_vocal._pick_profile({}, st)["name"], "B")
        self.assertEqual(tts_vocal._pick_profile({"profile": "A"}, st)["name"], "B")

    def test_a_stale_pin_refuses_rather_than_falling_back(self):
        st = {"tts_profiles": [profile(name="A")], "active_tts_profile": "Ghost"}
        self.assertIsNone(tts_vocal._pick_profile({}, st))

    def test_pinning_drops_a_voice_override_but_not_speed_or_language(self):
        prof = profile(voice_id="pinned-voice")
        eff, gen = tts_vocal._apply_overrides(
            prof, {"voice": "other-voice", "speed": "1.3", "language": "fr"}, voice_locked=True
        )
        self.assertEqual(eff["voice_id"], "pinned-voice")
        self.assertEqual(gen, {"speed": 1.3, "language": "fr"})

    def test_run_reports_the_pinned_voice_even_when_a_different_one_is_requested(self):
        st = {
            "tts_profiles": [profile(name="A", voice_id="v-a"), profile(name="B", voice_id="v-b")],
            "active_tts_profile": "A",
            "tts_output_dir": str(self.tmp),
        }
        with mock.patch.object(tts_vocal, "_PROVIDERS", {"cartesia": lambda prof, text: b"AUDIO"}), \
                mock.patch.object(tts_vocal, "_normalize_to_wav", lambda raw, ffmpeg, out: out.write_bytes(b"RIFF")), \
                mock.patch.object(tts_vocal, "_probe_duration", return_value=0.1), \
                mock.patch.object(tts_vocal, "_resolve_ffmpeg", return_value="ffmpeg"):
            r = tts_vocal.run({"text": "hi", "profile": "B", "voice": "v-b"}, st)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["voice"], "v-a")

    def test_overrides_reach_the_cartesia_request_and_change_the_cache_key(self):
        prof = profile(settings={"speed": 1.0})
        eff, gen = tts_vocal._apply_overrides(prof, {"voice": "other-voice", "speed": "1.3", "language": "fr"})
        self.assertEqual((eff["voice_id"], gen), ("other-voice", {"speed": 1.3, "language": "fr"}))
        _, _, body, _ = call(eff)
        self.assertEqual((body["voice"], body["language"], body["generation_config"]), ("other-voice", "fr", {"speed": 1.3}))
        plain = tts_vocal._cache_key("cartesia", "voice-uuid-1", "hi", {"speed": 1.0})
        over = tts_vocal._cache_key("cartesia", "other-voice", "hi", gen)
        self.assertNotEqual(plain, over)
        self.assertEqual(plain, tts_vocal._cache_key("cartesia", "voice-uuid-1", "hi", {"speed": 1.0}))

    def test_a_provider_failure_is_a_result_not_an_exception(self):
        st = dict(self.settings, ffmpeg_path=FFMPEG or "ffmpeg")
        with mock.patch.object(tts_vocal.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")), \
                mock.patch.object(tts_vocal, "_resolve_ffmpeg", return_value=st["ffmpeg_path"]):
            r = tts_vocal.run({"text": "hi"}, st)
        self.assertFalse(r["ok"])
        self.assertIn("Could not reach Cartesia", r["message"])
        self.assertEqual(list(self.tmp.glob("TTS-Sample-*.wav")), [])

    def test_missing_ffmpeg_is_reported(self):
        with mock.patch.object(tts_vocal.shutil, "which", return_value=None):
            r = tts_vocal.run({"text": "hi"}, self.settings)
        self.assertEqual((r["ok"], r["message"]), (False, "ffmpeg not found. Set ffmpeg_path in Settings."))


@unittest.skipUnless(FFMPEG, "ffmpeg is not on PATH")
class CartesiaPipelineTests(unittest.TestCase):
    """profile -> (faked) Cartesia -> the REAL ffmpeg -> a WAV on disk, through run()."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="la-tts-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.settings = {"tts_profiles": [profile()], "tts_output_dir": str(self.tmp), "ffmpeg_path": FFMPEG}
        self.requests: list = []

        def fake(req, timeout=None):
            self.requests.append(req)
            return FakeResponse(float_wav(0.5))

        p = mock.patch.object(tts_vocal.urllib.request, "urlopen", fake)
        p.start()
        self.addCleanup(p.stop)

    def test_generates_a_real_wav(self):
        r = tts_vocal.run({"text": "Hello there"}, self.settings)
        self.assertTrue(r["ok"], r)
        self.assertEqual((r["message"], r["cacheHit"], r["provider"], r["voice"]), ("Generated.", False, "cartesia", "voice-uuid-1"))
        path = Path(r["path"])
        self.assertEqual(path.name, "TTS-Sample-1.wav")
        with wave.open(str(path), "rb") as w:
            self.assertEqual((w.getnchannels(), w.getframerate(), w.getsampwidth()), (1, 48000, 3))
            self.assertAlmostEqual(w.getnframes() / w.getframerate(), 0.5, delta=0.02)
        self.assertAlmostEqual(r["durationSec"], 0.5, delta=0.02)
        self.assertEqual(len(self.requests), 1)

    def test_the_second_identical_run_is_a_cache_hit_with_no_second_request(self):
        first = tts_vocal.run({"text": "Hello there"}, self.settings)
        second = tts_vocal.run({"text": "Hello there"}, self.settings)
        self.assertEqual((second["ok"], second["cacheHit"], second["message"]), (True, True, "Using cached generation."))
        self.assertEqual((Path(first["path"]).name, Path(second["path"]).name), ("TTS-Sample-1.wav", "TTS-Sample-2.wav"))
        self.assertEqual(len(self.requests), 1)

    def test_a_different_speed_is_a_new_generation(self):
        tts_vocal.run({"text": "Hello there"}, self.settings)
        r = tts_vocal.run({"text": "Hello there", "speed": "1.25"}, self.settings)
        self.assertFalse(r["cacheHit"])
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(json.loads(self.requests[1].data)["generation_config"], {"speed": 1.25})

    def test_no_partial_files_are_left_behind(self):
        tts_vocal.run({"text": "Hello there"}, self.settings)
        leftovers = [p.name for p in self.tmp.rglob("*") if p.suffix in (".src", ".tmp")]
        self.assertEqual(leftovers, [])

    def test_ffmpeg_rejecting_the_audio_is_a_result_not_a_crash(self):
        with mock.patch.object(tts_vocal.urllib.request, "urlopen", lambda req, timeout=None: FakeResponse(b"this is not audio")):
            r = tts_vocal.run({"text": "different text"}, self.settings)
        self.assertFalse(r["ok"])
        self.assertIn("ffmpeg failed", r["message"])


if __name__ == "__main__":
    unittest.main()
