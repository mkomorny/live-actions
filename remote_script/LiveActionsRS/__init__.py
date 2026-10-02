# LiveActionsRS -- Live Actions Helper "engine E2" browser companion.
#
# Why this exists: bridge/live-actions-bridge.js runs inside Max for Live, whose
# LiveAPI surface has no Browser / BrowserItem class at all -- probed live in
# v1.0.34, `live_app browser` came back exists:false with 0 children, 3/3 across
# three models. Application.browser is only reachable from a MIDI Remote Script
# (ControlSurface), which is real CPython inside Live. So everything that needs
# Live's own browser -- packs, presets, plug-ins, sample audition -- lives here
# and nowhere else.
#
# Deliberately narrow: this is a browser server, not a second bridge. Tracks,
# clips, notes, devices and mixer all stay on the OSC bridge, which already does
# them well. Keeping the surface small is what keeps this script stable across
# Live updates.
#
# Transport is newline-delimited JSON over TCP rather than the bridge's OSC/UDP.
# A browser listing is far bigger than a UDP datagram -- the OSC path needs the
# chunk-reassembly machinery in app/bridge_client.py to survive that, and TCP
# removes the whole failure mode instead of re-implementing it.

from __future__ import absolute_import

import json
import os
import socket
import threading
import time
import traceback

try:
    import Queue as queue  # py2 safety net; Live 12 is py3
except ImportError:
    import queue

from _Framework.ControlSurface import ControlSurface

# 11926 keeps the existing convention in app/settings_store.py (bridge 11924,
# helper 11925) and deliberately avoids 9877, so a user who also runs the
# third-party AbletonMCP script keeps both working side by side.
DEFAULT_PORT = int(os.environ.get("LIVE_ACTIONS_RS_PORT", "11926"))
HOST = "127.0.0.1"

PROTOCOL_VERSION = 1
SOCKET_TIMEOUT = 1.0
CLIENT_TIMEOUT = 60.0
MAX_LINE = 1024 * 1024
MAIN_THREAD_TIMEOUT = 15.0

# Search walks a real user library (47 packs and a deep Samples tree on the dev
# machine), so it is bounded on three axes rather than trusted to terminate.
SEARCH_MAX_RESULTS = 200
SEARCH_MAX_DEPTH = 6
SEARCH_TIME_BUDGET = 6.0

# One folder can be enormous -- the dev machine's Samples category lists 16,272
# entries, which is a multi-megabyte reply nobody can use in one go. Listings
# are paged instead, with the full set cached so paging costs nothing.
BROWSE_PAGE_DEFAULT = 500
BROWSE_PAGE_MAX = 2000
# Above this many entries, skip the per-item has_children probe: it materialises
# every child list, which is affordable for a 47-pack listing and not for 16k.
CHILD_PROBE_MAX = 400


def create_instance(c_instance):
    return LiveActionsRS(c_instance)


class LiveActionsRS(ControlSurface):
    """Browser-only Remote Script companion for Live Actions Helper."""

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._server = None
        self._server_thread = None
        self._running = False
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._refresh_listener = None

        self.log_message("LiveActionsRS: initializing (protocol v%d)" % PROTOCOL_VERSION)
        self._install_refresh_listener()
        self._start_server()
        self.show_message("Live Actions: browser engine listening on %d" % DEFAULT_PORT)

    # -- lifecycle ---------------------------------------------------------

    def _install_refresh_listener(self):
        """Live fires full_refresh when the library changes underneath us (a
        pack installed, a preset saved). Without this the cache would happily
        serve a tree that no longer matches what the user sees in the panel."""
        try:
            browser = self.application().browser
            if hasattr(browser, "add_full_refresh_listener"):
                self._refresh_listener = self._on_full_refresh
                browser.add_full_refresh_listener(self._refresh_listener)
        except Exception as exc:
            self.log_message("LiveActionsRS: could not attach refresh listener (%s)" % exc)

    def _on_full_refresh(self):
        self.clear_cache()
        self.log_message("LiveActionsRS: browser full_refresh -- cache cleared")

    def disconnect(self):
        self.log_message("LiveActionsRS: disconnecting")
        self._running = False
        if self._refresh_listener is not None:
            try:
                browser = self.application().browser
                if hasattr(browser, "remove_full_refresh_listener"):
                    browser.remove_full_refresh_listener(self._refresh_listener)
            except Exception:
                pass
            self._refresh_listener = None
        if self._server is not None:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None
        ControlSurface.disconnect(self)

    # -- socket server -----------------------------------------------------

    def _start_server(self):
        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((HOST, DEFAULT_PORT))
            self._server.listen(4)
            self._server.settimeout(SOCKET_TIMEOUT)
            self._running = True
            self._server_thread = threading.Thread(target=self._accept_loop)
            self._server_thread.daemon = True
            self._server_thread.start()
            self.log_message("LiveActionsRS: listening on %s:%d" % (HOST, DEFAULT_PORT))
        except Exception as exc:
            self.log_message("LiveActionsRS: failed to start server (%s)" % exc)
            self.log_message(traceback.format_exc())
            self._running = False

    def _accept_loop(self):
        while self._running:
            try:
                client, _addr = self._server.accept()
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    self.log_message("LiveActionsRS: accept failed, continuing")
                continue
            worker = threading.Thread(target=self._handle_client, args=(client,))
            worker.daemon = True
            worker.start()

    def _handle_client(self, client):
        """One line of JSON in, one line of JSON out. Newline framing means a
        reply of any size arrives intact -- the caller reads until the newline
        instead of guessing whether the payload is complete yet."""
        client.settimeout(CLIENT_TIMEOUT)
        buf = b""
        try:
            while self._running:
                try:
                    chunk = client.recv(65536)
                except socket.timeout:
                    break
                if not chunk:
                    break
                buf += chunk
                if len(buf) > MAX_LINE:
                    self._send(client, {"ok": False, "error": "request too large"})
                    break
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    self._send(client, self._dispatch_line(line))
        except Exception as exc:
            self.log_message("LiveActionsRS: client error (%s)" % exc)
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _send(self, client, payload):
        try:
            client.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        except Exception as exc:
            self.log_message("LiveActionsRS: send failed (%s)" % exc)

    def _dispatch_line(self, line):
        try:
            request = json.loads(line.decode("utf-8"))
        except Exception as exc:
            return {"ok": False, "error": "invalid JSON request (%s)" % exc}
        if not isinstance(request, dict):
            return {"ok": False, "error": "request must be a JSON object"}
        action = str(request.get("action") or "")
        params = request.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        req_id = request.get("id")
        try:
            result = self._dispatch(action, params)
        except Exception as exc:
            self.log_message("LiveActionsRS: %s failed (%s)" % (action, exc))
            self.log_message(traceback.format_exc())
            result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}
        if req_id is not None and isinstance(result, dict):
            result["id"] = req_id
        return result

    # Anything that mutates the Set has to run on Live's main thread --
    # load_item inserts a device, and calling that from the socket thread is
    # the classic way to corrupt Live's state or hard-crash it. Read-only
    # walks are safe inline, which is also what keeps browsing fast.
    _MAIN_THREAD_ACTIONS = frozenset(["load_item", "preview_item", "stop_preview"])

    def _dispatch(self, action, params):
        handler = getattr(self, "_cmd_" + action, None)
        if handler is None:
            return {"ok": False, "error": "unknown action '%s'" % action}
        if action not in self._MAIN_THREAD_ACTIONS:
            return handler(params)

        box = queue.Queue(maxsize=1)

        def run_on_main():
            try:
                box.put(handler(params))
            except Exception as exc:
                box.put({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)})

        self.schedule_message(0, run_on_main)
        try:
            return box.get(timeout=MAIN_THREAD_TIMEOUT)
        except Exception:
            return {"ok": False, "error": "timed out waiting for Live's main thread on '%s'" % action}

    # -- browser helpers ---------------------------------------------------

    # Ordered so the categories a producer reaches for first are listed first.
    CATEGORIES = [
        "sounds", "drums", "instruments", "audio_effects", "midi_effects",
        "max_for_live", "plugins", "clips", "samples",
        "user_library", "current_project", "packs",
    ]

    def _browser(self):
        app = self.application()
        if app is None:
            raise RuntimeError("Live application unavailable")
        browser = getattr(app, "browser", None)
        if browser is None:
            raise RuntimeError("Live browser unavailable")
        return browser

    def _category_root(self, category):
        key = str(category or "").strip().lower().replace(" ", "_").replace("-", "_")
        browser = self._browser()
        root = getattr(browser, key, None)
        if root is None:
            raise ValueError(
                "unknown browser category '%s' -- available: %s"
                % (category, ", ".join(self.available_categories()))
            )
        return key, root

    def available_categories(self):
        browser = self._browser()
        return [c for c in self.CATEGORIES if getattr(browser, c, None) is not None]

    @classmethod
    def _describe(cls, item, with_children=False):
        """Flatten one BrowserItem.

        `is_folder` alone is NOT a reliable "can I descend here?" signal: a Live
        Pack reports is_folder False and is_loadable False while still having
        children (verified against a real library -- "Beat Tools" has 6). Left
        at that, a caller sees "not a folder, not loadable" and treats an entire
        Pack as a dead end. `has_children` fixes that, but it materialises each
        item's child list, so it is only computed for small listings (see
        CHILD_PROBE_MAX) -- a Samples folder here has 16k entries and probing
        every one would cost far more than the listing itself.
        """
        out = {
            "name": getattr(item, "name", "") or "",
            "is_folder": bool(getattr(item, "is_folder", False)),
            "is_device": bool(getattr(item, "is_device", False)),
            "is_loadable": bool(getattr(item, "is_loadable", False)),
            "uri": getattr(item, "uri", None),
        }
        if with_children:
            out["has_children"] = bool(cls._children(item))
        return out

    @staticmethod
    def _children(item):
        try:
            return list(getattr(item, "children", []) or [])
        except Exception:
            return []

    def _resolve(self, category, path):
        """Walk `path` (a list of child names) down from a category root.

        Name-based rather than URI-based on purpose: a URI lookup means a full
        recursive scan of the library to find a match, while a path walk only
        touches the folders actually named. Names are also what the model and
        the user can both see in Live's panel.
        """
        key, current = self._category_root(category)
        walked = []
        for part in (path or []):
            target = str(part).strip().lower()
            found = None
            for child in self._children(current):
                if (getattr(child, "name", "") or "").strip().lower() == target:
                    found = child
                    break
            if found is None:
                names = [self._describe(c)["name"] for c in self._children(current)][:40]
                raise ValueError(
                    "'%s' not found under %s -- available here: %s"
                    % (part, "/".join([key] + walked), ", ".join(names) or "(empty)")
                )
            current = found
            walked.append(getattr(found, "name", "") or str(part))
        return key, current, walked

    def _find_by_uri(self, uri, max_depth=SEARCH_MAX_DEPTH):
        """Fallback lookup when a caller has only a URI. Bounded by depth and
        by a wall-clock budget so a pathological library cannot wedge Live."""
        deadline = time.time() + SEARCH_TIME_BUDGET
        browser = self._browser()
        for category in self.available_categories():
            root = getattr(browser, category, None)
            if root is None:
                continue
            stack = [(root, 0)]
            while stack:
                if time.time() > deadline:
                    return None
                node, depth = stack.pop()
                if getattr(node, "uri", None) == uri:
                    return node
                if depth < max_depth:
                    for child in self._children(node):
                        stack.append((child, depth + 1))
        return None

    def _item_for(self, params):
        """Accept either a path (preferred, cheap) or a bare URI (fallback)."""
        uri = params.get("uri")
        category = params.get("category")
        path = params.get("path") or []
        if isinstance(path, str):
            path = [p for p in path.split("/") if p]
        if category:
            _key, item, _walked = self._resolve(category, path)
            return item
        if uri:
            item = self._find_by_uri(str(uri))
            if item is None:
                raise ValueError("no browser item with uri '%s'" % uri)
            return item
        raise ValueError("need either category(+path) or uri")

    def clear_cache(self):
        with self._cache_lock:
            self._cache.clear()

    # -- commands ----------------------------------------------------------

    def _cmd_ping(self, params):
        app = self.application()
        try:
            version = app.get_version_string()
        except Exception:
            version = "unknown"
        return {
            "ok": True,
            "engine": "LiveActionsRS",
            "protocol": PROTOCOL_VERSION,
            "port": DEFAULT_PORT,
            "live_version": version,
            "categories": self.available_categories(),
        }

    def _cmd_browse(self, params):
        """List one level of the tree. This is the list_browser(category, path,
        refresh) entry point."""
        category = params.get("category")
        if not category:
            return {"ok": True, "categories": self.available_categories(), "items": []}
        path = params.get("path") or []
        if isinstance(path, str):
            path = [p for p in path.split("/") if p]
        refresh = bool(params.get("refresh"))
        offset = max(0, int(params.get("offset") or 0))
        limit = min(max(1, int(params.get("limit") or BROWSE_PAGE_DEFAULT)), BROWSE_PAGE_MAX)
        cache_key = (str(category).lower(), tuple(str(p).lower() for p in path))

        cached = False
        entry = None
        if not refresh:
            with self._cache_lock:
                entry = self._cache.get(cache_key)
            cached = entry is not None

        if entry is None:
            key, item, walked = self._resolve(category, path)
            children = self._children(item)
            probe = len(children) <= CHILD_PROBE_MAX
            entry = {
                "category": key,
                "path": walked,
                "all_items": [self._describe(c, with_children=probe) for c in children],
                "is_loadable": bool(getattr(item, "is_loadable", False)) if walked else False,
                "uri": getattr(item, "uri", None) if walked else None,
                "children_probed": probe,
            }
            with self._cache_lock:
                self._cache[cache_key] = entry

        total = len(entry["all_items"])
        page = entry["all_items"][offset : offset + limit]
        return {
            "ok": True,
            "category": entry["category"],
            "path": entry["path"],
            "items": page,
            "item_count": len(page),
            "total": total,
            "offset": offset,
            "truncated": offset + len(page) < total,
            "children_probed": entry["children_probed"],
            "is_loadable": entry["is_loadable"],
            "uri": entry["uri"],
            "cached": cached,
        }

    def _cmd_search(self, params):
        """Recursive name match. Bounded by results, depth and wall clock."""
        query = str(params.get("query") or "").strip().lower()
        if not query:
            return {"ok": False, "error": "query required"}
        limit = min(int(params.get("limit") or 50), SEARCH_MAX_RESULTS)
        loadable_only = bool(params.get("loadable_only", True))
        categories = params.get("categories") or []
        if isinstance(categories, str):
            categories = [categories]
        if not categories:
            categories = self.available_categories()

        deadline = time.time() + SEARCH_TIME_BUDGET
        browser = self._browser()
        results = []
        truncated = False

        for category in categories:
            root = getattr(browser, str(category).lower(), None)
            if root is None:
                continue
            stack = [(child, [], 0) for child in self._children(root)]
            while stack:
                if time.time() > deadline or len(results) >= limit:
                    truncated = truncated or bool(stack)
                    break
                node, trail, depth = stack.pop()
                name = getattr(node, "name", "") or ""
                if query in name.lower():
                    described = self._describe(node)
                    if described["is_loadable"] or not loadable_only:
                        described["category"] = str(category).lower()
                        described["path"] = trail + [name]
                        results.append(described)
                if depth < SEARCH_MAX_DEPTH:
                    for child in self._children(node):
                        stack.append((child, trail + [name], depth + 1))
            if len(results) >= limit:
                truncated = True
                break

        return {
            "ok": True,
            "query": params.get("query"),
            "results": results[:limit],
            "count": len(results[:limit]),
            "truncated": truncated,
            "searched_categories": [str(c).lower() for c in categories],
        }

    def _cmd_load_item(self, params):
        """Load a preset / device / plug-in onto a track. Main thread only."""
        item = self._item_for(params)
        if not getattr(item, "is_loadable", False):
            return {
                "ok": False,
                "error": "'%s' is not loadable (it is a folder or an unavailable item)"
                % (getattr(item, "name", "?")),
            }
        song = self.song()
        tracks = list(song.tracks)
        track_index = params.get("track_index")
        if track_index is not None:
            idx = int(track_index)
            if idx < 0 or idx >= len(tracks):
                return {
                    "ok": False,
                    "error": "track_index %d out of range (0-%d)" % (idx, len(tracks) - 1),
                }
            track = tracks[idx]
            song.view.selected_track = track
        else:
            track = song.view.selected_track

        self._browser().load_item(item)
        return {
            "ok": True,
            "loaded": True,
            "item_name": getattr(item, "name", ""),
            "uri": getattr(item, "uri", None),
            "track_name": getattr(track, "name", ""),
            "track_index": tracks.index(track) if track in tracks else None,
        }

    def _cmd_preview_item(self, params):
        """Audition through Live's preview channel -- does not touch the Set."""
        item = self._item_for(params)
        browser = self._browser()
        if not hasattr(browser, "preview_item"):
            return {"ok": False, "error": "this Live version has no browser preview"}
        browser.preview_item(item)
        return {
            "ok": True,
            "previewing": getattr(item, "name", ""),
            "uri": getattr(item, "uri", None),
        }

    def _cmd_stop_preview(self, params):
        browser = self._browser()
        if hasattr(browser, "stop_preview"):
            browser.stop_preview()
        return {"ok": True, "stopped": True}

    def _cmd_list_plugins(self, params):
        """Real installed VST/VST3 -- the M4L path could never read these, which
        is why palLibrary still (correctly, for that engine) returns []."""
        out = []
        for folder in self._children(self._category_root("plugins")[1]):
            fmt = getattr(folder, "name", "") or ""
            for plug in self._children(folder):
                described = self._describe(plug)
                described["format"] = fmt
                out.append(described)
            if len(out) >= 1000:
                break
        return {"ok": True, "plugins": out, "count": len(out)}

    def _cmd_list_packs(self, params):
        packs = [self._describe(p) for p in self._children(self._category_root("packs")[1])]
        return {"ok": True, "packs": packs, "count": len(packs)}

    def _cmd_clear_cache(self, params):
        self.clear_cache()
        return {"ok": True, "cleared": True}
