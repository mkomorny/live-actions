"""Tests for engine E2: the RemoteScriptClient TCP client and the browser
logic inside remote_script/LiveActionsRS/__init__.py.

Two halves, for two different reasons:

1. RemoteScriptClient is exercised against a real loopback TCP server that
   speaks the same newline-JSON framing LiveActionsRS does. That covers the
   reconnect-once behaviour, which is the part most likely to regress and the
   part that decides whether a user sees "engine offline" spuriously.

2. LiveActionsRS itself cannot normally be imported outside Live -- it does
   `from _Framework.ControlSurface import ControlSurface`, which only exists
   inside Live's Python. Rather than leave the browser-walking logic untested
   until someone has Live open, a stub _Framework is injected into sys.modules
   and the real module is loaded against fake BrowserItem objects. That is what
   lets path resolution, the folder cache and the search bounds be verified
   offline. Same spirit as test_osc_chunking.py mirroring the JS chunker.

Run from app\\:  python -m unittest test_remote_script_client
"""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
import threading
import types
import unittest
import unittest.mock
from pathlib import Path

import remote_script_client
from remote_script_client import RemoteScriptClient


# ── half 1: the TCP client ─────────────────────────────────────────────────

class _FakeEngine:
    """Minimal newline-JSON TCP server standing in for LiveActionsRS."""

    def __init__(self, handler=None, drop_after: int | None = None, raw_reply: bytes | None = None) -> None:
        self.handler = handler or (lambda action, params: {"ok": True, "action": action})
        self.drop_after = drop_after
        self.raw_reply = raw_reply
        self.requests: list[dict] = []
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(4)
        self._sock.settimeout(0.5)
        self.port = self._sock.getsockname()[1]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                client, _ = self._sock.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._client, args=(client,), daemon=True).start()

    def _client(self, client: socket.socket) -> None:
        served = 0
        buf = b""
        client.settimeout(2.0)
        try:
            while not self._stop.is_set():
                try:
                    chunk = client.recv(65536)
                except (socket.timeout, OSError):
                    break
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    if self.drop_after is not None and served >= self.drop_after:
                        client.close()
                        return
                    if self.raw_reply is not None:
                        client.sendall(self.raw_reply)
                        served += 1
                        continue
                    req = json.loads(line.decode("utf-8"))
                    self.requests.append(req)
                    reply = self.handler(req.get("action"), req.get("params") or {})
                    if isinstance(reply, dict) and req.get("id") is not None:
                        reply = dict(reply, id=req["id"])
                    client.sendall(json.dumps(reply).encode("utf-8") + b"\n")
                    served += 1
        finally:
            try:
                client.close()
            except OSError:
                pass

    def close(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass


class RemoteScriptClientTest(unittest.TestCase):
    def tearDown(self) -> None:
        for engine in getattr(self, "_engines", []):
            engine.close()

    def _engine(self, **kw) -> _FakeEngine:
        engine = _FakeEngine(**kw)
        self._engines = getattr(self, "_engines", [])
        self._engines.append(engine)
        return engine

    def test_call_round_trips_and_marks_online(self) -> None:
        engine = self._engine(handler=lambda a, p: {"ok": True, "echo": p})
        client = RemoteScriptClient(engine.port)
        self.assertFalse(client.online())

        res = client.call("browse", {"category": "instruments"})
        self.assertTrue(res["ok"])
        self.assertEqual(res["echo"], {"category": "instruments"})
        self.assertTrue(client.online())
        self.assertEqual(engine.requests[0]["action"], "browse")
        client.close()

    def test_offline_engine_returns_actionable_error_not_exception(self) -> None:
        # A port nothing is listening on is the everyday case: the user has not
        # enabled the Control Surface yet. It must not raise.
        client = RemoteScriptClient(59999)
        res = client.call("ping")
        self.assertFalse(res["ok"])
        self.assertIn("LiveActionsRS", res["error"])
        self.assertIn("Control Surface", res["error"])
        self.assertFalse(client.online())

    def test_reconnects_once_after_engine_drops_idle_socket(self) -> None:
        # Live dropping a socket that has been idle since the last call must not
        # surface as "engine offline" -- the client gets exactly one retry.
        engine = self._engine(drop_after=1)
        client = RemoteScriptClient(engine.port)
        self.assertTrue(client.call("ping")["ok"])
        self.assertTrue(client.call("ping")["ok"])
        client.close()

    def test_request_ids_increment_so_replies_are_attributable(self) -> None:
        engine = self._engine()
        client = RemoteScriptClient(engine.port)
        client.call("ping")
        client.call("browse")
        self.assertEqual([r["id"] for r in engine.requests], [1, 2])
        client.close()

    def test_malformed_reply_is_reported_not_raised(self) -> None:
        engine = self._engine(raw_reply=b"this is not json\n")
        client = RemoteScriptClient(engine.port)
        res = client.call("ping")
        self.assertFalse(res["ok"])
        self.assertIn("Invalid JSON", res["error"])
        # A garbled reply must not be mistaken for a healthy engine.
        self.assertFalse(client.online())
        client.close()

    def test_online_window_expires(self) -> None:
        engine = self._engine()
        client = RemoteScriptClient(engine.port)
        client.call("ping")
        self.assertTrue(client.online())
        client.last_pong -= remote_script_client.ONLINE_WINDOW_S + 1
        self.assertFalse(client.online())
        client.close()


# ── half 2: the Remote Script's browser logic, offline ─────────────────────

class _FakeItem:
    """Stand-in for Live's BrowserItem."""

    def __init__(self, name, children=None, loadable=False, device=False, uri=None):
        self.name = name
        self.children = children or []
        self.is_folder = bool(children)
        self.is_device = device
        self.is_loadable = loadable
        self.uri = uri or ("query:%s" % name.replace(" ", "%20"))


def _load_live_actions_rs():
    """Import the Remote Script with a stub _Framework in place."""
    framework = types.ModuleType("_Framework")
    cs_mod = types.ModuleType("_Framework.ControlSurface")

    class _StubControlSurface:
        def __init__(self, c_instance=None):
            pass

        def log_message(self, *a, **k):
            pass

        def show_message(self, *a, **k):
            pass

        def schedule_message(self, _delay, fn):
            fn()

        def disconnect(self):
            pass

    cs_mod.ControlSurface = _StubControlSurface
    framework.ControlSurface = cs_mod
    sys.modules.setdefault("_Framework", framework)
    sys.modules.setdefault("_Framework.ControlSurface", cs_mod)

    path = Path(__file__).resolve().parent.parent / "remote_script" / "LiveActionsRS" / "__init__.py"
    spec = importlib.util.spec_from_file_location("live_actions_rs_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Harness:
    """A LiveActionsRS with the socket server and Live objects stubbed out, so
    only the browser logic under test is real."""

    def __init__(self, rs_module, browser, tracks=None):
        self._rs = rs_module
        self.instance = rs_module.LiveActionsRS.__new__(rs_module.LiveActionsRS)
        self.instance._cache = {}
        self.instance._cache_lock = threading.Lock()
        self.instance._running = False
        self.instance._refresh_listener = None
        self._browser = browser
        self._tracks = tracks or []
        self.instance._browser = lambda: browser
        self.instance.application = lambda: types.SimpleNamespace(
            browser=browser, get_version_string=lambda: "12.0 test"
        )
        self.instance.log_message = lambda *a, **k: None
        self.instance.song = lambda: self._song()

    def _song(self):
        view = types.SimpleNamespace(selected_track=self._tracks[0] if self._tracks else None)
        return types.SimpleNamespace(tracks=self._tracks, view=view)


class LiveActionsRSLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rs = _load_live_actions_rs()

    def _browser(self):
        analog = _FakeItem("Analog", loadable=True, device=True)
        bass = _FakeItem(
            "Bass",
            children=[_FakeItem("Sub Bass", loadable=True), _FakeItem("Reese Lead", loadable=True)],
        )
        return types.SimpleNamespace(
            instruments=_FakeItem("Instruments", children=[analog, bass]),
            sounds=_FakeItem("Sounds", children=[_FakeItem("Bass Hit", loadable=True)]),
            plugins=_FakeItem(
                "Plugins",
                children=[
                    _FakeItem("VST3", children=[_FakeItem("Serum", loadable=True)]),
                ],
            ),
            packs=_FakeItem("Packs", children=[_FakeItem("Beat Tools")]),
            load_item=lambda item: self._loaded.append(item),
            preview_item=lambda item: self._previewed.append(item),
            stop_preview=lambda: self._previewed.append(None),
        )

    def setUp(self) -> None:
        self._loaded: list = []
        self._previewed: list = []
        self.h = _Harness(self.rs, self._browser(), tracks=[
            types.SimpleNamespace(name="Drums"), types.SimpleNamespace(name="Bass"),
        ])
        self.rs_i = self.h.instance

    def test_available_categories_reflects_what_the_browser_actually_has(self) -> None:
        cats = self.rs_i.available_categories()
        self.assertIn("instruments", cats)
        self.assertIn("plugins", cats)
        # Ordered for producers, not alphabetically.
        self.assertLess(cats.index("sounds"), cats.index("instruments"))

    def test_browse_lists_one_level(self) -> None:
        res = self.rs_i._cmd_browse({"category": "instruments"})
        self.assertTrue(res["ok"])
        self.assertEqual([i["name"] for i in res["items"]], ["Analog", "Bass"])
        self.assertTrue(res["items"][0]["is_loadable"])
        self.assertFalse(res["cached"])

    def test_browse_descends_a_path(self) -> None:
        res = self.rs_i._cmd_browse({"category": "instruments", "path": ["Bass"]})
        self.assertEqual([i["name"] for i in res["items"]], ["Sub Bass", "Reese Lead"])
        self.assertEqual(res["path"], ["Bass"])

    def test_browse_accepts_a_slash_string_path(self) -> None:
        res = self.rs_i._cmd_browse({"category": "instruments", "path": "Bass"})
        self.assertEqual(res["path"], ["Bass"])

    def test_second_browse_is_served_from_cache(self) -> None:
        self.rs_i._cmd_browse({"category": "instruments"})
        self.assertTrue(self.rs_i._cmd_browse({"category": "instruments"})["cached"])

    def test_refresh_bypasses_cache_and_full_refresh_clears_it(self) -> None:
        self.rs_i._cmd_browse({"category": "instruments"})
        self.assertFalse(
            self.rs_i._cmd_browse({"category": "instruments", "refresh": True})["cached"]
        )
        self.rs_i._cmd_browse({"category": "instruments"})
        self.rs_i.clear_cache()
        self.assertFalse(self.rs_i._cmd_browse({"category": "instruments"})["cached"])

    def test_browse_reports_total_and_pages(self) -> None:
        # A real Samples category listed 16,272 entries in one reply. Paging is
        # what keeps that from being a multi-megabyte answer nobody can use.
        big = types.SimpleNamespace(
            instruments=_FakeItem("Big", children=[_FakeItem("i%03d" % i, loadable=True) for i in range(50)]),
        )
        rs = _Harness(self.rs, big).instance
        first = rs._cmd_browse({"category": "instruments", "limit": 20})
        self.assertEqual(first["total"], 50)
        self.assertEqual(first["item_count"], 20)
        self.assertEqual(first["offset"], 0)
        self.assertTrue(first["truncated"])
        self.assertEqual(first["items"][0]["name"], "i000")

        second = rs._cmd_browse({"category": "instruments", "limit": 20, "offset": 20})
        self.assertEqual(second["items"][0]["name"], "i020")
        self.assertTrue(second["truncated"])

        last = rs._cmd_browse({"category": "instruments", "limit": 20, "offset": 40})
        self.assertEqual(last["item_count"], 10)
        self.assertFalse(last["truncated"])

    def test_offset_past_the_end_is_empty_not_an_error(self) -> None:
        res = self.rs_i._cmd_browse({"category": "instruments", "offset": 9999})
        self.assertTrue(res["ok"])
        self.assertEqual(res["items"], [])
        self.assertEqual(res["total"], 2)

    def test_has_children_marks_an_expandable_non_folder(self) -> None:
        # Verified against a real library: a Live Pack reports is_folder False
        # AND is_loadable False, yet has children. Without has_children a
        # caller reads that as a dead end and never opens the Pack.
        pack = _FakeItem("Beat Tools", children=[_FakeItem("Drums", children=[_FakeItem("x")])])
        pack.is_folder = False
        browser = types.SimpleNamespace(packs=_FakeItem("Packs", children=[pack]))
        rs = _Harness(self.rs, browser).instance
        res = rs._cmd_browse({"category": "packs"})
        item = res["items"][0]
        self.assertFalse(item["is_folder"])
        self.assertFalse(item["is_loadable"])
        self.assertTrue(item["has_children"])
        self.assertTrue(res["children_probed"])

    def test_child_probe_is_skipped_on_large_listings(self) -> None:
        # The probe materialises every child list, so it must not run on a
        # 16k-entry folder. Callers learn it was skipped via children_probed.
        n = self.rs.CHILD_PROBE_MAX + 1
        browser = types.SimpleNamespace(
            samples=_FakeItem("Samples", children=[_FakeItem("s%d" % i) for i in range(n)]),
        )
        rs = _Harness(self.rs, browser).instance
        res = rs._cmd_browse({"category": "samples", "limit": 5})
        self.assertEqual(res["total"], n)
        self.assertFalse(res["children_probed"])
        self.assertNotIn("has_children", res["items"][0])

    def test_no_category_lists_categories(self) -> None:
        res = self.rs_i._cmd_browse({})
        self.assertIn("instruments", res["categories"])
        self.assertEqual(res["items"], [])

    def test_unknown_category_names_the_valid_ones(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.rs_i._cmd_browse({"category": "nonsense"})
        self.assertIn("instruments", str(ctx.exception))

    def test_missing_path_part_reports_what_is_actually_there(self) -> None:
        # The error has to be useful to a model that guessed a folder name.
        with self.assertRaises(ValueError) as ctx:
            self.rs_i._cmd_browse({"category": "instruments", "path": ["Nope"]})
        msg = str(ctx.exception)
        self.assertIn("Nope", msg)
        self.assertIn("Analog", msg)

    def test_search_finds_nested_loadable_items(self) -> None:
        res = self.rs_i._cmd_search({"query": "bass"})
        names = [r["name"] for r in res["results"]]
        self.assertIn("Sub Bass", names)
        self.assertIn("Bass Hit", names)
        # "Bass" the folder is not loadable, so loadable_only excludes it.
        self.assertNotIn("Bass", names)

    def test_search_records_the_path_needed_to_load_the_hit(self) -> None:
        res = self.rs_i._cmd_search({"query": "sub bass"})
        hit = res["results"][0]
        self.assertEqual(hit["category"], "instruments")
        self.assertEqual(hit["path"], ["Bass", "Sub Bass"])

    def test_search_honours_limit_and_flags_truncation(self) -> None:
        res = self.rs_i._cmd_search({"query": "bass", "limit": 1})
        self.assertEqual(len(res["results"]), 1)
        self.assertTrue(res["truncated"])

    def test_search_requires_a_query(self) -> None:
        self.assertFalse(self.rs_i._cmd_search({"query": "  "})["ok"])

    def test_load_item_by_path_selects_track_and_loads(self) -> None:
        res = self.rs_i._cmd_load_item(
            {"category": "instruments", "path": ["Analog"], "track_index": 1}
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["item_name"], "Analog")
        self.assertEqual(res["track_name"], "Bass")
        self.assertEqual(len(self._loaded), 1)

    def test_load_item_refuses_a_folder(self) -> None:
        res = self.rs_i._cmd_load_item({"category": "instruments", "path": ["Bass"]})
        self.assertFalse(res["ok"])
        self.assertIn("not loadable", res["error"])
        self.assertEqual(self._loaded, [])

    def test_load_item_rejects_out_of_range_track(self) -> None:
        res = self.rs_i._cmd_load_item(
            {"category": "instruments", "path": ["Analog"], "track_index": 9}
        )
        self.assertFalse(res["ok"])
        self.assertIn("out of range", res["error"])
        self.assertEqual(self._loaded, [])

    def test_load_item_by_uri_falls_back_to_scanning(self) -> None:
        res = self.rs_i._cmd_load_item({"uri": "query:Analog"})
        self.assertTrue(res["ok"])
        self.assertEqual(res["item_name"], "Analog")

    def test_item_lookup_needs_category_or_uri(self) -> None:
        with self.assertRaises(ValueError):
            self.rs_i._item_for({})

    def test_preview_and_stop(self) -> None:
        self.assertTrue(
            self.rs_i._cmd_preview_item({"category": "instruments", "path": ["Analog"]})["ok"]
        )
        self.assertTrue(self.rs_i._cmd_stop_preview({})["ok"])
        self.assertEqual(len(self._previewed), 2)

    def test_list_plugins_tags_each_with_its_format(self) -> None:
        res = self.rs_i._cmd_list_plugins({})
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["plugins"][0]["name"], "Serum")
        self.assertEqual(res["plugins"][0]["format"], "VST3")

    def test_list_packs(self) -> None:
        res = self.rs_i._cmd_list_packs({})
        self.assertEqual([p["name"] for p in res["packs"]], ["Beat Tools"])

    # -- dispatch / protocol --------------------------------------------

    def test_unknown_action_is_reported(self) -> None:
        res = self.rs_i._dispatch("no_such_action", {})
        self.assertFalse(res["ok"])
        self.assertIn("unknown action", res["error"])

    def test_mutating_actions_are_marshalled_to_the_main_thread(self) -> None:
        # The safety property: load must never run straight off the socket
        # thread. If this set ever loses load_item, Live can crash.
        self.assertIn("load_item", self.rs.LiveActionsRS._MAIN_THREAD_ACTIONS)
        self.assertNotIn("browse", self.rs.LiveActionsRS._MAIN_THREAD_ACTIONS)
        self.assertNotIn("search", self.rs.LiveActionsRS._MAIN_THREAD_ACTIONS)

    def test_dispatch_line_rejects_bad_json(self) -> None:
        res = self.rs_i._dispatch_line(b"{nope")
        self.assertFalse(res["ok"])
        self.assertIn("invalid JSON", res["error"])

    def test_dispatch_line_echoes_request_id(self) -> None:
        res = self.rs_i._dispatch_line(
            json.dumps({"id": 7, "action": "browse", "params": {}}).encode("utf-8")
        )
        self.assertEqual(res["id"], 7)

    def test_handler_exception_becomes_an_error_reply(self) -> None:
        res = self.rs_i._dispatch_line(
            json.dumps({"id": 1, "action": "browse", "params": {"category": "nonsense"}}).encode()
        )
        self.assertFalse(res["ok"])
        self.assertIn("ValueError", res["error"])


# ── half 3: the Genius-facing dispatch ─────────────────────────────────────

class _FakeRs:
    """Stands in for RemoteScriptClient inside genius_client."""

    def __init__(self, replies) -> None:
        self.replies = replies
        self.calls: list[tuple[str, dict]] = []

    def call(self, action, params=None, timeout=None):
        self.calls.append((action, params or {}))
        reply = self.replies.get(action, {"ok": False, "error": "no fake reply for " + action})
        return reply(params or {}) if callable(reply) else reply


class GeniusBrowserDispatchTests(unittest.TestCase):
    """These run through the real call_live_tool path with bridge=None.

    bridge=None is the point: neither disk search nor engine E2 needs the Max
    for Live device, and an earlier cut of this feature fell through to the
    bridge and turned a perfectly good browser result into "Live Actions Bridge
    is not connected" whenever the device wasn't on a track. Caught live.
    """

    def setUp(self) -> None:
        import genius_client

        self.gc = genius_client
        self.settings = {"rs_port": 59998, "samples_dir": str(Path(__file__).parent)}

    def _run(self, name, args, replies, online=True):
        fake = _FakeRs(replies)
        with unittest.mock.patch.object(self.gc, "rs_online", return_value=online), \
             unittest.mock.patch.object(self.gc, "rs_client", return_value=fake):
            out = self.gc.call_live_tool(None, name, args, settings=self.settings)
        return out, fake

    def test_browse_works_with_no_osc_bridge(self) -> None:
        out, _ = self._run("live_browse", {"category": "instruments"}, {
            "browse": {"ok": True, "category": "instruments", "path": [], "total": 2, "offset": 0,
                       "truncated": False, "items": [
                           {"name": "Analog", "is_folder": False, "is_device": True, "is_loadable": True},
                           {"name": "Bass", "is_folder": True, "is_device": False, "is_loadable": False},
                       ]},
        })
        self.assertIn("Analog", out)
        self.assertIn("loadable", out)
        self.assertIn("browse into it", out)
        self.assertNotIn("Bridge is not connected", out)

    def test_browse_flags_an_expandable_non_folder(self) -> None:
        out, _ = self._run("live_browse", {"category": "packs"}, {
            "browse": {"ok": True, "category": "packs", "path": [], "total": 1, "offset": 0,
                       "truncated": False, "items": [
                           {"name": "Beat Tools", "is_folder": False, "is_device": False,
                            "is_loadable": False, "has_children": True},
                       ]},
        })
        self.assertIn("browse into it", out)

    def test_browse_reports_paging(self) -> None:
        out, _ = self._run("live_browse", {"category": "samples"}, {
            "browse": {"ok": True, "category": "samples", "path": [], "total": 16272, "offset": 0,
                       "truncated": True, "items": [{"name": "kick.wav", "is_loadable": True}]},
        })
        self.assertIn("16272", out)
        self.assertIn("offset", out)

    def test_browse_offline_explains_the_control_surface_step(self) -> None:
        out, _ = self._run("live_browse", {"category": "instruments"}, {}, online=False)
        self.assertIn("LiveActionsRS", out)
        self.assertIn("Control Surface", out)

    def test_library_search_returns_browser_hits_with_no_bridge(self) -> None:
        out, fake = self._run("live_library", {"action": "search", "query": "reese"}, {
            "search": {"ok": True, "results": [
                {"name": "Reese Lead", "category": "instruments", "path": ["Bass", "Reese Lead"],
                 "is_loadable": True},
            ]},
        })
        self.assertIn("Reese Lead", out)
        self.assertIn("Bass/Reese Lead", out)
        self.assertNotIn("Bridge is not connected", out)
        self.assertEqual(fake.calls[0][0], "search")

    def test_library_search_offline_says_the_browser_was_not_searched(self) -> None:
        out, _ = self._run("live_library", {"action": "search", "query": "reese"}, {}, online=False)
        self.assertIn("disk Samples folder only", out)
        self.assertNotIn("Bridge is not connected", out)

    def test_list_plugins_offline_is_actionable_not_a_bridge_error(self) -> None:
        out, _ = self._run("live_library", {"action": "listPlugins"}, {}, online=False)
        self.assertIn("LiveActionsRS", out)
        self.assertNotIn("Bridge is not connected", out)

    def test_list_plugins_online_reports_real_formats(self) -> None:
        out, _ = self._run("live_library", {"action": "listPlugins"}, {
            "list_plugins": {"ok": True, "plugins": [{"name": "Serum", "format": "VST3"}], "count": 1},
        })
        self.assertIn("Serum", out)
        self.assertIn("VST3", out)

    def test_load_names_the_track_the_way_live_shows_it(self) -> None:
        out, fake = self._run("live_load_browser_item",
                              {"category": "instruments", "path": ["Analog"], "track_number": 2}, {
            "load_item": {"ok": True, "item_name": "Analog", "track_name": "Bass", "track_index": 1},
        })
        # 1-based in, 1-based out: the model must never see a raw index.
        self.assertEqual(fake.calls[0][1]["track_index"], 1)
        self.assertIn("Live track 2", out)
        self.assertIn("Analog", out)

    def test_preview_stop_does_not_need_a_target(self) -> None:
        out, fake = self._run("live_preview_browser_item", {"op": "stop"}, {
            "stop_preview": {"ok": True, "stopped": True},
        })
        self.assertEqual(fake.calls[0][0], "stop_preview")
        self.assertIn("Stopped", out)


if __name__ == "__main__":
    unittest.main()
