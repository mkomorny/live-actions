"""Preferences service for the WebView2 shell -- pure logic, no UI import.

The Tk app's Settings page kept every value in a widget and collected them back on
"Save". Here Python owns the settings dict (the SAME dict object the session model and
the Genius session read, mutated in place), the page is a view of it, and every change is
one small call that validates, persists and returns the new masked snapshot -- so there is
no Save button and nothing to lose by closing the modal.

Secrets
  API keys (the vault, the flat active key, TTS profile keys) never leave Python: the
  snapshot carries a masked hint ("xai-••••••••a91f") and nothing else. Keys travel one
  way only -- from the page's password input into `add_key` / `save_tts` / the probes.

Every operation is `call(op, args)` -> {"ok": bool, "error"?: str, "prefs": <snapshot>, ...}.
The page reaches it through ONE public ShellApi method (`prefs`), so the page-callable
surface stays small and this whitelist (`OPS`) is what test_shell_prefs pins.

Network probes (detect provider, list models, test key, TTS voices) run on the calling
js_api thread with the lock RELEASED, so a 6-60 s probe never stalls the bridge or the chat.
"""

from __future__ import annotations

import copy
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

import agent_registry
import ai_pricing
import custom_instructions
import settings_store

WEB_THEMES_DIR = Path(__file__).resolve().parent / "web" / "css" / "themes"

# Swatch metadata for every design kit (previews/redesign-round/shared/data.js). Only kits whose
# CSS file exists in web/css/themes are OFFERED; adding a kit later = dropping its file in.
KNOWN_THEMES = [
    {"slug": "theatre-lighting-plot", "label": "Theatre Lighting Plot", "bg": "#080A12", "surface": "#141830", "accent": "#F2B872"},
    {"slug": "studio-patchbay", "label": "Studio Patchbay", "bg": "#0E0D0C", "surface": "#1D1B19", "accent": "#F2C14E"},
    {"slug": "risograph-art-studio", "label": "Riso Art Studio", "bg": "#faf5eb", "surface": "#faf5eb", "accent": "#ff3377"},
    {"slug": "max-msp-patcher", "label": "Max/MSP Patcher", "bg": "#A9ACAF", "surface": "#EDEEEF", "accent": "#F1C400"},
    {"slug": "cyber-neon-pink", "label": "Cyber Neon Pink", "bg": "#09090b", "surface": "#27272a", "accent": "#ec4899"},
    {"slug": "charcoal-lime-pastel-cards", "label": "Charcoal Lime Pastel", "bg": "#0e1015", "surface": "#1b1e28", "accent": "#d4f938"},
    {"slug": "charcoal-amber-capsule", "label": "Charcoal Amber Pastel", "bg": "#f4f5f7", "surface": "#ffffff", "accent": "#f59e0b"},
    {"slug": "broadcast-on-air", "label": "Broadcast On Air", "bg": "#141719", "surface": "#22272B", "accent": "#E01B24"},
    {"slug": "aurora-borealis-geomagnetic", "label": "Aurora Borealis", "bg": "#030712", "surface": "#111C38", "accent": "#10B981"},
    {"slug": "amethyst-dusk", "label": "Amethyst Dusk", "bg": "#1e1b4b", "surface": "#3b0764", "accent": "#c084fc"},
    {"slug": "acetate-dubplate", "label": "Acetate Dubplate", "bg": "#0B0B0D", "surface": "#1A1A1D", "accent": "#2F44C4"},
]
DEFAULT_THEME = "risograph-art-studio"

PATH_KEYS = (
    "tools_dir", "knowledge_dir", "music_db_dir", "samples_dir", "plugin_docs_dir",
    "tts_output_dir", "audio_sample_output_dir", "ffmpeg_path",
)
TTS_PROVIDERS = ("xai", "openai", "cartesia")


class PrefsError(Exception):
    """A refusal the page should show next to the control that caused it."""


def mask_key(key: str) -> str:
    """'xai-••••••••a91f' -- enough to recognise a key, never enough to use it."""
    k = str(key or "").strip()
    if not k:
        return ""
    return (k[:4] + "••••••••" + k[-4:]) if len(k) > 10 else "••••••••"


class _Net:
    """The network-touching helpers, imported lazily (they pull in urllib-heavy modules) and
    replaceable in tests."""

    @staticmethod
    def detect_provider(api_key: str) -> tuple[str, str, str]:
        import ai_providers
        return ai_providers.detect_provider(api_key)

    @staticmethod
    def list_models(provider: str, api_key: str, api_base: str) -> list[str]:
        import ai_providers
        return ai_providers.list_models(provider, api_key, api_base)

    @staticmethod
    def probe_model(provider: str, api_key: str, api_base: str, model: str) -> str:
        import ai_providers
        return ai_providers.probe_chat_model(provider, api_key, api_base, model)

    @staticmethod
    def test_key(settings: dict[str, Any]) -> str:
        import genius_client
        return genius_client.test_key(settings)

    @staticmethod
    def tts_detect(api_key: str) -> tuple[str, str]:
        import tts_vocal
        return tts_vocal.detect_provider(api_key)

    @staticmethod
    def tts_voices(provider: str, api_key: str) -> list[dict[str, Any]]:
        import tts_vocal
        return tts_vocal.list_voices(provider, api_key)

    @staticmethod
    def provider_defaults() -> dict[str, str]:
        import ai_providers
        return dict(ai_providers.PROVIDER_DEFAULTS)


class PrefsService:
    def __init__(
        self,
        *,
        lock: threading.RLock,
        settings: dict[str, Any],
        save: Callable[[dict[str, Any]], Any],
        log: Callable[[str], None],
        hooks: dict[str, Callable[..., None]] | None = None,
        net: Any = None,
        themes_dir: Path = WEB_THEMES_DIR,
        open_folder: Callable[[Path], None] | None = None,
    ) -> None:
        self._lock = lock
        self._settings = settings
        self._save = save
        self._log = log
        self._hooks = hooks or {}
        self._net = net or _Net()
        self._themes_dir = themes_dir
        self._open_folder = open_folder or (lambda p: os.startfile(str(p)))   # type: ignore[attr-defined]
        # BridgeClient binds its sockets once at launch, so a port edit only takes effect on restart.
        self._started_ports = (self._int(settings.get("listen_port")), self._int(settings.get("bridge_port")))
        self._demo = False
        # key id -> chat models that key's provider listed; memory only (the chat header's
        # key + model picker). Filled on demand by key_models, never persisted.
        self._models_by_key: dict[str, list[str]] = {}
        # key id -> models that answered 429/503/timeout on the live test: kept (the model works,
        # the provider is busy or the quota is spent), but labelled in the picker.
        self._busy_by_key: dict[str, list[str]] = {}
        # key id -> {model: [input $/1M, output $/1M]} for models ai_pricing recognizes.
        # No provider's /models endpoint returns pricing, so this is a static table lookup,
        # not a live probe; a model ai_pricing doesn't know about is just absent here.
        self._price_by_key: dict[str, dict[str, list[float]]] = {}
        self.OPS: dict[str, Callable[..., dict[str, Any]]] = {
            "set_theme": self.set_theme, "set_ports": self.set_ports, "set_path": self.set_path,
            "add_key": self.add_key, "use_key": self.use_key, "delete_key": self.delete_key,
            "set_model": self.set_model, "set_base": self.set_base,
            "use_key_model": self.use_key_model, "key_models": self.key_models,
            "detect_provider": self.detect_provider, "list_models": self.list_models, "test_key": self.test_key,
            "enable_agent": self.enable_agent, "remove_agent": self.remove_agent, "agent_tools": self.agent_tools,
            "set_agent_tool": self.set_agent_tool, "set_agent_group": self.set_agent_group,
            "save_tts": self.save_tts, "tts_detect": self.tts_detect, "tts_voices": self.tts_voices,
            "tts_pin": self.tts_pin,
            "open_settings_folder": self.open_settings_folder,
            # Genius custom instructions. Note delete lives here and only here:
            # the Preferences UI can remove a preset, Genius cannot.
            "ci_create": self.ci_create, "ci_update": self.ci_update,
            "ci_delete": self.ci_delete, "ci_bind": self.ci_bind,
        }

    # -- plumbing ---------------------------------------------------------------

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def call(self, op: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        fn = self.OPS.get(str(op))
        if fn is None:
            return {"ok": False, "error": "Unknown preferences operation.", "prefs": self.snapshot()}
        if self._demo:
            return {"ok": False, "error": "Preferences are read-only in the demo state.", "prefs": self.snapshot()}
        try:
            extra = fn(**(args if isinstance(args, dict) else {}))
        except PrefsError as exc:
            return {"ok": False, "error": str(exc), "prefs": self.snapshot()}
        except TypeError as exc:
            return {"ok": False, "error": "Bad arguments: %s" % exc, "prefs": self.snapshot()}
        out: dict[str, Any] = {"ok": True}
        out.update(extra or {})
        out["prefs"] = self.snapshot()
        return out

    def _commit(self, mutate: Callable[[dict[str, Any]], None]) -> None:
        """Apply `mutate` to a copy, persist the copy, and only then adopt it in place. A failed
        write therefore leaves the running settings exactly as they were."""
        with self._lock:
            new = copy.deepcopy(self._settings)
            mutate(new)
            try:
                self._save(new)
            except OSError as exc:
                raise PrefsError("Could not save settings: %s" % exc)
            self._settings.clear()
            self._settings.update(new)

    def _hook(self, name: str) -> None:
        fn = self._hooks.get(name)
        if fn is not None:
            try:
                fn()
            except Exception as exc:                       # a refresh failing must not fail the save
                self._log("Preferences: %s refresh failed: %s" % (name, exc))

    # -- snapshot ---------------------------------------------------------------

    def themes(self) -> list[dict[str, str]]:
        return [t for t in KNOWN_THEMES if (self._themes_dir / (t["slug"] + ".css")).is_file()]

    def _agent_maps(self, s: dict[str, Any], slug: str) -> tuple[dict[str, Any] | None, dict[str, bool]]:
        agent = agent_registry.load_agent(s, slug)
        if agent is None:
            return None, {}
        default = agent_registry.default_tool_map(agent)
        stored = (s.get("agent_tool_prefs") or {}).get(slug)
        stored = stored if isinstance(stored, dict) else {}
        return agent, {n: bool(stored.get(n, on)) for n, on in default.items()}

    def snapshot(self) -> dict[str, Any]:
        if self._demo:
            return copy.deepcopy(DEMO_PREFS)
        with self._lock:
            s = self._settings
            active_id = str(s.get("active_api_key_id") or "")
            keys = [
                {
                    "id": str(k.get("id") or ""), "label": str(k.get("label") or ""), "provider": str(k.get("provider") or ""),
                    "model": str(k.get("model") or ""), "apiBase": str(k.get("api_base") or ""), "masked": mask_key(k.get("api_key")),
                }
                for k in (s.get("api_keys") or []) if isinstance(k, dict)
            ]
            active = next((k for k in (s.get("api_keys") or []) if isinstance(k, dict) and k.get("id") == active_id), {})
            enabled: list[dict[str, Any]] = []
            for slug in list(s.get("enabled_agents") or []):
                agent, tools = self._agent_maps(s, slug)
                if agent is not None:
                    enabled.append({"slug": slug, "title": str(agent["title"]), "on": sum(tools.values()), "total": len(tools)})
            taken = {e["slug"] for e in enabled} | set(s.get("enabled_agents") or [])
            available = [{"slug": a["slug"], "title": str(a["title"])} for a in agent_registry.list_agents(s) if a["slug"] not in taken]
            themes = self.themes()
            cur = str(s.get("theme") or DEFAULT_THEME)
            return {
                "theme": cur,
                "themes": themes,
                "ports": {"listen": self._int(s.get("listen_port")), "bridge": self._int(s.get("bridge_port"))},
                "portDefaults": {"listen": settings_store.DEFAULTS["listen_port"], "bridge": settings_store.DEFAULTS["bridge_port"]},
                "restart": (self._int(s.get("listen_port")), self._int(s.get("bridge_port"))) != self._started_ports,
                "keys": keys,
                "activeKeyId": active_id,
                "modelsByKey": {k: list(v) for k, v in self._models_by_key.items()},
                "busyByKey": {k: list(v) for k, v in self._busy_by_key.items()},
                "priceByKey": {k: {m: list(p) for m, p in v.items()} for k, v in self._price_by_key.items()},
                "model": str(s.get("model") or ""),
                "apiBase": str(s.get("api_base") or ""),
                "provider": str(active.get("provider") or ""),
                "hasKey": bool(str(s.get("api_key") or "").strip()),
                "agents": {"enabled": enabled, "available": available},
                "paths": {k: str(s.get(k) or "") for k in PATH_KEYS},
                "tts": [
                    {
                        "src": i, "name": str(p.get("name") or ""), "provider": str(p.get("provider") or "xai"),
                        "hint": mask_key(p.get("api_key")), "voiceId": str(p.get("voice_id") or ""), "model": str(p.get("model") or ""),
                        "speed": str((p.get("settings") or {}).get("speed") or ""), "language": str((p.get("settings") or {}).get("language") or ""),
                    }
                    for i, p in enumerate(s.get("tts_profiles") or []) if isinstance(p, dict)
                ],
                "activeTtsProfile": str(s.get("active_tts_profile") or ""),
                "settingsFolder": str(settings_store.APP_DATA),
                "customInstructions": {
                    "presets": [
                        {"id": p["id"], "name": p["name"], "body": p["body"]}
                        for p in custom_instructions.list_presets(s)
                    ],
                    # The Genius page's dropdown needs to show which preset is
                    # live for the Set that is actually open, not just the list.
                    "setName": self._live_set_name(),
                    "activeId": custom_instructions.active_preset_id(s, self._live_set_name()),
                },
            }

    # -- Genius custom instructions ---------------------------------------------

    @staticmethod
    def _live_set_name() -> str:
        """Name of the Live Set currently open, or "" when Live hasn't said.

        Read from genius_client rather than stored here: it is the module both
        front-ends already report the Set name to, so there is one source of
        truth. Imported lazily and guarded so Preferences still opens if the
        Genius import chain is unavailable (e.g. in a bare unit test).
        """
        try:
            import genius_client

            return genius_client.current_live_set()
        except Exception:
            return ""

    def ci_create(self, name: str = "", body: str = "") -> dict[str, Any]:
        created: dict[str, Any] = {}

        def mutate(s: dict[str, Any]) -> None:
            created.update(custom_instructions.create_preset(s, name, body))

        try:
            self._commit(mutate)
        except ValueError as exc:
            raise PrefsError(str(exc))
        return {"createdId": created.get("id", "")}

    def ci_update(self, id: str = "", name: str | None = None, body: str | None = None) -> dict[str, Any]:
        def mutate(s: dict[str, Any]) -> None:
            custom_instructions.update_preset(s, id, name=name, body=body)

        try:
            self._commit(mutate)
        except ValueError as exc:
            raise PrefsError(str(exc))
        return {}

    def ci_delete(self, id: str = "") -> dict[str, Any]:
        removed: list[bool] = []

        def mutate(s: dict[str, Any]) -> None:
            removed.append(custom_instructions.delete_preset(s, id))

        self._commit(mutate)
        if not (removed and removed[0]):
            raise PrefsError("No such custom-instruction preset.")
        return {}

    def ci_bind(self, id: str = "", setName: str | None = None) -> dict[str, Any]:
        """Bind a preset to a Live Set. Empty id unbinds."""
        target = setName if setName is not None else self._live_set_name()

        def mutate(s: dict[str, Any]) -> None:
            custom_instructions.bind(s, target, str(id or ""))

        try:
            self._commit(mutate)
        except ValueError as exc:
            raise PrefsError(str(exc))
        return {"boundTo": target}

    # -- appearance / connection / folders ------------------------------------------

    def set_theme(self, slug: str) -> dict[str, Any]:
        slug = str(slug or "")
        if slug not in {t["slug"] for t in self.themes()}:
            raise PrefsError("That theme is not installed.")
        self._commit(lambda s: s.__setitem__("theme", slug))
        return {}

    def set_ports(self, listen: Any, bridge: Any) -> dict[str, Any]:
        try:
            lp, bp = int(str(listen).strip()), int(str(bridge).strip())
        except ValueError:
            raise PrefsError("Ports must be whole numbers.")
        for p in (lp, bp):
            if not 1 <= p <= 65535:
                raise PrefsError("Ports must be between 1 and 65535.")
        if lp == bp:
            raise PrefsError("The listen and send ports must be different.")
        self._commit(lambda s: s.update(listen_port=lp, bridge_port=bp))
        self._log("Ports saved (%d / %d). Restart Live Actions to apply." % (lp, bp))
        return {}

    def set_path(self, key: str, value: str) -> dict[str, Any]:
        if key not in PATH_KEYS:
            raise PrefsError("Unknown setting.")
        value = str(value or "").strip()
        self._commit(lambda s: s.__setitem__(key, value))
        note = ""
        if value and key != "ffmpeg_path" and not os.path.exists(value):
            note = "Saved, but that path does not exist right now."
        if key == "tools_dir":
            self._hook("tools")
        return {"note": note}

    # -- API keys ----------------------------------------------------------------------

    @staticmethod
    def _activate(s: dict[str, Any], entry: dict[str, Any], defaults: dict[str, str]) -> None:
        s["active_api_key_id"] = entry.get("id", "")
        s["api_key"] = str(entry.get("api_key") or "")
        s["api_base"] = str(entry.get("api_base") or defaults.get(str(entry.get("provider") or ""), "") or settings_store.DEFAULTS["api_base"])
        if entry.get("model"):
            s["model"] = str(entry["model"])

    def add_key(self, api_key: str, label: str = "", provider: str = "", api_base: str = "", model: str = "") -> dict[str, Any]:
        api_key = str(api_key or "").strip()
        if not api_key:
            raise PrefsError("Paste an API key first.")
        defaults = self._net.provider_defaults()
        provider = str(provider or "").strip()
        result: dict[str, Any] = {}

        def mutate(s: dict[str, Any]) -> None:
            keys = list(s.get("api_keys") or [])
            entry = next((k for k in keys if k.get("api_key") == api_key), None)
            base = str(api_base or "").strip() or defaults.get(provider, "") or str(s.get("api_base") or settings_store.DEFAULTS["api_base"])
            if entry is None:
                entry = {"id": "k_" + uuid.uuid4().hex[:10], "label": "", "provider": provider, "api_key": api_key, "api_base": base, "model": ""}
                keys.append(entry)
            entry["label"] = str(label or "").strip() or entry.get("label") or ("Key %d" % len(keys))
            entry["provider"] = provider or entry.get("provider", "")
            entry["api_base"] = base
            entry["model"] = str(model or "").strip() or entry.get("model") or str(s.get("model") or "")
            s["api_keys"] = keys
            self._activate(s, entry, defaults)
            result["label"] = entry["label"]

        self._commit(mutate)
        self._log("Saved key '%s'." % result["label"])
        self._hook("genius")
        return {}

    def use_key(self, id: str) -> dict[str, Any]:
        defaults = self._net.provider_defaults()
        found: dict[str, Any] = {}

        def mutate(s: dict[str, Any]) -> None:
            entry = next((k for k in (s.get("api_keys") or []) if k.get("id") == id), None)
            if entry is None:
                raise PrefsError("That key is no longer saved.")
            self._activate(s, entry, defaults)
            found.update(entry)

        self._commit(mutate)
        self._log("Using saved key '%s'." % found.get("label"))
        self._hook("genius")
        return {}

    def delete_key(self, id: str) -> dict[str, Any]:
        def mutate(s: dict[str, Any]) -> None:
            keys = list(s.get("api_keys") or [])
            gone = next((k for k in keys if k.get("id") == id), None)
            if gone is None:
                return
            s["api_keys"] = [k for k in keys if k.get("id") != id]
            if s.get("active_api_key_id") == id:
                s["active_api_key_id"] = ""
                # Deleting the key you are using must actually stop using it (the Tk page left the
                # deleted key active in the flat field).
                if s.get("api_key") == gone.get("api_key"):
                    s["api_key"] = ""

        self._commit(mutate)
        self._hook("genius")
        return {}

    def use_key_model(self, id: str, model: str) -> dict[str, Any]:
        """The chat header's picker: switch key AND model in one save (use_key then set_model would
        save twice and reload Genius twice, briefly pairing the new key with the old model)."""
        model = str(model or "").strip()
        if not model:
            raise PrefsError("Pick a model.")
        defaults = self._net.provider_defaults()
        found: dict[str, Any] = {}

        def mutate(s: dict[str, Any]) -> None:
            entry = next((k for k in (s.get("api_keys") or []) if k.get("id") == id), None)
            if entry is None:
                raise PrefsError("That key is no longer saved.")
            entry["model"] = model
            base = self._endpoint_for(entry, model, defaults)
            if base:
                entry["api_base"] = base
            self._activate(s, entry, defaults)
            found.update(entry)

        self._commit(mutate)
        self._log("Using '%s' with %s." % (found.get("label"), model))
        self._hook("genius")
        notice = self._hooks.get("notice")
        if notice is not None:
            try:
                notice("Now using %s · %s" % (found.get("label"), model))
            except Exception as exc:
                self._log("Preferences: notice failed: %s" % exc)
        return {"label": str(found.get("label") or ""), "model": model}

    def key_models(self, id: str) -> dict[str, Any]:
        """List one saved key's chat models for the header picker. The key itself stays in Python;
        the result is cached in memory so the picker does not hit the network on every render."""
        with self._lock:
            entry = next((dict(k) for k in (self._settings.get("api_keys") or []) if k.get("id") == id), None)
        if entry is None:
            raise PrefsError("That key is no longer saved.")
        key = str(entry.get("api_key") or "").strip()
        if not key:
            raise PrefsError("That saved key is empty.")
        provider, base = str(entry.get("provider") or ""), str(entry.get("api_base") or "")
        models, busy = self._working_models(provider, key, base, str(entry.get("label") or id))
        pricing = ai_pricing.pricing_for_models(provider, models)
        with self._lock:
            self._models_by_key[str(id)] = models
            self._busy_by_key[str(id)] = busy
            self._price_by_key[str(id)] = pricing
        return {"models": models, "busy": busy, "pricing": pricing}

    _PROBE_WORKERS = 4

    def _working_models(self, provider: str, key: str, base: str, label: str) -> tuple[list[str], list[str]]:
        """The provider's chat-model list, then one tiny tool-enabled request per model: only models
        that answer (or are merely busy) are kept. Runs with the lock released -- a probe per model."""
        listed = list(self._net.list_models(provider, key, base))
        if not listed:
            return [], []
        from concurrent.futures import ThreadPoolExecutor

        def probe(m: str) -> str:
            try:
                return self._net.probe_model(provider, key, base, m)
            except Exception:
                return "broken"

        with ThreadPoolExecutor(max_workers=self._PROBE_WORKERS) as pool:
            verdicts = list(pool.map(probe, listed))
        ok = [m for m, v in zip(listed, verdicts) if v in ("ok", "busy")]
        busy = [m for m, v in zip(listed, verdicts) if v == "busy"]
        dropped = len(listed) - len(ok)
        self._log("%s: %d working model(s)%s%s." % (
            label, len(ok), (", %d busy right now" % len(busy)) if busy else "",
            (", %d hidden (no access or no tool calling)" % dropped) if dropped else ""))
        return ok, busy

    def _set_active_field(self, field: str, entry_field: str, value: str) -> None:
        value = str(value or "").strip()

        def mutate(s: dict[str, Any]) -> None:
            s[field] = value
            for k in (s.get("api_keys") or []):
                if k.get("id") == s.get("active_api_key_id"):
                    k[entry_field] = value

        self._commit(mutate)
        self._hook("genius")

    def _endpoint_for(self, entry: dict[str, Any], model: str, defaults: dict[str, str]) -> str:
        """The endpoint a TESTED model needs: its provider's chat base. Only for models the live test
        passed for this key, so a hand-typed model on a custom endpoint (a proxy, a local server)
        keeps the endpoint the user set. "" = leave the endpoint alone."""
        with self._lock:
            tested = model in self._models_by_key.get(str(entry.get("id") or ""), [])
        return defaults.get(str(entry.get("provider") or ""), "") if tested else ""

    def set_model(self, model: str) -> dict[str, Any]:
        model = str(model or "").strip()
        defaults = self._net.provider_defaults()

        def mutate(s: dict[str, Any]) -> None:
            s["model"] = model
            for k in (s.get("api_keys") or []):
                if k.get("id") == s.get("active_api_key_id"):
                    k["model"] = model
                    base = self._endpoint_for(k, model, defaults)
                    if base:
                        k["api_base"] = s["api_base"] = base

        self._commit(mutate)
        self._hook("genius")
        return {}

    def set_base(self, api_base: str) -> dict[str, Any]:
        value = str(api_base or "").strip()
        if value and not value.lower().startswith(("http://", "https://")):
            raise PrefsError("The endpoint must start with http:// or https://.")
        self._set_active_field("api_base", "api_base", value or settings_store.DEFAULTS["api_base"])
        return {}

    def _key_for_probe(self, typed: str) -> str:
        typed = str(typed or "").strip()
        if typed:
            return typed
        with self._lock:
            return str(self._settings.get("api_key") or "").strip()

    def detect_provider(self, api_key: str = "") -> dict[str, Any]:
        key = self._key_for_probe(api_key)
        if not key:
            raise PrefsError("Paste an API key first.")
        self._log("Detecting provider…")
        provider, base, message = self._net.detect_provider(key)
        self._log(message)
        return {"provider": provider, "apiBase": base, "message": message}

    def list_models(self, api_key: str = "", provider: str = "", api_base: str = "") -> dict[str, Any]:
        key = self._key_for_probe(api_key)
        if not key:
            raise PrefsError("Add an API key first.")
        with self._lock:
            active = next((k for k in (self._settings.get("api_keys") or []) if k.get("id") == self._settings.get("active_api_key_id")), {})
            provider = str(provider or active.get("provider") or "")
            api_base = str(api_base or self._settings.get("api_base") or "")
        self._log("Fetching and testing models…")
        models, busy = self._working_models(provider, key, api_base, provider or "Key")
        pricing = ai_pricing.pricing_for_models(provider, models)
        if not models:
            self._log("No working models — check the key/provider.")
        elif not str(api_key or "").strip():
            with self._lock:
                active_id = str(self._settings.get("active_api_key_id") or "")
                if active_id:
                    self._models_by_key[active_id] = list(models)
                    self._busy_by_key[active_id] = list(busy)
                    self._price_by_key[active_id] = pricing
        return {"models": list(models), "busy": list(busy), "pricing": pricing}

    def test_key(self, api_key: str = "") -> dict[str, Any]:
        typed = str(api_key or "").strip()
        with self._lock:
            probe = {k: self._settings.get(k) for k in ("api_key", "api_base", "model")}
            active = next((k for k in (self._settings.get("api_keys") or []) if k.get("id") == self._settings.get("active_api_key_id")), {})
            probe["provider"] = active.get("provider", "")
        if typed:
            probe["api_key"] = typed
        try:
            text = self._net.test_key(probe)
        except Exception as exc:
            self._log("Key test failed: %s" % exc)
            return {"test": {"ok": False, "message": str(exc)[:400]}}
        self._log("Key test succeeded.")
        return {"test": {"ok": True, "message": str(text)[:400]}}

    # -- agents ----------------------------------------------------------------------------

    def enable_agent(self, slug: str) -> dict[str, Any]:
        def mutate(s: dict[str, Any]) -> None:
            agent = agent_registry.load_agent(s, slug)
            if agent is None:
                raise PrefsError("That agent no longer exists.")
            enabled = list(s.get("enabled_agents") or [])
            if slug in enabled:
                return
            enabled.append(slug)
            s["enabled_agents"] = enabled
            prefs = dict(s.get("agent_tool_prefs") or {})
            prefs[slug] = agent_registry.default_tool_map(agent)
            s["agent_tool_prefs"] = prefs

        self._commit(mutate)
        self._hook("genius")
        return {}

    def remove_agent(self, slug: str) -> dict[str, Any]:
        def mutate(s: dict[str, Any]) -> None:
            s["enabled_agents"] = [a for a in (s.get("enabled_agents") or []) if a != slug]
            prefs = dict(s.get("agent_tool_prefs") or {})
            prefs.pop(slug, None)
            s["agent_tool_prefs"] = prefs
            if s.get("active_agent") == slug:
                s["active_agent"] = ""

        self._commit(mutate)
        self._hook("genius")
        return {}

    def _groups(self, tools: dict[str, bool]) -> list[dict[str, Any]]:
        return [
            {"name": group, "tools": [{"name": n, "on": tools[n]} for n in names if n in tools]}
            for group, names in agent_registry.TOOL_GROUPS.items()
            if any(n in tools for n in names)
        ]

    def agent_tools(self, slug: str) -> dict[str, Any]:
        with self._lock:
            agent, tools = self._agent_maps(self._settings, slug)
        if agent is None:
            raise PrefsError("That agent no longer exists.")
        return {"slug": slug, "groups": self._groups(tools)}

    def _set_tools(self, slug: str, names: list[str], on: bool) -> dict[str, Any]:
        bad = [n for n in names if n not in agent_registry.ALL_TOOL_NAMES]
        if bad:
            raise PrefsError("Unknown tool: %s" % bad[0])

        def mutate(s: dict[str, Any]) -> None:
            if slug not in (s.get("enabled_agents") or []):
                raise PrefsError("That agent is not enabled.")
            prefs = dict(s.get("agent_tool_prefs") or {})
            agent_map = dict(prefs.get(slug) or {})
            for n in names:
                agent_map[n] = bool(on)
            prefs[slug] = agent_map
            s["agent_tool_prefs"] = prefs

        self._commit(mutate)
        return self.agent_tools(slug)

    def set_agent_tool(self, slug: str, name: str, on: bool) -> dict[str, Any]:
        return self._set_tools(slug, [str(name)], bool(on))

    def set_agent_group(self, slug: str, group: str, on: bool) -> dict[str, Any]:
        names = list(agent_registry.TOOL_GROUPS.get(str(group), ()))
        if not names:
            raise PrefsError("Unknown tool group.")
        return self._set_tools(slug, names, bool(on))

    # -- TTS profiles --------------------------------------------------------------------------

    def _tts_key(self, src: Any, typed: str) -> str:
        typed = str(typed or "").strip()
        if typed:
            return typed
        with self._lock:
            profiles = self._settings.get("tts_profiles") or []
            try:
                return str(profiles[int(src)].get("api_key") or "").strip()
            except (TypeError, ValueError, IndexError, AttributeError):
                return ""

    def save_tts(self, profiles: list[dict[str, Any]]) -> dict[str, Any]:
        """`profiles` is the page's whole working list. An entry keeps its stored key ("keep", by
        the index it came from), takes a newly typed one ("typed"), or copies one from the vault."""
        if not isinstance(profiles, list):
            raise PrefsError("Bad profile list.")

        def mutate(s: dict[str, Any]) -> None:
            old = s.get("tts_profiles") or []
            old_pin = str(s.get("active_tts_profile") or "").strip()
            vault = {k.get("id"): k for k in (s.get("api_keys") or [])}
            out: list[dict[str, Any]] = []
            renamed_pin: str | None = None            # the pinned profile's name under the new list, if it moved
            for p in profiles:
                name = str(p.get("name") or "").strip()
                if not name:
                    continue                                   # a blank row is not a profile (as in Tk)
                provider = str(p.get("provider") or "xai").strip()
                if provider not in TTS_PROVIDERS:
                    raise PrefsError("Unknown TTS provider: %s" % provider)
                mode = str(p.get("key_mode") or "keep")
                src = p.get("src")
                if mode == "typed":
                    key = str(p.get("api_key") or "").strip()
                elif mode == "vault":
                    entry = vault.get(p.get("vault_id"))
                    if entry is None:
                        raise PrefsError("That saved key is no longer available.")
                    key = str(entry.get("api_key") or "")
                else:
                    try:
                        key = str(old[int(src)].get("api_key") or "")
                    except (TypeError, ValueError, IndexError, AttributeError):
                        key = ""
                # Track a rename of the currently-pinned profile by its old list position,
                # so pinning survives a typo fix instead of silently dropping. `src` is -1
                # for a brand-new row -- must be checked as a real index, not just caught,
                # since Python's own negative-index wraparound would otherwise match a new
                # row's src=-1 against old's LAST entry.
                if old_pin:
                    try:
                        src_i = int(src)
                    except (TypeError, ValueError):
                        src_i = -1
                    if 0 <= src_i < len(old) and str(old[src_i].get("name") or "") == old_pin:
                        renamed_pin = name
                prof: dict[str, Any] = {
                    "name": name, "provider": provider, "api_key": key,
                    "voice_id": str(p.get("voice_id") or "").strip(), "model": str(p.get("model") or "").strip(), "settings": {},
                }
                speed = str(p.get("speed") or "").strip()
                if speed:
                    try:
                        prof["settings"]["speed"] = float(speed)
                    except ValueError:
                        raise PrefsError("Speed for '%s' must be a number." % name)
                language = str(p.get("language") or "").strip()
                if language:
                    prof["settings"]["language"] = language
                out.append(prof)
            s["tts_profiles"] = out
            if old_pin:
                if renamed_pin is not None:
                    s["active_tts_profile"] = renamed_pin
                elif not any(pr["name"] == old_pin for pr in out):
                    s["active_tts_profile"] = ""       # the pinned profile was removed -- unpin, don't dangle

        self._commit(mutate)
        self._hook("catalog")          # the TTS Vocal tool's Profile dropdown is built from these
        return {}

    def tts_pin(self, name: str = "") -> dict[str, Any]:
        """Pin one saved profile as the only voice every generation may use, or unpin
        with an empty name. Enforced in tts_vocal._pick_profile / _apply_overrides and
        genius_client._resolve_tts_profile -- this just records which one."""
        name = str(name or "").strip()

        def mutate(s: dict[str, Any]) -> None:
            if name and not any(
                str(p.get("name") or "") == name for p in (s.get("tts_profiles") or []) if isinstance(p, dict)
            ):
                raise PrefsError("That TTS profile no longer exists.")
            s["active_tts_profile"] = name

        self._commit(mutate)
        self._hook("catalog")          # withheld profiles/behaviour depend on the pin too
        return {}

    def tts_detect(self, src: Any = -1, api_key: str = "") -> dict[str, Any]:
        key = self._tts_key(src, api_key)
        if not key:
            raise PrefsError("Paste an API key for this profile first.")
        self._log("Detecting provider…")
        provider, message = self._net.tts_detect(key)
        self._log(message)
        return {"provider": provider, "message": message}

    def tts_voices(self, provider: str, src: Any = -1, api_key: str = "") -> dict[str, Any]:
        provider = str(provider or "").strip()
        key = self._tts_key(src, api_key)
        if provider not in TTS_PROVIDERS:
            raise PrefsError("No voice list is available for '%s'." % provider)
        if not key:
            raise PrefsError("This profile needs an API key first.")
        self._log("Fetching voices for %s…" % provider)
        voices = self._net.tts_voices(provider, key)
        self._log("Found %d voice(s) for %s (%d custom)." % (len(voices), provider, sum(1 for v in voices if v.get("custom"))))
        return {"voices": [{"voiceId": v["voice_id"], "name": v["name"], "custom": bool(v.get("custom"))} for v in voices]}

    # -- misc -----------------------------------------------------------------------------------

    def open_settings_folder(self) -> dict[str, Any]:
        settings_store.APP_DATA.mkdir(parents=True, exist_ok=True)
        try:
            self._open_folder(settings_store.APP_DATA)
        except OSError as exc:
            raise PrefsError("Could not open the folder: %s" % exc)
        return {}

    def load_demo(self) -> None:
        self._demo = True


# The preview's mock Preferences content (previews/redesign-round/shared/shared.js settingsBody), so the
# real modal can be pixel-compared with shots/extra__a-settings*.png. Demo state only; read-only.
DEMO_PREFS: dict[str, Any] = {
    "theme": DEFAULT_THEME,
    "themes": KNOWN_THEMES,
    "ports": {"listen": 11925, "bridge": 11924},
    "portDefaults": {"listen": 11925, "bridge": 11924},
    "restart": False,
    "keys": [
        {"id": "demo-xai", "label": "xAI · Main key", "provider": "xai", "model": "grok-4.6", "apiBase": "", "masked": "xai-••••••••a91f"},
        {"id": "demo-openai", "label": "OpenAI · Backup", "provider": "openai", "model": "gpt-5", "apiBase": "", "masked": "sk-••••••••7c2d"},
    ],
    "activeKeyId": "demo-xai",
    "model": "grok-4.6",
    "apiBase": "https://api.x.ai/v1",
    "provider": "xai",
    "hasKey": True,
    "agents": {"enabled": [{"slug": "drum-doctor", "title": "Drum Doctor", "on": 7, "total": 14}], "available": []},
    "paths": {
        "tools_dir": "…\\Live Actions\\tools", "knowledge_dir": "…\\Live Actions\\knowledge", "music_db_dir": "",
        "samples_dir": "", "tts_output_dir": "", "audio_sample_output_dir": "", "ffmpeg_path": "",
    },
    "tts": [],
    "settingsFolder": "",
    "customInstructions": {
        "presets": [
            {"id": "demo-ci", "name": "Concise answers", "body": "Keep replies under 120 words.\nLead with the action, not the theory."},
        ],
        "setName": "Neon Nights 128.als",
        "activeId": "demo-ci",
    },
}
