"""Tests for v1.0.42's selectable Genius agents (app/agent_registry.py) plus the
system-prompt override and tool-filtering wiring in app/genius_client.py.

Run from app\\:  python -m unittest test_agent_registry
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import agent_registry
import genius_client
import settings_store
from genius_client import LIVE_TOOLS


# A saved TTS profile, so the capability axis added in v1.2.0 can be held steady
# while a test varies something else.
_PROFILE = {"name": "Test Voice", "provider": "cartesia", "api_key": "sk_car_x", "voice_id": "v1"}


def _settings(**overrides):
    data = settings_store.default_settings()
    data.update(overrides)
    return data


class ToolGroupCoverageTests(unittest.TestCase):
    def test_every_live_tool_is_core_or_grouped(self) -> None:
        grouped = set(agent_registry.ALL_TOOL_NAMES)
        missing = []
        for t in LIVE_TOOLS:
            name = t["name"]
            if name in agent_registry.CORE_TOOLS:
                continue
            if name not in grouped:
                missing.append(name)
        self.assertEqual(missing, [], f"ungrouped tools (add to TOOL_GROUPS or CORE_TOOLS): {missing}")

    def test_no_tool_double_grouped(self) -> None:
        seen: dict[str, str] = {}
        for group, names in agent_registry.TOOL_GROUPS.items():
            for name in names:
                self.assertNotIn(
                    name, seen, f"{name!r} appears in both {seen.get(name)!r} and {group!r}"
                )
                seen[name] = group

    def test_core_tools_never_toggleable(self) -> None:
        for group_names in agent_registry.TOOL_GROUPS.values():
            for core_name in agent_registry.CORE_TOOLS:
                self.assertNotIn(core_name, group_names)


class ParseFrontmatterTests(unittest.TestCase):
    def test_round_trips_shipped_agent_files(self) -> None:
        live_tool_names = {t["name"] for t in LIVE_TOOLS}
        agents = agent_registry.list_agents(_settings())
        slugs = {a["slug"] for a in agents}
        self.assertEqual(
            slugs,
            {"mix-master-engineer", "music-theory-harmony", "sound-designer", "drum-beat-programmer"},
        )
        for agent in agents:
            self.assertTrue(agent["body"].strip(), f"{agent['slug']} has an empty body")
            self.assertTrue(agent["title"])
            tools_default = agent["tools_default"]
            self.assertIsNotNone(tools_default, f"{agent['slug']} is missing tools_default")
            self.assertTrue(tools_default)
            for name in tools_default:
                self.assertIn(name, live_tool_names, f"{agent['slug']} lists unknown tool {name!r}")

    def test_folded_and_list_forms(self) -> None:
        text = (
            "---\n"
            "name: sample-agent\n"
            "title: Sample Agent\n"
            "description: >\n"
            "  A description\n"
            "  folded across lines.\n"
            "tools_default: [live_connect, live_read_meter,\n"
            "                live_analyze_audio]\n"
            "---\n"
            "Body text here.\n"
        )
        meta, body = agent_registry.parse_frontmatter(text)
        self.assertEqual(meta["name"], "sample-agent")
        self.assertEqual(meta["description"], "A description folded across lines.")
        self.assertEqual(meta["tools_default"], ["live_connect", "live_read_meter", "live_analyze_audio"])
        self.assertEqual(body.strip(), "Body text here.")


class DefaultToolMapTests(unittest.TestCase):
    def test_tools_default_present_seeds_subset(self) -> None:
        agent = {"tools_default": ["live_read_meter", "live_analyze_audio"]}
        result = agent_registry.default_tool_map(agent)
        self.assertTrue(result["live_read_meter"])
        self.assertTrue(result["live_analyze_audio"])
        self.assertFalse(result["live_write_drum_grid"])

    def test_tools_default_absent_seeds_everything_on(self) -> None:
        result = agent_registry.default_tool_map({"tools_default": None})
        self.assertTrue(all(result.values()))
        self.assertEqual(set(result), agent_registry.ALL_TOOL_NAMES)


class ResolveActiveTests(unittest.TestCase):
    def test_no_active_agent_is_stock_genius(self) -> None:
        agent, allowed = agent_registry.resolve_active(_settings())
        self.assertIsNone(agent)
        self.assertIsNone(allowed)

    def test_stale_active_agent_falls_back_to_stock(self) -> None:
        settings = _settings(active_agent="mix-master-engineer", enabled_agents=[])
        agent, allowed = agent_registry.resolve_active(settings)
        self.assertIsNone(agent)
        self.assertIsNone(allowed)

    def test_active_agent_resolves_stored_prefs_over_defaults(self) -> None:
        settings = _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
            agent_tool_prefs={"mix-master-engineer": {"live_read_meter": False}},
        )
        agent, allowed = agent_registry.resolve_active(settings)
        self.assertIsNotNone(agent)
        self.assertEqual(agent["slug"], "mix-master-engineer")
        self.assertNotIn("live_read_meter", allowed)
        self.assertIn("live_analyze_audio", allowed)


class SettingsRoundTripTests(unittest.TestCase):
    def test_new_keys_survive_save_and_load(self) -> None:
        data = settings_store.default_settings()
        data["enabled_agents"] = ["mix-master-engineer"]
        data["active_agent"] = "mix-master-engineer"
        data["agent_tool_prefs"] = {"mix-master-engineer": {"live_read_meter": False}}
        # Round-trip through the real save/load path against a temp file.
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            fake_path = Path(tmp) / "settings.json"
            with patch.object(settings_store, "SETTINGS_PATH", fake_path), \
                 patch.object(settings_store, "APP_DATA", Path(tmp)):
                settings_store.save_settings(data)
                loaded = settings_store.load_settings()
        self.assertEqual(loaded["enabled_agents"], ["mix-master-engineer"])
        self.assertEqual(loaded["active_agent"], "mix-master-engineer")
        self.assertEqual(loaded["agent_tool_prefs"], {"mix-master-engineer": {"live_read_meter": False}})


class BuildSystemPromptTests(unittest.TestCase):
    STOCK_SENTENCE = "You are Genius inside Live Actions"
    NUMBERING_RULE = "Numbering (v1.0.32)"
    LIBRARY_HEADING = "## Genius knowledge library"

    def test_no_active_agent_keeps_stock_persona(self) -> None:
        prompt = genius_client.build_system_prompt(_settings(), "unknown")
        self.assertIn(self.STOCK_SENTENCE, prompt)
        self.assertIn(self.NUMBERING_RULE, prompt)
        self.assertIn(self.LIBRARY_HEADING, prompt)

    def test_active_agent_overrides_persona_only(self) -> None:
        settings = _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
        )
        prompt = genius_client.build_system_prompt(settings, "unknown")
        self.assertNotIn(self.STOCK_SENTENCE, prompt)
        self.assertIn("Studio Mix & Master Engineer", prompt)
        self.assertIn(self.NUMBERING_RULE, prompt)
        self.assertIn(self.LIBRARY_HEADING, prompt)


class ToolFilteringTests(unittest.TestCase):
    def _capture_tools_anthropic(self, settings):
        captured = {}

        def fake_stream(endpoint, api_key, payload, **kwargs):
            captured["tools"] = payload.get("tools")
            return "ok", []

        with patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream):
            genius_client._ask_genius_anthropic(settings, [{"role": "user", "content": "hi"}], "unknown")
        return captured["tools"]

    def _capture_tools_openai(self, settings):
        captured = {}

        def fake_stream(endpoint, api_key, payload, **kwargs):
            captured["tools"] = payload.get("tools")
            return "ok", []

        with patch.object(genius_client, "_stream_round", side_effect=fake_stream):
            genius_client._ask_genius_openai(settings, [{"role": "user", "content": "hi"}], "unknown")
        return captured["tools"]

    def test_disabled_tool_absent_anthropic(self) -> None:
        settings = _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
            agent_tool_prefs={"mix-master-engineer": {"live_write_drum_grid": False}},
        )
        names = {t["name"] for t in self._capture_tools_anthropic(settings)}
        self.assertNotIn("live_write_drum_grid", names)
        for core in agent_registry.CORE_TOOLS:
            self.assertIn(core, names)

    def test_disabled_tool_absent_openai(self) -> None:
        settings = _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
            agent_tool_prefs={"mix-master-engineer": {"live_write_drum_grid": False}},
        )
        names = {t["function"]["name"] for t in self._capture_tools_openai(settings)}
        self.assertNotIn("live_write_drum_grid", names)
        for core in agent_registry.CORE_TOOLS:
            self.assertIn(core, names)

    def test_all_toggleable_off_still_keeps_core(self) -> None:
        agent = agent_registry.load_agent(_settings(), "mix-master-engineer")
        all_off = {name: False for name in agent_registry.ALL_TOOL_NAMES}
        settings = _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
            agent_tool_prefs={"mix-master-engineer": all_off},
        )
        names = {t["name"] for t in self._capture_tools_anthropic(settings)}
        self.assertEqual(names, set(agent_registry.CORE_TOOLS))

    def test_no_active_agent_sends_every_tool_when_every_engine_is_up(self) -> None:
        # "No active agent" means no PERSONA filtering. Capability filtering is a
        # separate axis (engine E2 in v1.1.0, a saved TTS profile in v1.2.0), so this
        # only holds with every capability satisfied -- hence the patch and the profile
        # rather than a bare call.
        with patch.object(genius_client, "rs_online", return_value=True):
            names = {t["name"] for t in self._capture_tools_anthropic(_settings(tts_profiles=[_PROFILE]))}
        self.assertEqual(names, {t["name"] for t in LIVE_TOOLS})

    def test_browser_tools_are_withheld_when_engine_e2_is_offline(self) -> None:
        # A tool the model cannot call is a capability it cannot promise. This
        # is what stops Genius offering to load a preset when the LiveActionsRS
        # Remote Script isn't enabled.
        with patch.object(genius_client, "rs_online", return_value=False):
            names = {t["name"] for t in self._capture_tools_anthropic(_settings(tts_profiles=[_PROFILE]))}
        self.assertEqual(names, {t["name"] for t in LIVE_TOOLS} - genius_client.E2_TOOLS)
        # Everything that does not need the browser is still offered.
        self.assertIn("live_read_set", names)
        self.assertIn("live_custom_instructions", names)

    def test_tts_tools_are_withheld_when_no_profile_is_saved(self) -> None:
        # The same honesty rule on a second, purely local capability axis: with no
        # profile there is nothing to generate with, so Genius is not given the tool
        # and cannot offer to make a vocal.
        with patch.object(genius_client, "rs_online", return_value=True):
            names = {t["name"] for t in self._capture_tools_anthropic(_settings(tts_profiles=[]))}
        self.assertEqual(names, {t["name"] for t in LIVE_TOOLS} - genius_client.TTS_TOOLS)
        # live_audio_op is NOT gated -- ffmpeg edits need no profile and no API key.
        self.assertIn("live_audio_op", names)


class ToolExecutionEnforcementTests(unittest.TestCase):
    """A model can emit a tool call for a name we didn't offer in the schema --
    some providers don't hard-enforce the function list, and live_control_section's
    prose describes every tool regardless of which agent is active. The bridge
    must refuse it, not silently execute it (the schema-only filter is not enough)."""

    def _disabled_agent_settings(self):
        return _settings(
            active_agent="mix-master-engineer",
            enabled_agents=["mix-master-engineer"],
            agent_tool_prefs={"mix-master-engineer": {"live_write_drum_grid": False}},
        )

    def test_disabled_tool_refused_at_execution_anthropic(self) -> None:
        state = {"n": 0}

        def fake_stream(endpoint, api_key, payload, **kwargs):
            state["n"] += 1
            if state["n"] == 1:
                return "", [{"call_id": "c1", "name": "live_write_drum_grid", "arguments": "{}"}]
            return "Can't do that with this agent.", []

        with patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream), \
             patch.object(genius_client, "call_live_tool") as mock_call:
            reply = genius_client._ask_genius_anthropic(
                self._disabled_agent_settings(), [{"role": "user", "content": "program a beat"}], "unknown",
            )
        mock_call.assert_not_called()
        self.assertEqual(reply, "Can't do that with this agent.")

    def test_disabled_tool_refused_at_execution_openai(self) -> None:
        state = {"n": 0}

        def fake_stream(endpoint, api_key, payload, **kwargs):
            state["n"] += 1
            if state["n"] == 1:
                return "", [{"call_id": "c1", "name": "live_write_drum_grid", "arguments": "{}"}]
            return "Can't do that with this agent.", []

        with patch.object(genius_client, "_stream_round", side_effect=fake_stream), \
             patch.object(genius_client, "call_live_tool") as mock_call:
            reply = genius_client._ask_genius_openai(
                self._disabled_agent_settings(), [{"role": "user", "content": "program a beat"}], "unknown",
            )
        mock_call.assert_not_called()
        self.assertEqual(reply, "Can't do that with this agent.")


class ToolLoopSafetyTests(unittest.TestCase):
    """A long multi-step ask (e.g. "fix the whole mix") can legitimately need
    many tool-call rounds. The last round must force a text reply instead of
    raising "reached the tool-call limit", regardless of how many rounds a
    verbose model burns through first."""

    def test_last_round_forces_text_reply_anthropic(self) -> None:
        calls: list[dict] = []

        def fake_stream(endpoint, api_key, payload, **kwargs):
            calls.append(payload)
            if "tools" in payload:
                return "", [{"call_id": "c%d" % len(calls), "name": "live_connect", "arguments": "{}"}]
            return "Here's a summary of what I did.", []

        with patch.object(genius_client, "MAX_TOOL_LOOPS", 3), \
             patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream):
            reply = genius_client._ask_genius_anthropic(
                _settings(), [{"role": "user", "content": "fix the mix"}], "unknown",
            )
        self.assertEqual(reply, "Here's a summary of what I did.")
        self.assertEqual(len(calls), 3)
        self.assertNotIn("tools", calls[-1])

    def test_last_round_forces_text_reply_openai(self) -> None:
        calls: list[dict] = []

        def fake_stream(endpoint, api_key, payload, **kwargs):
            calls.append(payload)
            if payload.get("tool_choice") == "auto":
                return "", [{"call_id": "c%d" % len(calls), "name": "live_connect", "arguments": "{}"}]
            return "Here's a summary of what I did.", []

        with patch.object(genius_client, "MAX_TOOL_LOOPS", 3), \
             patch.object(genius_client, "_stream_round", side_effect=fake_stream):
            reply = genius_client._ask_genius_openai(
                _settings(), [{"role": "user", "content": "fix the mix"}], "unknown",
            )
        self.assertEqual(reply, "Here's a summary of what I did.")
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[-1].get("tool_choice"), "none")


if __name__ == "__main__":
    unittest.main()
