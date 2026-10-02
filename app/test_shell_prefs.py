"""Tests for shell_prefs.PrefsService (no network, no window, nothing written to %APPDATA%)."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

import agent_registry
import shell_prefs
from shell_prefs import PrefsService, mask_key
from shell_model import SessionModel, load_demo_state

SECRETS = ["sk-live-SECRET-0123456789", "xai-SECRET-abcdefghij", "cart-SECRET-zzzzzzzzzz"]


class FakeNet:
    def __init__(self, lock=None):
        self.lock = lock
        self.lock_free_during_probe: list[bool] = []
        self.calls: list[tuple] = []
        self.provider = ("openai", "https://api.openai.com/v1", "Detected openai.")
        self.models = ["gpt-5", "gpt-4o"]
        self.test_result: str | Exception = "ok"
        self.verdicts: dict[str, str] = {}   # model -> live-test verdict; default "ok"

    def _probe(self):
        if self.lock is not None:
            # A probe must not run under the shared lock: another thread has to be able to take it.
            got = []
            t = threading.Thread(target=lambda: got.append(self.lock.acquire(timeout=0.5) and (self.lock.release() or True)))
            t.start(); t.join()
            self.lock_free_during_probe.append(bool(got and got[0]))

    def detect_provider(self, key):
        self._probe(); self.calls.append(("detect", key)); return self.provider

    def list_models(self, provider, key, base):
        self._probe(); self.calls.append(("models", provider, key, base)); return list(self.models)

    def probe_model(self, provider, key, base, model):
        self._probe(); return self.verdicts.get(model, "ok")

    def test_key(self, settings):
        self._probe(); self.calls.append(("test", dict(settings)))
        if isinstance(self.test_result, Exception):
            raise self.test_result
        return self.test_result

    def tts_detect(self, key):
        self._probe(); self.calls.append(("tts_detect", key)); return ("cartesia", "Detected cartesia.")

    def tts_voices(self, provider, key):
        self._probe(); self.calls.append(("voices", provider, key))
        return [{"voice_id": "v1", "name": "Ada", "custom": False}, {"voice_id": "v2", "name": "Me", "custom": True}]

    def provider_defaults(self):
        return {"xai": "https://api.x.ai/v1", "openai": "https://api.openai.com/v1"}


def make(settings=None, themes=("risograph-art-studio",), fail_save=False):
    tmp = Path(tempfile.mkdtemp(prefix="la-prefs-"))
    for slug in themes:
        (tmp / (slug + ".css")).write_text("/* */", encoding="utf-8")
    settings = settings if settings is not None else {
        "api_key": "", "api_base": "https://api.x.ai/v1", "model": "grok-4.6", "api_keys": [], "active_api_key_id": "",
        "listen_port": 11925, "bridge_port": 11924, "tools_dir": "T", "knowledge_dir": "K", "enabled_agents": [],
        "active_agent": "", "agent_tool_prefs": {}, "tts_profiles": [], "theme": "risograph-art-studio",
    }
    lock = threading.RLock()
    saved: list[dict] = []
    logs: list[str] = []
    hooks_hit: list[str] = []

    def save(data):
        if fail_save:
            raise OSError("disk full")
        saved.append(data)

    net = FakeNet(lock)
    svc = PrefsService(lock=lock, settings=settings, save=save, log=logs.append, net=net, themes_dir=tmp,
                       hooks={"tools": lambda: hooks_hit.append("tools"), "catalog": lambda: hooks_hit.append("catalog"), "genius": lambda: hooks_hit.append("genius")},
                       open_folder=lambda p: hooks_hit.append("open:%s" % p.name))
    return svc, settings, saved, logs, hooks_hit, net


class KeysAndSecrets(unittest.TestCase):
    def test_mask_shape_matches_the_preview(self):
        self.assertEqual(mask_key("xai-abcdefgh91af"), "xai-••••••••91af")
        self.assertEqual(mask_key("short"), "••••••••")
        self.assertEqual(mask_key(""), "")

    def test_the_snapshot_never_contains_a_secret(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai"})
        s["tts_profiles"] = [{"name": "Narrator", "provider": "xai", "api_key": SECRETS[1], "voice_id": "v", "model": "", "settings": {}}]
        s["api_keys"].append({"id": "k2", "label": "B", "provider": "xai", "api_key": SECRETS[2], "api_base": "", "model": ""})
        text = repr(svc.call("set_theme", {"slug": "risograph-art-studio"}))
        text += repr(svc.snapshot())
        for secret in SECRETS:
            self.assertNotIn(secret, text)
        self.assertIn(mask_key(SECRETS[0]), text)

    def test_add_key_saves_activates_and_mirrors_into_the_flat_fields(self):
        svc, s, saved, logs, hooks, _ = make()
        r = svc.call("add_key", {"api_key": "  " + SECRETS[0] + " ", "label": "Main", "provider": "openai", "model": "gpt-5"})
        self.assertTrue(r["ok"], r)
        self.assertEqual((s["api_key"], s["api_base"], s["model"]), (SECRETS[0], "https://api.openai.com/v1", "gpt-5"))
        self.assertEqual(s["api_keys"][0]["label"], "Main")
        self.assertEqual(s["active_api_key_id"], s["api_keys"][0]["id"])
        self.assertEqual(saved[-1]["api_key"], SECRETS[0])
        self.assertEqual(r["prefs"]["keys"][0]["masked"], mask_key(SECRETS[0]))
        self.assertTrue(r["prefs"]["hasKey"])
        self.assertIn("genius", hooks)
        self.assertIn("Saved key 'Main'.", logs)

    def test_saving_the_same_key_twice_updates_instead_of_duplicating(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "One"})
        svc.call("add_key", {"api_key": SECRETS[0], "label": "Renamed", "model": "m2"})
        self.assertEqual(len(s["api_keys"]), 1)
        self.assertEqual((s["api_keys"][0]["label"], s["model"]), ("Renamed", "m2"))

    def test_empty_key_is_refused_and_nothing_changes(self):
        svc, s, saved, *_ = make()
        r = svc.call("add_key", {"api_key": "   "})
        self.assertEqual((r["ok"], r["error"]), (False, "Paste an API key first."))
        self.assertEqual((saved, s["api_keys"]), ([], []))

    def test_use_and_delete(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5"})
        svc.call("add_key", {"api_key": SECRETS[1], "label": "B", "provider": "xai", "model": "grok-4.6"})
        a, b = s["api_keys"]
        self.assertEqual(s["active_api_key_id"], b["id"])
        svc.call("use_key", {"id": a["id"]})
        self.assertEqual((s["api_key"], s["api_base"], s["model"]), (SECRETS[0], "https://api.openai.com/v1", "gpt-5"))
        self.assertFalse(svc.call("use_key", {"id": "nope"})["ok"])
        svc.call("delete_key", {"id": b["id"]})                      # not the active one
        self.assertEqual((len(s["api_keys"]), s["api_key"]), (1, SECRETS[0]))
        svc.call("delete_key", {"id": a["id"]})                      # the active one: it must really stop being used
        self.assertEqual((s["api_keys"], s["active_api_key_id"], s["api_key"]), ([], "", ""))

    def test_header_picker_switches_key_and_model_in_one_save(self):
        svc, s, saved, logs, hooks_hit, net = make()
        notes: list[str] = []
        svc._hooks["notice"] = notes.append
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5"})
        svc.call("add_key", {"api_key": SECRETS[1], "label": "B", "provider": "xai", "model": "grok-4.6"})
        a = s["api_keys"][0]
        before, hits = len(saved), hooks_hit.count("genius")
        r = svc.call("use_key_model", {"id": a["id"], "model": "gpt-4o"})
        self.assertTrue(r["ok"])
        self.assertEqual(len(saved), before + 1)                       # one save, not two
        self.assertEqual(hooks_hit.count("genius"), hits + 1)          # one Genius refresh
        a = next(k for k in s["api_keys"] if k["id"] == a["id"])        # _commit adopts a deep copy
        self.assertEqual((s["active_api_key_id"], s["api_key"], s["api_base"], s["model"], a["model"]),
                         (a["id"], SECRETS[0], "https://api.openai.com/v1", "gpt-4o", "gpt-4o"))
        self.assertEqual(notes, ["Now using A · gpt-4o"])
        self.assertFalse(svc.call("use_key_model", {"id": "nope", "model": "x"})["ok"])
        self.assertFalse(svc.call("use_key_model", {"id": a["id"], "model": " "})["ok"])
        self.assertEqual(s["model"], "gpt-4o")

    def test_key_models_lists_per_key_without_leaking_the_key(self):
        svc, s, saved, logs, hooks_hit, net = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5"})
        a = s["api_keys"][0]
        r = svc.call("key_models", {"id": a["id"]})
        self.assertEqual(r["models"], ["gpt-5", "gpt-4o"])
        self.assertEqual(r["prefs"]["modelsByKey"], {a["id"]: ["gpt-5", "gpt-4o"]})
        self.assertEqual(net.calls[-1], ("models", "openai", SECRETS[0], "https://api.openai.com/v1"))
        self.assertTrue(all(net.lock_free_during_probe))
        blob = repr(r)
        self.assertFalse(any(secret in blob for secret in SECRETS))
        self.assertFalse(svc.call("key_models", {"id": "nope"})["ok"])

    def test_key_models_keeps_only_models_that_pass_the_live_test(self):
        svc, s, saved, logs, hooks_hit, net = make()
        net.models = ["gpt-5", "gpt-4o", "o-old", "gpt-busy"]
        net.verdicts = {"o-old": "broken", "gpt-busy": "busy"}
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5"})
        a = s["api_keys"][0]
        r = svc.call("key_models", {"id": a["id"]})
        self.assertEqual(r["models"], ["gpt-5", "gpt-4o", "gpt-busy"])    # broken hidden, busy kept
        self.assertEqual(r["prefs"]["busyByKey"], {a["id"]: ["gpt-busy"]})
        self.assertTrue(all(net.lock_free_during_probe))
        self.assertTrue(any("1 hidden" in line for line in logs))

    def test_picking_a_tested_model_restores_its_providers_endpoint(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5",
                             "api_base": "https://stale.example/v1"})
        a = s["api_keys"][0]
        svc.call("use_key_model", {"id": a["id"], "model": "gpt-4o"})     # not tested yet: endpoint left alone
        self.assertEqual(s["api_base"], "https://stale.example/v1")
        svc.call("key_models", {"id": a["id"]})
        svc.call("use_key_model", {"id": a["id"], "model": "gpt-4o"})
        self.assertEqual((s["api_base"], s["api_keys"][0]["api_base"]), ("https://api.openai.com/v1",) * 2)
        svc.call("set_base", {"api_base": "https://stale.example/v1"})
        svc.call("set_model", {"model": "gpt-5"})                          # Preferences dropdown does the same
        self.assertEqual(s["api_base"], "https://api.openai.com/v1")

    def test_model_and_endpoint_follow_the_active_key(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[0], "label": "A", "provider": "openai", "model": "gpt-5"})
        svc.call("set_model", {"model": " gpt-4o "})
        svc.call("set_base", {"api_base": "https://example.test/v1"})
        self.assertEqual((s["model"], s["api_base"]), ("gpt-4o", "https://example.test/v1"))
        self.assertEqual((s["api_keys"][0]["model"], s["api_keys"][0]["api_base"]), ("gpt-4o", "https://example.test/v1"))
        self.assertFalse(svc.call("set_base", {"api_base": "ftp://nope"})["ok"])

    def test_a_failed_write_leaves_the_running_settings_untouched(self):
        svc, s, *_ = make(fail_save=True)
        r = svc.call("add_key", {"api_key": SECRETS[0]})
        self.assertFalse(r["ok"])
        self.assertIn("Could not save settings", r["error"])
        self.assertEqual((s["api_key"], s["api_keys"]), ("", []))


class Probes(unittest.TestCase):
    def test_probes_run_with_the_lock_released_and_never_mutate(self):
        svc, s, saved, logs, hooks, net = make()
        svc.call("add_key", {"api_key": SECRETS[0], "provider": "openai"})
        before = dict(s)
        r = svc.call("detect_provider", {"api_key": "typed-key-0123456789"})
        self.assertEqual((r["provider"], r["apiBase"]), ("openai", "https://api.openai.com/v1"))
        self.assertEqual(net.calls[-1], ("detect", "typed-key-0123456789"))
        r = svc.call("list_models", {})                               # falls back to the active key
        self.assertEqual((r["models"], net.calls[-1][2]), (["gpt-5", "gpt-4o"], SECRETS[0]))
        svc.call("tts_detect", {"api_key": "t"}); svc.call("tts_voices", {"provider": "xai", "api_key": "t"})
        self.assertTrue(net.lock_free_during_probe and all(net.lock_free_during_probe))
        self.assertEqual(s, before)

    def test_test_key_reports_success_and_failure_as_data(self):
        svc, s, _, _, _, net = make()
        svc.call("add_key", {"api_key": SECRETS[0], "provider": "openai", "model": "gpt-5"})
        self.assertEqual(svc.call("test_key", {})["test"], {"ok": True, "message": "ok"})
        sent = net.calls[-1][1]
        self.assertEqual((sent["api_key"], sent["model"], sent["provider"]), (SECRETS[0], "gpt-5", "openai"))
        net.test_result = RuntimeError("API 401: bad key")
        r = svc.call("test_key", {})
        self.assertTrue(r["ok"])                                      # the CALL worked; the key did not
        self.assertEqual(r["test"], {"ok": False, "message": "API 401: bad key"})
        self.assertEqual(svc.call("detect_provider", {"api_key": ""})["ok"], True)          # falls back to the active key


class Connection(unittest.TestCase):
    def test_ports_validate_and_flag_a_restart(self):
        svc, s, saved, *_ = make()
        self.assertFalse(svc.snapshot()["restart"])
        for bad in ({"listen": "abc", "bridge": 1}, {"listen": 0, "bridge": 5}, {"listen": 70000, "bridge": 5}, {"listen": 9000, "bridge": 9000}):
            self.assertFalse(svc.call("set_ports", bad)["ok"], bad)
        self.assertEqual(saved, [])
        r = svc.call("set_ports", {"listen": "12000", "bridge": "12001"})
        self.assertTrue(r["ok"] and r["prefs"]["restart"])
        self.assertEqual((s["listen_port"], s["bridge_port"]), (12000, 12001))
        svc.call("set_ports", {"listen": 11925, "bridge": 11924})
        self.assertFalse(svc.snapshot()["restart"])                   # back to what the running bridge uses

    def test_paths_are_whitelisted_and_tools_dir_reloads_the_catalog(self):
        svc, s, _, _, hooks, _ = make()
        self.assertFalse(svc.call("set_path", {"key": "api_key", "value": "x"})["ok"])
        self.assertEqual(s["api_key"], "")
        r = svc.call("set_path", {"key": "knowledge_dir", "value": "  Z:\\definitely\\not\\here  "})
        self.assertTrue(r["ok"] and "does not exist" in r["note"])
        self.assertEqual(s["knowledge_dir"], "Z:\\definitely\\not\\here")
        self.assertNotIn("tools", hooks)
        svc.call("set_path", {"key": "tools_dir", "value": tempfile.gettempdir()})
        self.assertIn("tools", hooks)
        self.assertEqual(svc.call("set_path", {"key": "ffmpeg_path", "value": "ffmpeg"})["note"], "")

    def test_theme_must_be_an_installed_kit(self):
        svc, s, *_ = make()
        self.assertEqual([t["slug"] for t in svc.snapshot()["themes"]], ["risograph-art-studio"])
        self.assertFalse(svc.call("set_theme", {"slug": "cyber-neon-pink"})["ok"])          # known, not installed
        self.assertFalse(svc.call("set_theme", {"slug": "../../evil"})["ok"])
        svc2, s2, *_ = make(themes=("risograph-art-studio", "cyber-neon-pink"))
        self.assertTrue(svc2.call("set_theme", {"slug": "cyber-neon-pink"})["ok"])
        self.assertEqual(s2["theme"], "cyber-neon-pink")

    def test_open_settings_folder_uses_the_injected_opener(self):
        svc, _, _, _, hooks, _ = make()
        self.assertTrue(svc.call("open_settings_folder", {})["ok"])
        self.assertTrue(any(h.startswith("open:") for h in hooks))


class Agents(unittest.TestCase):
    def setUp(self):
        self.agents = agent_registry.list_agents({})
        self.slug, self.title = self.agents[0]["slug"], self.agents[0]["title"]

    def test_enable_toggle_group_and_remove(self):
        svc, s, _, _, hooks, _ = make()
        snap = svc.snapshot()["agents"]
        self.assertEqual(snap["enabled"], [])
        self.assertIn(self.slug, [a["slug"] for a in snap["available"]])
        r = svc.call("enable_agent", {"slug": self.slug})
        self.assertTrue(r["ok"])
        enabled = r["prefs"]["agents"]["enabled"][0]
        self.assertEqual((enabled["slug"], enabled["title"]), (self.slug, self.title))
        self.assertEqual(enabled["total"], len(agent_registry.ALL_TOOL_NAMES))
        self.assertNotIn(self.slug, [a["slug"] for a in r["prefs"]["agents"]["available"]])
        self.assertIn("genius", hooks)

        groups = svc.call("agent_tools", {"slug": self.slug})["groups"]
        self.assertEqual({g["name"] for g in groups}, set(agent_registry.TOOL_GROUPS))
        name = groups[0]["tools"][0]["name"]
        was = groups[0]["tools"][0]["on"]
        r = svc.call("set_agent_tool", {"slug": self.slug, "name": name, "on": not was})
        self.assertEqual(r["groups"][0]["tools"][0]["on"], not was)
        self.assertEqual(s["agent_tool_prefs"][self.slug][name], not was)
        r = svc.call("set_agent_group", {"slug": self.slug, "group": groups[0]["name"], "on": False})
        self.assertTrue(all(not t["on"] for t in r["groups"][0]["tools"]))
        self.assertLess(r["prefs"]["agents"]["enabled"][0]["on"], r["prefs"]["agents"]["enabled"][0]["total"])
        self.assertFalse(svc.call("set_agent_tool", {"slug": self.slug, "name": "not_a_tool", "on": True})["ok"])
        self.assertFalse(svc.call("set_agent_tool", {"slug": "ghost", "name": name, "on": True})["ok"])

        s["active_agent"] = self.slug
        svc.call("remove_agent", {"slug": self.slug})
        self.assertEqual((s["enabled_agents"], s["active_agent"], self.slug in s["agent_tool_prefs"]), ([], "", False))

    def test_unknown_agent_is_refused(self):
        svc, s, *_ = make()
        self.assertFalse(svc.call("enable_agent", {"slug": "ghost-agent"})["ok"])
        self.assertEqual(s["enabled_agents"], [])


class TtsProfiles(unittest.TestCase):
    def test_keep_typed_and_vault_key_modes(self):
        svc, s, *_ = make()
        svc.call("add_key", {"api_key": SECRETS[2], "label": "Cartesia", "provider": "cartesia"})
        vault_id = s["api_keys"][0]["id"]
        s["tts_profiles"] = [{"name": "Old", "provider": "xai", "api_key": SECRETS[1], "voice_id": "v", "model": "", "settings": {"speed": 1.1}}]
        r = svc.call("save_tts", {"profiles": [
            {"src": 0, "name": "Old", "provider": "xai", "key_mode": "keep", "voice_id": "v9", "speed": "1.25", "language": "en"},
            {"src": -1, "name": "New", "provider": "openai", "key_mode": "typed", "api_key": SECRETS[0]},
            {"src": -1, "name": "Vaulted", "provider": "cartesia", "key_mode": "vault", "vault_id": vault_id},
            {"src": -1, "name": "   ", "provider": "xai", "key_mode": "typed", "api_key": "dropped"},
        ]})
        self.assertTrue(r["ok"], r)
        got = s["tts_profiles"]
        self.assertEqual([p["name"] for p in got], ["Old", "New", "Vaulted"])
        self.assertEqual([p["api_key"] for p in got], [SECRETS[1], SECRETS[0], SECRETS[2]])
        self.assertEqual(got[0]["settings"], {"speed": 1.25, "language": "en"})
        self.assertEqual([t["hint"] for t in r["prefs"]["tts"]], [mask_key(SECRETS[1]), mask_key(SECRETS[0]), mask_key(SECRETS[2])])
        for secret in SECRETS:
            self.assertNotIn(secret, repr(r))

    def test_a_saved_list_refreshes_the_catalog_but_a_refused_one_does_not(self):
        svc, s, _, _, hooks, _ = make()
        self.assertTrue(svc.call("save_tts", {"profiles": [{"src": -1, "name": "A", "provider": "xai", "key_mode": "typed", "api_key": "k"}]})["ok"])
        self.assertEqual(hooks.count("catalog"), 1)
        self.assertFalse(svc.call("save_tts", {"profiles": [{"name": "B", "provider": "nope", "key_mode": "typed", "api_key": "k"}]})["ok"])
        self.assertEqual(hooks.count("catalog"), 1)

    def test_validation_leaves_the_stored_profiles_alone(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [{"name": "Keep me", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}}]
        self.assertFalse(svc.call("save_tts", {"profiles": [{"name": "X", "provider": "nope", "key_mode": "typed", "api_key": "k"}]})["ok"])
        self.assertFalse(svc.call("save_tts", {"profiles": [{"name": "X", "provider": "xai", "key_mode": "typed", "api_key": "k", "speed": "fast"}]})["ok"])
        self.assertFalse(svc.call("save_tts", {"profiles": [{"name": "X", "provider": "xai", "key_mode": "vault", "vault_id": "gone"}]})["ok"])
        self.assertEqual([p["name"] for p in s["tts_profiles"]], ["Keep me"])

    def test_detect_and_voices_resolve_a_stored_key_when_none_is_typed(self):
        svc, s, _, _, _, net = make()
        s["tts_profiles"] = [{"name": "N", "provider": "xai", "api_key": SECRETS[1], "voice_id": "", "model": "", "settings": {}}]
        self.assertEqual(svc.call("tts_detect", {"src": 0})["provider"], "cartesia")
        self.assertEqual(net.calls[-1], ("tts_detect", SECRETS[1]))
        r = svc.call("tts_voices", {"provider": "xai", "src": 0})
        self.assertEqual(net.calls[-1], ("voices", "xai", SECRETS[1]))
        self.assertEqual([v["voiceId"] for v in r["voices"]], ["v1", "v2"])
        self.assertFalse(svc.call("tts_voices", {"provider": "elevenlabs", "src": 0})["ok"])
        self.assertFalse(svc.call("tts_voices", {"provider": "xai", "src": 5})["ok"])          # no such profile, no key

    def test_pin_and_unpin(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [
            {"name": "A", "provider": "xai", "api_key": "k", "voice_id": "va", "model": "", "settings": {}},
            {"name": "B", "provider": "xai", "api_key": "k", "voice_id": "vb", "model": "", "settings": {}},
        ]
        r = svc.call("tts_pin", {"name": "B"})
        self.assertTrue(r["ok"], r)
        self.assertEqual(s["active_tts_profile"], "B")
        self.assertEqual(r["prefs"]["activeTtsProfile"], "B")
        r = svc.call("tts_pin", {"name": ""})
        self.assertTrue(r["ok"], r)
        self.assertEqual(s["active_tts_profile"], "")

    def test_pinning_an_unknown_profile_is_refused(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [{"name": "A", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}}]
        r = svc.call("tts_pin", {"name": "Ghost"})
        self.assertFalse(r["ok"])
        self.assertEqual(s.get("active_tts_profile", ""), "")

    def test_save_tts_follows_a_rename_of_the_pinned_profile(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [{"name": "Old Name", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}}]
        s["active_tts_profile"] = "Old Name"
        r = svc.call("save_tts", {"profiles": [
            {"src": 0, "name": "New Name", "provider": "xai", "key_mode": "keep"},
        ]})
        self.assertTrue(r["ok"], r)
        self.assertEqual(s["active_tts_profile"], "New Name")

    def test_save_tts_unpins_when_the_pinned_profile_is_removed(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [
            {"name": "Keep", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}},
            {"name": "Pinned", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}},
        ]
        s["active_tts_profile"] = "Pinned"
        r = svc.call("save_tts", {"profiles": [
            {"src": 0, "name": "Keep", "provider": "xai", "key_mode": "keep"},
        ]})
        self.assertTrue(r["ok"], r)
        self.assertEqual(s["active_tts_profile"], "")

    def test_save_tts_leaves_an_untouched_pin_alone(self):
        svc, s, *_ = make()
        s["tts_profiles"] = [{"name": "A", "provider": "xai", "api_key": "k", "voice_id": "", "model": "", "settings": {}}]
        s["active_tts_profile"] = "A"
        r = svc.call("save_tts", {"profiles": [
            {"src": 0, "name": "A", "provider": "xai", "key_mode": "keep"},
            {"src": -1, "name": "B", "provider": "xai", "key_mode": "typed", "api_key": "k2"},
        ]})
        self.assertTrue(r["ok"], r)
        self.assertEqual(s["active_tts_profile"], "A")


class ThroughTheModel(unittest.TestCase):
    def test_model_owns_a_service_that_mutates_the_shared_settings_in_place(self):
        events: list[dict] = []
        saved: list[dict] = []
        settings = {"listen_port": 1, "bridge_port": 2, "api_key": "", "model": "m", "api_keys": [], "enabled_agents": [], "tools_dir": tempfile.gettempdir()}
        model = SessionModel(settings, [], emit=events.append, save_settings=saved.append)
        self.assertIn("prefs", model.snapshot())
        model.prefs.call("add_key", {"api_key": SECRETS[0], "provider": "openai"})
        self.assertEqual(settings["api_key"], SECRETS[0])                    # same dict object: Genius sees it at once
        self.assertEqual(saved[-1]["api_key"], SECRETS[0])
        self.assertTrue(model.genius.snapshot()["status"]["key"])
        self.assertTrue(any(e.get("op") == "agent" for e in events))          # ...and the chat header was told
        self.assertEqual([e for e in events if e.get("op") == "agent"][-1]["status"], {"key": True})
        model.prefs.call("delete_key", {"id": settings["api_keys"][0]["id"]})
        self.assertEqual([e for e in events if e.get("op") == "agent"][-1]["status"], {"key": False})   # deleting the last key is announced too
        events.clear()
        model.prefs.call("set_path", {"key": "tools_dir", "value": tempfile.gettempdir()})
        self.assertTrue(any(e.get("type") == "patch" and "tools" in e["patch"] for e in events))
        for secret in SECRETS[:1]:
            self.assertNotIn(secret, repr(model.snapshot()))

    def test_demo_is_the_previews_mock_and_read_only(self):
        model = SessionModel({"listen_port": 1, "bridge_port": 2}, [], emit=lambda e: None)
        load_demo_state(model)
        snap = model.snapshot()["prefs"]
        self.assertEqual(len(snap["themes"]), 11)
        self.assertEqual([k["masked"] for k in snap["keys"]], ["xai-••••••••a91f", "sk-••••••••7c2d"])
        r = model.prefs.call("set_ports", {"listen": 1, "bridge": 2})
        self.assertFalse(r["ok"])
        self.assertEqual(model.prefs.call("nope", {})["ok"], False)


class Surface(unittest.TestCase):
    def test_the_page_can_reach_exactly_these_operations(self):
        svc, *_ = make()
        self.assertEqual(sorted(svc.OPS), sorted([
            "set_theme", "set_ports", "set_path", "add_key", "use_key", "delete_key", "set_model", "set_base",
            "use_key_model", "key_models",
            "detect_provider", "list_models", "test_key", "enable_agent", "remove_agent", "agent_tools",
            "set_agent_tool", "set_agent_group", "save_tts", "tts_detect", "tts_voices", "tts_pin", "open_settings_folder",
            # Genius custom instructions. ci_delete is reachable only from here
            # -- the Genius-facing tool has no delete operation at all.
            "ci_create", "ci_update", "ci_delete", "ci_bind"]))
        r = svc.call("__class__", {})
        self.assertFalse(r["ok"])
        self.assertFalse(svc.call("set_ports", {"bogus": 1})["ok"])                # bad arguments are an error, not a crash


if __name__ == "__main__":
    unittest.main()
