"""Tests for shell_genius.GeniusSession (no network, no window): the ask function is a script."""

from __future__ import annotations

import copy
import threading
import unittest

import agent_registry
import shell_genius
from shell_genius import GeniusSession
from shell_model import SessionModel, load_demo_state


class Page:
    """Python twin of the page's event reducer (web/js/app.js applyGenius). If replaying every
    pushed event into this reproduces GeniusSession.snapshot(), the events are sufficient."""

    def __init__(self, snap: dict) -> None:
        self.msgs = copy.deepcopy(snap["messages"])
        self.busy = snap["busy"]

    def msg(self, mid):
        return next(m for m in self.msgs if m["id"] == mid)

    def apply(self, e: dict) -> None:
        op = e["op"]
        if op == "add":
            self.msgs.append(copy.deepcopy(e["msg"]))
        elif op == "part":
            self.msg(e["id"])["parts"].append(copy.deepcopy(e["part"]))
        elif op == "text":
            p = self.msg(e["id"])["parts"][e["i"]]
            p["text"] = p["text"][: e["offset"]] + e["text"]
        elif op == "settext":
            self.msg(e["id"])["parts"][e["i"]]["text"] = e["text"]
        elif op == "call":
            p = self.msg(e["id"])["parts"][e["i"]]
            p["state"], p["note"] = e["state"], e["note"]
        elif op == "done":
            m = self.msg(e["id"])
            m["state"] = e["state"]
            if e.get("error"):
                m["error"] = e["error"]
            self.busy = False
        elif op == "busy":
            self.busy = e["busy"]
        elif op == "clear":
            self.msgs = copy.deepcopy(e["messages"])
            self.busy = False


def make(ask=None, settings=None, flush_every=0.01):
    events: list[dict] = []
    saved: list[dict] = []
    settings = settings if settings is not None else {"api_key": "k", "model": "m", "enabled_agents": [], "active_agent": ""}
    lock = threading.RLock()
    session = GeniusSession(
        lock=lock,
        emit=events.append,
        get_settings=lambda: settings,
        live_line=lambda: "Live offline",
        get_bridge=lambda: None,
        save_settings=lambda s: saved.append(dict(s)),
        ask=ask,
        flush_every=flush_every,
    )
    return session, events, saved, settings


def wait_idle(session: GeniusSession, timeout: float = 5.0) -> None:
    end = threading.Event()
    t = threading.Timer(timeout, end.set)
    t.start()
    try:
        while session._turn is not None and not end.is_set():
            end.wait(0.005)
    finally:
        t.cancel()
    if session._turn is not None:
        raise AssertionError("turn never finished")
    # Let a pending flush timer drain too.
    end2 = threading.Event()
    end2.wait(0.05)


def genius_events(events):
    return [e for e in events if e.get("type") == "genius"]


class SendAndStream(unittest.TestCase):
    def test_a_reply_streams_into_one_bot_bubble_and_lands_in_history(self):
        def ask(settings, history, live_line, **kw):
            self.assertEqual(history[-1], {"role": "user", "content": "hi there"})
            self.assertEqual(live_line, "Live offline")
            kw["on_content"]("Hel")
            kw["on_content"]("lo")
            return "Hello"

        s, ev, _, _ = make(ask)
        self.assertEqual(s.send("  hi there  "), {"ok": True})
        wait_idle(s)
        snap = s.snapshot()
        self.assertFalse(snap["busy"])
        roles = [m["role"] for m in snap["messages"]]
        self.assertEqual(roles, ["bot", "user", "bot"])          # greeting, you, Genius
        self.assertEqual(snap["messages"][-1]["parts"], [{"kind": "text", "text": "Hello"}])
        self.assertEqual(snap["messages"][-1]["state"], "done")
        self.assertEqual(s._history, [{"role": "user", "content": "hi there"}, {"role": "assistant", "content": "Hello"}])

    def test_events_replayed_into_the_page_reproduce_the_snapshot(self):
        def ask(settings, history, live_line, **kw):
            kw["on_thinking"]("hmm ")
            kw["on_thinking"]("ok")
            kw["on_content"]("Let me look. ")
            kw["on_tool_call"]("live_read_set", "-> Live Actions: read set...")
            kw["on_tool_call"]("live_read_set", "[Done] read set")
            kw["on_tool_call"]("live_write_notes", "-> Live Actions: add notes...")
            kw["on_tool_call"]("live_write_notes", "[Error] no such clip")
            kw["on_content"]("All ")
            kw["on_content"]("done")
            return "All done."          # final text differs from the streamed text: settext must reconcile it

        s, ev, _, _ = make(ask)
        page = Page(s.snapshot())
        s.send("go")
        wait_idle(s)
        for e in genius_events(ev):
            page.apply(e)
        self.assertEqual(page.msgs, s.snapshot()["messages"])
        self.assertFalse(page.busy)
        bot = page.msgs[-1]
        kinds = [p["kind"] for p in bot["parts"]]
        self.assertEqual(kinds, ["think", "text", "call", "call", "text"])
        self.assertEqual(bot["parts"][0]["text"], "hmm ok")
        self.assertEqual(bot["parts"][1]["text"], "Let me look. ")            # narration before the calls survives
        self.assertEqual([(p["state"], p["note"]) for p in bot["parts"] if p["kind"] == "call"], [("ok", ""), ("error", "no such clip")])
        self.assertEqual(bot["parts"][4]["text"], "All done.")                # the authoritative reply

    def test_text_emission_is_coalesced_but_lossless(self):
        gate = threading.Event()

        def ask(settings, history, live_line, **kw):
            for _ in range(500):
                kw["on_content"]("x")
            gate.set()
            return "x" * 500

        s, ev, _, _ = make(ask, flush_every=0.2)      # long window: 500 chunks must collapse
        s.send("go")
        wait_idle(s)
        text_events = [e for e in genius_events(ev) if e["op"] == "text"]
        self.assertLess(len(text_events), 10, "500 tokens must not become 500 pushes")
        bot_id = s.snapshot()["messages"][-1]["id"]
        self.assertEqual({e["id"] for e in text_events}, {bot_id}, "only the message being answered streams; the greeting is never re-sent")
        page = Page({"messages": [], "busy": False})
        for e in genius_events(ev):
            if e["op"] == "add":
                page.apply(e)
            elif e["op"] in ("part", "text", "settext", "done"):
                page.apply(e)
        self.assertEqual(page.msgs[-1]["parts"][0]["text"], "x" * 500)

    def test_a_snapshot_taken_mid_stream_can_never_double_the_text(self):
        """The page fetches its snapshot while text is buffered but unsent; the later flush carries an
        absolute offset, so replaying it over the snapshot's text is idempotent."""
        release = threading.Event()
        started = threading.Event()

        def ask(settings, history, live_line, **kw):
            kw["on_content"]("abc")
            started.set()
            release.wait(5)
            kw["on_content"]("def")
            return "abcdef"

        s, ev, _, _ = make(ask, flush_every=0.02)
        s.send("go")
        started.wait(5)
        snap = s.snapshot()                                   # contains "abc" whether or not it was flushed
        page = Page(snap)
        cut = len(ev)                                         # a real gate discards everything before the snapshot
        release.set()
        wait_idle(s)
        for e in genius_events(ev[cut:]):
            page.apply(e)
        self.assertEqual(page.msgs[-1]["parts"][0]["text"], "abcdef")

    def test_busy_and_empty_sends_are_refused(self):
        hold = threading.Event()
        s, ev, _, _ = make(lambda *a, **k: (hold.wait(5), "ok")[1])
        self.assertEqual(s.send("   "), {"ok": False, "error": "empty"})
        self.assertEqual(s.send("one"), {"ok": True})
        self.assertEqual(s.send("two"), {"ok": False, "error": "busy"})
        self.assertEqual(sum(1 for m in s.snapshot()["messages"] if m["role"] == "user"), 1)
        hold.set()
        wait_idle(s)


class ErrorsAndStop(unittest.TestCase):
    def test_an_error_keeps_the_history_alternating_and_is_shown(self):
        def ask(*a, **k):
            raise RuntimeError("No API key. Open Settings and paste your API key.")

        s, ev, _, _ = make(ask)
        s.send("hi")
        wait_idle(s)
        bot = s.snapshot()["messages"][-1]
        self.assertEqual(bot["state"], "error")
        self.assertEqual(bot["error"], "Error: No API key. Open Settings and paste your API key.")
        self.assertEqual([h["role"] for h in s._history], ["user", "assistant"])
        self.assertEqual(s.send("again"), {"ok": True})            # and the chat is usable again
        wait_idle(s)
        self.assertEqual([h["role"] for h in s._history], ["user", "assistant", "user", "assistant"])

    def test_stop_closes_the_turn_at_once_and_ignores_the_late_worker(self):
        entered, release = threading.Event(), threading.Event()
        late: list[str] = []

        def ask(settings, history, live_line, **kw):
            kw["on_tool_call"]("live_slow", "-> Live Actions: slow...")
            entered.set()
            release.wait(5)                                   # a bridge call that ignores cancel for a while
            kw["on_content"]("too late")                      # ...and reports afterwards
            kw["on_tool_call"]("live_slow", "[Done] slow")
            late.append("ran")
            raise RuntimeError("Generation stopped by user.")

        s, ev, _, _ = make(ask)
        page = Page(s.snapshot())
        s.send("go")
        entered.wait(5)
        self.assertTrue(s.stop())
        self.assertFalse(s.snapshot()["busy"])
        self.assertFalse(s.stop())                            # nothing left to stop
        release.set()
        for _ in range(200):
            if late:
                break
            threading.Event().wait(0.01)
        threading.Event().wait(0.1)
        for e in genius_events(ev):
            page.apply(e)
        bot = page.msgs[-1]
        self.assertEqual(bot["state"], "stopped")
        self.assertEqual([p["kind"] for p in bot["parts"]], ["call"])         # nothing added after Stop
        self.assertEqual((bot["parts"][0]["state"], bot["parts"][0]["note"]), ("error", "stopped"))
        self.assertEqual(s._history[-1], {"role": "assistant", "content": shell_genius.STOPPED})
        self.assertEqual(page.msgs, s.snapshot()["messages"])
        self.assertEqual(s.send("next"), {"ok": True})        # a new turn works while the old worker is still winding down

    def test_clear_resets_and_cancels(self):
        release = threading.Event()
        cancelled: list[bool] = []

        def ask(settings, history, live_line, **kw):
            release.wait(5)
            cancelled.append(kw["cancel_event"].is_set())
            return "x"

        s, ev, _, _ = make(ask)
        s.send("go")
        s.clear()
        release.set()
        wait_idle(s)
        threading.Event().wait(0.05)
        self.assertEqual([m["role"] for m in s.snapshot()["messages"]], ["bot"])     # just the greeting
        self.assertEqual(s._history, [])
        self.assertEqual(cancelled, [True])
        self.assertFalse(s.snapshot()["busy"])


class AgentsAndStatus(unittest.TestCase):
    def test_set_agent_persists_notes_and_announces(self):
        agents = agent_registry.list_agents({})
        self.assertTrue(agents, "the repo ships personas")
        slug, title = agents[0]["slug"], agents[0]["title"]
        s, ev, saved, settings = make(settings={"api_key": "k", "model": "m", "enabled_agents": [slug], "active_agent": ""})
        snap = s.snapshot()
        self.assertEqual(snap["agent"], {"slug": "", "title": "Stock Genius"})
        self.assertEqual(snap["agents"], [{"slug": slug, "title": title}])

        self.assertEqual(s.set_agent("not-enabled"), {"ok": False, "error": "That agent is not enabled."})
        self.assertEqual(saved, [])
        self.assertEqual(s.set_agent(slug), {"ok": True})
        self.assertEqual(saved[-1]["active_agent"], slug)
        note = s.snapshot()["messages"][-1]
        self.assertEqual((note["role"], note["text"]), ("system", "Switched to %s." % title))
        self.assertEqual(genius_events(ev)[-1]["agent"], {"slug": slug, "title": title})
        self.assertEqual(genius_events(ev)[-1]["status"], {"key": True})              # the page learns key presence from this event
        self.assertEqual(s.set_agent(""), {"ok": True})
        self.assertEqual(s.snapshot()["agent"]["title"], "Stock Genius")
        self.assertEqual(s.snapshot()["messages"][-1]["text"], "Switched back to stock Genius.")

    def test_status_reports_key_presence_without_the_key(self):
        s, _, _, _ = make(settings={"api_key": "sk-secret", "model": "m", "enabled_agents": []})
        snap = s.snapshot()
        self.assertTrue(snap["status"]["key"])
        self.assertNotIn("sk-secret", repr(snap))
        s2, _, _, _ = make(settings={"api_key": "  ", "model": "m", "enabled_agents": []})
        self.assertFalse(s2.snapshot()["status"]["key"])

    def test_demo_is_the_previews_conversation(self):
        s, _, _, _ = make()
        s.load_demo()
        snap = s.snapshot()
        self.assertEqual([m["role"] for m in snap["messages"]], ["user", "bot", "user", "bot"])
        self.assertEqual([p["state"] for p in snap["messages"][1]["parts"] if p["kind"] == "call"], ["ok", "ok", "ok"])
        self.assertEqual(snap["messages"][3]["parts"][1], {"kind": "call", "name": "live_duplicate", "state": "run", "note": ""})
        self.assertEqual((snap["agent"]["title"], snap["model"]), ("Stock Genius", "grok-4.6"))
        self.assertTrue(snap["status"]["key"])


class ThroughTheModel(unittest.TestCase):
    def test_model_snapshot_carries_genius_and_events_share_the_stream(self):
        events: list[dict] = []
        model = SessionModel({"listen_port": 1, "bridge_port": 2, "api_key": "k", "model": "m"}, [], emit=events.append)
        self.assertIn("genius", model.snapshot())
        self.assertEqual(model.live_line(), "Live offline")
        load_demo_state(model)
        self.assertEqual(model.live_line(), "Live connected: Neon Nights 128.als @ 128.00")
        snap = model.snapshot()["genius"]
        self.assertEqual(len(snap["messages"]), 4)
        model.genius._ask = lambda *a, **k: "pong"
        events.clear()
        model.genius.send("ping")
        wait_idle(model.genius)
        self.assertTrue(events and all(e["type"] == "genius" for e in events))
        model.genius.close()


if __name__ == "__main__":
    unittest.main()
