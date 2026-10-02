"""Tests for v1.0.30's multi-key/model-dropdown Settings work.

Covers app/ai_providers.py (provider detection + model listing over the
OpenAI-Chat-Completions-compatible /models contract) and app/settings_store.py's
migration of a pre-existing flat api_key into the new api_keys vault.

Run from app\\:  python -m unittest test_settings_and_providers
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ai_providers
import settings_store




def _native_fails(openai_body: bytes):
    """A _probe stand-in where Gemini's native models.list fails, so list_models falls back to the
    OpenAI-compatible /models answer."""
    def probe(url: str, _headers: dict[str, str]) -> tuple[int, bytes]:
        return (403, b"{}") if "/v1beta/models" in url else (200, openai_body)
    return probe

class SaveSettingsRetryTests(unittest.TestCase):
    """Windows denies the atomic rename while a scanner briefly holds settings.json open (found by the
    shell e2e, which polls the file): a short hold must not lose the user's edit."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for target, value in (("APP_DATA", root), ("SETTINGS_PATH", root / "settings.json")):
            p = patch.object(settings_store, target, value)
            p.start()
            self.addCleanup(p.stop)

    def test_a_brief_hold_is_waited_out(self) -> None:
        real = os.replace
        calls = {"n": 0}

        def flaky(src, dst):
            calls["n"] += 1
            if calls["n"] <= 3:
                raise PermissionError(5, "Access is denied")
            return real(src, dst)

        with patch.object(settings_store.os, "replace", flaky):
            settings_store.save_settings({"listen_port": 4321})
        self.assertEqual(calls["n"], 4)
        self.assertEqual(json.loads(settings_store.SETTINGS_PATH.read_text(encoding="utf-8"))["listen_port"], 4321)

    def test_a_hold_that_never_ends_is_still_an_error(self) -> None:
        with patch.object(settings_store.os, "replace", side_effect=PermissionError(5, "Access is denied")) as rep:
            with self.assertRaises(PermissionError):
                settings_store.save_settings({"listen_port": 1})
        self.assertEqual(rep.call_count, 10)


class AiProvidersTests(unittest.TestCase):
    def test_detect_provider_empty_key(self) -> None:
        provider, base, message = ai_providers.detect_provider("")
        self.assertEqual(provider, "")
        self.assertIn("No API key", message)

    def test_detect_provider_picks_first_200(self) -> None:
        # xai-prefixed key orders xai first; only openai's probe returns 200 here,
        # so detection must still find it further down the order, not just guess
        # from the prefix.
        def fake_probe(url: str, _headers: dict[str, str]) -> tuple[int, bytes]:
            if url.startswith(ai_providers.PROVIDER_DEFAULTS["openai"]):
                return 200, b"{}"
            return 401, b"{}"

        with patch("ai_providers._probe", side_effect=fake_probe):
            provider, base, message = ai_providers.detect_provider("xai-doesnotmatter")
        self.assertEqual(provider, "openai")
        self.assertEqual(base, ai_providers.PROVIDER_DEFAULTS["openai"])

    def test_list_models_filters_non_chat_models(self) -> None:
        fake_body = json.dumps({"data": [
            {"id": "gpt-4o"},
            {"id": "text-embedding-3-small"},
            {"id": "whisper-1"},
            {"id": "dall-e-3"},
            {"id": "gpt-4o-mini"},
        ]}).encode("utf-8")

        with patch("ai_providers._probe", return_value=(200, fake_body)):
            models = ai_providers.list_models("openai", "sk-test", "https://api.openai.com/v1")

        self.assertEqual(models, ["gpt-4o", "gpt-4o-mini"])

    def test_list_models_empty_on_failure(self) -> None:
        with patch("ai_providers._probe", return_value=(401, b"{}")):
            models = ai_providers.list_models("openai", "bad-key", "https://api.openai.com/v1")
        self.assertEqual(models, [])

    def test_detect_provider_anthropic(self) -> None:
        def fake_probe(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
            if "api.anthropic.com" in url and "x-api-key" in headers:
                return 200, b"{}"
            return 401, b"{}"

        with patch("ai_providers._probe", side_effect=fake_probe):
            provider, base, message = ai_providers.detect_provider("sk-ant-test-key")
        self.assertEqual(provider, "anthropic")
        self.assertEqual(base, "https://api.anthropic.com/v1")

    def test_detect_provider_aq_gemini(self) -> None:
        def fake_probe(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
            if "generativelanguage.googleapis.com" in url:
                return 200, b"{}"
            return 401, b"{}"

        with patch("ai_providers._probe", side_effect=fake_probe):
            provider, base, message = ai_providers.detect_provider("AQ.Ab8RN6-test-key")
        self.assertEqual(provider, "gemini")
        self.assertEqual(base, ai_providers.PROVIDER_DEFAULTS["gemini"])

    def test_list_models_filters_live_and_strips_prefix(self) -> None:
        fake_body = json.dumps({"data": [
            {"id": "models/gemini-3.6-flash"},
            {"id": "models/gemini-3.8-live"},
            {"id": "gemini-2.0-flash-realtime-exp"},
            {"id": "models/gemini-3.1-pro"},
        ]}).encode("utf-8")

        with patch("ai_providers._probe", side_effect=_native_fails(fake_body)):
            models = ai_providers.list_models("gemini", "AIza-test", ai_providers.PROVIDER_DEFAULTS["gemini"])

        # models/ prefix stripped, -live and realtime filtered out
        self.assertEqual(models, ["gemini-3.1-pro", "gemini-3.6-flash"])

    def test_list_models_drops_transcribe_robotics_and_computer_use(self) -> None:
        fake_body = json.dumps({"data": [
            {"id": "models/gemini-3.8-flash"},
            {"id": "models/gemini-3.5-transcribe"},
            {"id": "models/gemini-robotics-er-2-preview"},
            {"id": "models/gemini-2.5-computer-use-preview-10-2025"},
        ]}).encode("utf-8")
        with patch("ai_providers._probe", side_effect=_native_fails(fake_body)):
            models = ai_providers.list_models("gemini", "AIza-test", ai_providers.PROVIDER_DEFAULTS["gemini"])
        self.assertEqual(models, ["gemini-3.8-flash"])

    def test_gemini_native_list_keeps_only_chat_models_across_pages(self) -> None:
        gc = ["generateContent", "countTokens"]
        page1 = {"models": [
            {"name": "models/gemini-3.8-flash", "supportedGenerationMethods": gc},
            {"name": "models/gemini-3.1-flash-live-preview", "supportedGenerationMethods": ["bidiGenerateContent"]},
            {"name": "models/gemini-2.5-flash-native-audio-preview-12-2025", "supportedGenerationMethods": ["bidiGenerateContent"]},
            {"name": "models/lyria-realtime-exp", "supportedGenerationMethods": ["bidiGenerateMusic"]},
            {"name": "models/lyria-3.5-clip-preview", "supportedGenerationMethods": gc},
            {"name": "models/gemini-3.1-flash-tts-preview", "supportedGenerationMethods": gc},
        ], "nextPageToken": "p2"}
        page2 = {"models": [
            {"name": "models/gemini-3.1-flash-image", "supportedGenerationMethods": gc},
            {"name": "models/nano-banana-pro-preview", "supportedGenerationMethods": gc},
            {"name": "models/veo-3.1-generate-preview", "supportedGenerationMethods": ["predictLongRunning"]},
            {"name": "models/imagen-4.0-generate", "supportedGenerationMethods": ["predict"]},
            {"name": "models/gemini-embedding-2-preview", "supportedGenerationMethods": ["embedContent"]},
            {"name": "models/deep-research-preview-04-2026", "supportedGenerationMethods": gc},
            {"name": "models/gemini-3.1-pro", "supportedGenerationMethods": gc},
        ]}
        urls: list[str] = []

        def fake_probe(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
            urls.append(url)
            self.assertEqual(headers, {"x-goog-api-key": "AIza-test"})
            return 200, json.dumps(page2 if "pageToken=p2" in url else page1).encode("utf-8")

        with patch("ai_providers._probe", side_effect=fake_probe):
            models = ai_providers.list_models("gemini", "AIza-test", ai_providers.PROVIDER_DEFAULTS["gemini"])
        self.assertEqual(models, ["gemini-3.1-pro", "gemini-3.8-flash"])
        self.assertEqual(len(urls), 2)

    def test_probe_chat_model_verdicts(self) -> None:
        import io
        import urllib.error

        class Resp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def http(code):
            return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b"{}"))

        base = ai_providers.PROVIDER_DEFAULTS["gemini"]
        with patch("urllib.request.urlopen", return_value=Resp()) as op:
            self.assertEqual(ai_providers.probe_chat_model("gemini", "k", base, "gemini-3.8-flash"), "ok")
            sent = json.loads(op.call_args[0][0].data)
            self.assertEqual(sent["tools"][0]["function"]["name"], "ping")      # tool calling is part of the test
            self.assertTrue(op.call_args[0][0].full_url.endswith("/chat/completions"))
        for code, verdict in ((429, "busy"), (503, "busy"), (400, "broken"), (403, "broken"), (404, "broken")):
            with patch("urllib.request.urlopen", side_effect=http(code)):
                self.assertEqual(ai_providers.probe_chat_model("gemini", "k", base, "m"), verdict, code)
        with patch("urllib.request.urlopen", side_effect=TimeoutError()):
            self.assertEqual(ai_providers.probe_chat_model("gemini", "k", base, "m"), "busy")
        self.assertEqual(ai_providers.probe_chat_model("gemini", "", base, "m"), "broken")

    def test_gemini_thought_signature_preserved_in_stream(self) -> None:
        import genius_client
        from io import BytesIO

        # Simulate Gemini 3 streaming SSE with thought_signature inside extra_content
        sse_lines = [
            b"data: " + json.dumps({
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_123",
                            "function": {"name": "live_connect", "arguments": "{}"},
                            "extra_content": {"google": {"thought_signature": "sig_abc123"}},
                        }]
                    }
                }]
            }).encode("utf-8") + b"\n\n",
            b"data: [DONE]\n\n",
        ]

        class FakeResponse:
            def __init__(self, lines: list[bytes]) -> None:
                self.lines = iter(lines)
            def __iter__(self):
                return self.lines
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        with patch("urllib.request.urlopen", return_value=FakeResponse(sse_lines)):
            content, tool_calls = genius_client._stream_round(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                "test-key",
                {"model": "gemini-3.6-flash", "messages": []}
            )

        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "live_connect")
        self.assertEqual(tool_calls[0]["extra_content"], {"google": {"thought_signature": "sig_abc123"}})


class SettingsMigrationTests(unittest.TestCase):
    """A settings.json saved before the multi-key vault existed must not lose
    its key -- load_settings() should surface it as the first api_keys entry
    (regression guard for the exact scenario the deferred v1.0.28 plan item and
    this pass's implementation were both written to avoid)."""

    def test_legacy_flat_key_is_migrated_into_api_keys(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            fake_path = Path(tmp) / "settings.json"
            fake_path.write_text(json.dumps({
                "api_key": "xai-legacy-key",
                "api_base": "https://api.x.ai/v1",
                "model": "grok-4.6",
            }), encoding="utf-8")
            with patch.object(settings_store, "SETTINGS_PATH", fake_path):
                data = settings_store.load_settings()

        self.assertEqual(len(data["api_keys"]), 1)
        self.assertEqual(data["api_keys"][0]["api_key"], "xai-legacy-key")
        self.assertEqual(data["active_api_key_id"], "imported-legacy")
        # The flat fields stay untouched -- genius_client.py's only touchpoints.
        self.assertEqual(data["api_key"], "xai-legacy-key")

    def test_no_migration_when_api_keys_already_present(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            fake_path = Path(tmp) / "settings.json"
            fake_path.write_text(json.dumps({
                "api_key": "xai-active",
                "api_keys": [{"id": "k_1", "label": "Mine", "provider": "xai", "api_key": "xai-active", "api_base": "", "model": ""}],
                "active_api_key_id": "k_1",
            }), encoding="utf-8")
            with patch.object(settings_store, "SETTINGS_PATH", fake_path):
                data = settings_store.load_settings()

        self.assertEqual(len(data["api_keys"]), 1)
        self.assertEqual(data["api_keys"][0]["id"], "k_1")


class InstanceIsolationTests(unittest.TestCase):
    """v1.0.46: LIVE_ACTIONS_INSTANCE gives a second copy its own state."""

    def _probe(self, instance: str | None) -> dict[str, str]:
        import os
        import subprocess
        import sys

        env = {k: v for k, v in os.environ.items() if k != "LIVE_ACTIONS_INSTANCE"}
        env["APPDATA"] = r"C:\fake-appdata"
        if instance is not None:
            env["LIVE_ACTIONS_INSTANCE"] = instance
        code = (
            "import json, settings_store as s;"
            "print(json.dumps({'data': str(s.APP_DATA), 'listen': s.DEFAULTS['listen_port'],"
            " 'bridge': s.DEFAULTS['bridge_port'], 'suffix': s.instance_suffix()}))"
        )
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                             text=True, check=True, cwd=os.path.dirname(__file__)).stdout
        return json.loads(out)

    def test_unset_keeps_todays_values(self) -> None:
        got = self._probe(None)
        self.assertTrue(got["data"].endswith("Live Actions"))
        self.assertEqual((got["listen"], got["bridge"], got["suffix"]), (11925, 11924, ""))

    def test_named_instance_gets_own_folder_and_ports(self) -> None:
        got = self._probe("redesign")
        self.assertTrue(got["data"].endswith("Live Actions-redesign"))
        self.assertEqual((got["listen"], got["bridge"], got["suffix"]), (12025, 12024, "-redesign"))

    def test_instance_name_is_sanitised(self) -> None:
        got = self._probe("a/b..c$d")
        self.assertEqual(got["suffix"], "-abcd")


if __name__ == "__main__":
    unittest.main()
