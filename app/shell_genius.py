"""Genius chat session for the WebView2 shell -- pure logic, no UI import.

The Tk app kept the conversation in a `tk.Text` widget plus a handful of flags
(`_busy`, `_thinking_active`, `_cancel_event`, `_genius_messages`). Here Python owns
all of it and the page is a view, exactly like shell_model.SessionModel (whose lock
and `emit` this class shares, so an event can never slip between a page snapshot
and the gate that opens after it).

What is displayed vs. what is sent
  * `_history`  -- the provider conversation: [{"role", "content"}], user/assistant
    turns only, kept strictly alternating (an error or a Stop still appends an
    assistant turn, as helper.py did, because Anthropic rejects two user turns in a row).
  * `_msgs`     -- what the page shows: user bubbles, bot bubbles made of PARTS, and
    one-line system notes. A bot bubble's parts are, in arrival order:
        {"kind": "think", "text"}                      streamed reasoning
        {"kind": "text",  "text"}                      streamed reply text
        {"kind": "call",  "name", "state", "note"}     a tool call: run | ok | error
    `genius_client.ask_genius` returns only the LAST round's text; earlier rounds'
    text (narration before a tool call) arrives through on_content and stays visible
    as its own text part. On success the last text part is overwritten with the
    authoritative reply.

Streaming
  Token deltas can arrive hundreds of times a second, and every push is an
  evaluate_js round trip. State is always updated immediately; only the EMISSION of
  text is coalesced (one event per part per `flush_every`, default 50 ms). Text
  events carry the absolute `offset` they start at, so a page that already has the
  text (because its snapshot was taken mid-stream) can never double it.

Stop
  `stop()` closes the turn at once (the Tk app did too). The worker thread keeps
  running until its next cancel check; everything it reports afterwards is ignored
  because each callback checks that its turn is still the current one.

Event shapes (all plain JSON, pushed through the model's `emit`):
  {"type":"genius","op":"add",    "msg": {...}}
  {"type":"genius","op":"part",   "id", "part": {...}}
  {"type":"genius","op":"text",   "id", "i", "offset", "text"}
  {"type":"genius","op":"call",   "id", "i", "state", "note"}
  {"type":"genius","op":"done",   "id", "state", "error"?}     # also busy -> False
  {"type":"genius","op":"busy",   "busy"}
  {"type":"genius","op":"clear", "messages"}                # the fresh transcript (just the greeting)
  {"type":"genius","op":"settext","id", "i", "text"}      # the authoritative final reply
  {"type":"genius","op":"agent",  "agent", "agents", "model", "status"}
"""

from __future__ import annotations

import copy
import threading
import time
from typing import Any, Callable

import agent_registry
import settings_store

FLUSH_EVERY_S = 0.05
GREETING = (
    "I'm Genius — a knowledge library plus full Live control through the Live Actions Bridge.\n"
    "Ask a how-to question, or tell me to build tracks, native devices, clips, routing, and MIDI."
)
# Stored in history as the assistant turn's content when a turn ends without a real
# reply (stopped, or errored -- see _finish below). Phrased as a neutral session
# note, not as something Genius said: a bare "[Stopped by user]" or bracketed error
# string, read back on a later turn as the model's own prior words, taught it to
# narrate itself as a serial quitter rather than reporting what actually happened.
STOPPED = "(Session note: the user stopped generation before a reply was produced this turn.)"
# (label, prompt sent when the pill is clicked). Genius resolves tracks itself, so none of these name one.
PROMPT_PILLS = [
    ("Name my clips", "Give every unnamed clip in my Set a short, descriptive name based on what it contains."),
    ("Build a drum fill", "Build a one-bar drum fill for the end of my current drum clip."),
    ("Find the key", "What key and mode is my Set in? Check the MIDI clips and tell me."),
]


class _Turn:
    """One in-flight request. Identity is what matters: a callback is live only while
    `session._turn is turn`."""

    def __init__(self, msg_id: int) -> None:
        self.msg_id = msg_id
        self.cancel = threading.Event()


class GeniusSession:
    def __init__(
        self,
        *,
        lock: threading.RLock,
        emit: Callable[[dict[str, Any]], None],
        get_settings: Callable[[], dict[str, Any]],
        live_line: Callable[[], str],
        get_bridge: Callable[[], Any],
        save_settings: Callable[[dict[str, Any]], Any] | None = None,
        ask: Callable[..., str] | None = None,
        confirm: Callable[[str, dict[str, Any]], bool] | None = None,
        flush_every: float = FLUSH_EVERY_S,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._lock = lock
        self._emit = emit
        self._get_settings = get_settings
        self._live_line = live_line
        self._get_bridge = get_bridge
        self._save_settings = save_settings or settings_store.save_settings
        self._ask = ask
        # How a tool asks the user to approve something that costs them money. None means
        # the tools that need it refuse -- see genius_client.handle_tts_vocal.
        self._confirm = confirm
        self._flush_every = flush_every
        self._clock = clock

        self._msgs: list[dict[str, Any]] = []
        self._history: list[dict[str, str]] = []
        self._next_id = 1
        self._turn: _Turn | None = None
        self._sent: dict[tuple[int, int], int] = {}     # (msg id, part index) -> chars already emitted
        self._timer: threading.Timer | None = None
        self._demo = False
        self._closed = False
        self._add_bot(GREETING, state="done")

    # -- helpers (callers hold the lock) ---------------------------------------

    def _new_id(self) -> int:
        n = self._next_id
        self._next_id += 1
        return n

    def _add_bot(self, text: str = "", state: str = "streaming") -> dict[str, Any]:
        msg = {"id": self._new_id(), "role": "bot", "parts": [{"kind": "text", "text": text}] if text else [], "state": state}
        self._msgs.append(msg)
        return msg

    def _msg(self, msg_id: int) -> dict[str, Any] | None:
        for m in reversed(self._msgs):
            if m["id"] == msg_id:
                return m
        return None

    def _agents(self) -> tuple[dict[str, str], list[dict[str, str]]]:
        """(active agent, enabled agents) as {"slug","title"}; stock Genius is slug ""."""
        settings = self._get_settings()
        stock = {"slug": "", "title": "Stock Genius"}
        if self._demo:
            return stock, []
        enabled: list[dict[str, str]] = []
        for slug in list(settings.get("enabled_agents") or []):
            agent = agent_registry.load_agent(settings, slug)
            if agent is not None:
                enabled.append({"slug": slug, "title": str(agent["title"])})
        active = str(settings.get("active_agent") or "")
        current = next((a for a in enabled if a["slug"] == active), stock)
        return current, enabled

    def _status(self) -> dict[str, bool]:
        """Only what the page needs to warn about: whether an API key exists (never the key).
        Library/samples folder checks stay out on purpose -- a stat on a slow or missing drive
        must not run under the shared lock."""
        if self._demo:
            return {"key": True}
        return {"key": bool(str(self._get_settings().get("api_key") or "").strip())}

    def _agent_event(self) -> dict[str, Any]:
        current, enabled = self._agents()
        # `status` rides along: the same Preferences edits that change agents / model (a key added or deleted)
        # change whether Genius can answer at all, and the page only learns it from an event.
        return {"type": "genius", "op": "agent", "agent": current, "agents": enabled, "model": self._model_name(), "status": self._status()}

    def _model_name(self) -> str:
        return "grok-4.6" if self._demo else str(self._get_settings().get("model") or "")

    # -- snapshot --------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            current, enabled = self._agents()
            return {
                "busy": self._turn is not None,
                "messages": copy.deepcopy(self._msgs),
                "agent": current,
                "agents": enabled,
                "model": self._model_name(),
                "status": self._status(),
                "pills": [{"label": l, "prompt": p} for l, p in PROMPT_PILLS],
            }

    # -- streaming emission ------------------------------------------------------

    def _schedule_flush(self) -> None:
        if self._timer is None and not self._closed:
            self._timer = threading.Timer(self._flush_every, self._flush_timer)
            self._timer.daemon = True
            self._timer.start()

    def _flush_timer(self) -> None:
        with self._lock:
            self._timer = None
            self._flush_locked()

    def _flush_locked(self) -> None:
        """Emit the not-yet-sent tail of every streaming part of the message being answered.
        Only that message can have unsent text: every other part reached the page whole
        (through `add` or the snapshot)."""
        turn = self._turn
        m = self._msg(turn.msg_id) if turn is not None else None
        if m is None:
            return
        for i, p in enumerate(m["parts"]):
            if p["kind"] not in ("text", "think"):
                continue
            key = (m["id"], i)
            sent = self._sent.get(key, 0)
            if len(p["text"]) > sent:
                self._emit({"type": "genius", "op": "text", "id": m["id"], "i": i, "offset": sent, "text": p["text"][sent:]})
                self._sent[key] = len(p["text"])

    def _push_text(self, turn: _Turn, kind: str, chunk: str) -> None:
        with self._lock:
            if turn is not self._turn or not chunk:
                return
            msg = self._msg(turn.msg_id)
            if msg is None:
                return
            parts = msg["parts"]
            if parts and parts[-1]["kind"] == kind:
                parts[-1]["text"] += chunk
            else:
                parts.append({"kind": kind, "text": chunk})
                # Register the part with what it already holds so the tail logic emits from 0.
                self._emit({"type": "genius", "op": "part", "id": msg["id"], "part": {"kind": kind, "text": ""}})
                self._sent[(msg["id"], len(parts) - 1)] = 0
            self._schedule_flush()

    def _on_tool_call(self, turn: _Turn, name: str, status: str) -> None:
        with self._lock:
            if turn is not self._turn:
                return
            msg = self._msg(turn.msg_id)
            if msg is None:
                return
            self._flush_locked()
            if status.startswith("[Done]") or status.startswith("[Error]"):
                state = "ok" if status.startswith("[Done]") else "error"
                note = "" if state == "ok" else status[len("[Error]"):].strip()
                for i in range(len(msg["parts"]) - 1, -1, -1):
                    p = msg["parts"][i]
                    if p["kind"] == "call" and p["name"] == name and p["state"] == "run":
                        p["state"], p["note"] = state, note
                        self._emit({"type": "genius", "op": "call", "id": msg["id"], "i": i, "state": state, "note": note})
                        return
                # A result with no visible start (should not happen): show it anyway.
            part = {"kind": "call", "name": name, "state": "run", "note": ""}
            if status.startswith("[Done]") or status.startswith("[Error]"):
                part["state"] = "ok" if status.startswith("[Done]") else "error"
                part["note"] = "" if part["state"] == "ok" else status[len("[Error]"):].strip()
            msg["parts"].append(part)
            self._emit({"type": "genius", "op": "part", "id": msg["id"], "part": dict(part)})

    # -- user actions ------------------------------------------------------------

    def send(self, text: str) -> dict[str, Any]:
        text = str(text or "").strip()
        if not text:
            return {"ok": False, "error": "empty"}
        with self._lock:
            if self._turn is not None:
                return {"ok": False, "error": "busy"}
            user = {"id": self._new_id(), "role": "user", "text": text}
            self._msgs.append(user)
            self._history.append({"role": "user", "content": text})
            self._emit({"type": "genius", "op": "add", "msg": copy.deepcopy(user)})
            bot = self._add_bot()
            self._turn = _Turn(bot["id"])
            self._emit({"type": "genius", "op": "add", "msg": copy.deepcopy(bot)})
            self._emit({"type": "genius", "op": "busy", "busy": True})
            turn = self._turn
            settings = dict(self._get_settings())
            history = list(self._history)
            live_line = self._live_line()
            bridge = self._get_bridge()
        threading.Thread(target=self._work, args=(turn, settings, history, live_line, bridge), daemon=True, name="genius-turn").start()
        return {"ok": True}

    def _work(self, turn: _Turn, settings: dict[str, Any], history: list[dict[str, str]], live_line: str, bridge: Any) -> None:
        ask = self._ask
        if ask is None:
            import genius_client  # deferred: the module is large and only needed once someone chats
            ask = genius_client.ask_genius
        try:
            reply = ask(
                settings, history, live_line,
                bridge=bridge,
                cancel_event=turn.cancel,
                on_tool_call=lambda name, status: self._on_tool_call(turn, name, status),
                on_thinking=lambda chunk: self._push_text(turn, "think", chunk),
                on_content=lambda chunk: self._push_text(turn, "text", chunk),
                confirm=self._confirm,
            )
            err = ""
        except Exception as exc:
            reply, err = "", str(exc)
        self._finish(turn, reply, err)

    def _finish(self, turn: _Turn, reply: str, err: str) -> None:
        with self._lock:
            if turn is not self._turn:
                return                       # stopped/cleared meanwhile: the turn was already closed out
            self._flush_locked()
            msg = self._msg(turn.msg_id)
            self._turn = None
            if msg is None:
                return
            if err:
                shown = err if err.startswith("[") else "Error: " + err
                msg["state"], msg["error"] = "error", shown
                # A request error must not leave the user's message unanswered in the history:
                # Anthropic rejects two user turns in a row, and other providers lose the thread.
                # Phrased as a neutral session note rather than a bare bracketed error string --
                # see the comment on STOPPED above for why that distinction matters.
                self._history.append({
                    "role": "assistant",
                    "content": "(Session note: this turn failed before a reply was produced. %s)" % err,
                })
                self._emit({"type": "genius", "op": "done", "id": msg["id"], "state": "error", "error": shown})
                return
            reply = str(reply or "")
            # The authoritative reply is the LAST round's text: the last text part that comes after the
            # final tool call. Anything earlier is narration from a previous round and is left alone.
            last_call = max((i for i, p in enumerate(msg["parts"]) if p["kind"] == "call"), default=-1)
            tail = [i for i, p in enumerate(msg["parts"]) if p["kind"] == "text" and i > last_call]
            if tail:
                i = tail[-1]
                if msg["parts"][i]["text"] != reply:
                    msg["parts"][i]["text"] = reply
                    self._emit({"type": "genius", "op": "settext", "id": msg["id"], "i": i, "text": reply})
                    self._sent[(msg["id"], i)] = len(reply)
            elif reply:
                msg["parts"].append({"kind": "text", "text": reply})
                self._emit({"type": "genius", "op": "part", "id": msg["id"], "part": {"kind": "text", "text": reply}})
                self._sent[(msg["id"], len(msg["parts"]) - 1)] = len(reply)
            msg["state"] = "done"
            self._history.append({"role": "assistant", "content": reply})
            self._emit({"type": "genius", "op": "done", "id": msg["id"], "state": "done"})

    def stop(self) -> bool:
        with self._lock:
            turn = self._turn
            if turn is None:
                return False
            turn.cancel.set()
            self._flush_locked()
            self._turn = None
            msg = self._msg(turn.msg_id)
            if msg is not None:
                msg["state"] = "stopped"
                for i, p in enumerate(msg["parts"]):
                    if p["kind"] == "call" and p["state"] == "run":
                        p["state"], p["note"] = "error", "stopped"
                        self._emit({"type": "genius", "op": "call", "id": msg["id"], "i": i, "state": "error", "note": "stopped"})
                self._emit({"type": "genius", "op": "done", "id": msg["id"], "state": "stopped"})
            self._history.append({"role": "assistant", "content": STOPPED})
            return True

    def clear(self) -> None:
        with self._lock:
            if self._turn is not None:
                self._turn.cancel.set()
                self._turn = None
            self._msgs = []
            self._history = []
            self._sent = {}
            self._add_bot(GREETING, state="done")
            self._emit({"type": "genius", "op": "clear", "messages": copy.deepcopy(self._msgs)})

    def set_agent(self, slug: str) -> dict[str, Any]:
        slug = str(slug or "").strip()
        with self._lock:
            settings = self._get_settings()
            if slug and slug not in list(settings.get("enabled_agents") or []):
                return {"ok": False, "error": "That agent is not enabled."}
            settings["active_agent"] = slug
            try:
                self._save_settings(settings)
            except OSError as exc:
                return {"ok": False, "error": "Could not save the choice: %s" % exc}
            agent = agent_registry.load_agent(settings, slug) if slug else None
            note = "Switched to %s." % agent["title"] if agent else ("Switched back to stock Genius." if not slug else "Switched to %s." % slug)
            msg = {"id": self._new_id(), "role": "system", "text": note}
            self._msgs.append(msg)
            self._emit({"type": "genius", "op": "add", "msg": copy.deepcopy(msg)})
            self._emit(self._agent_event())
            return {"ok": True}

    def notice(self, text: str) -> None:
        """A one-line system message from outside the chat (e.g. the header's key + model picker)."""
        text = str(text or "").strip()
        if not text:
            return
        with self._lock:
            msg = {"id": self._new_id(), "role": "system", "text": text}
            self._msgs.append(msg)
            self._emit({"type": "genius", "op": "add", "msg": copy.deepcopy(msg)})

    def announce_agent(self) -> None:
        """Tell the page the agent list / active agent / model changed (Preferences edited them)."""
        with self._lock:
            self._emit(self._agent_event())

    def close(self) -> None:
        """Shutdown: cancel the running turn and the flush timer. Never joins the worker
        (it may be inside a 6-14 s bridge call); it is a daemon thread."""
        with self._lock:
            self._closed = True
            if self._turn is not None:
                self._turn.cancel.set()
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    # -- demo (the preview's mock conversation) ------------------------------------

    def load_demo(self) -> None:
        """The exact conversation previews/redesign-round/shared/shared.js mocks, so the
        real page can be pixel-compared with shots/extra__a-genius.png."""
        with self._lock:
            self._demo = True
            self._msgs = []
            self._history = []
            self._next_id = 1

            def user(text: str) -> None:
                self._msgs.append({"id": self._new_id(), "role": "user", "text": text})

            def bot(text: str, calls: list[tuple[str, str]]) -> None:
                parts: list[dict[str, Any]] = [{"kind": "text", "text": text}]
                parts += [{"kind": "call", "name": n, "state": s, "note": ""} for n, s in calls]
                self._msgs.append({"id": self._new_id(), "role": "bot", "parts": parts, "state": "done"})

            user("Make a 4-bar bassline in F♯ minor on the Bass track and name the clip “Sub Walk”.")
            bot("Done — I wrote 16 notes into a new 4-bar clip on **2 · Bass** and named it “Sub Walk”.",
                [("live_create_clip", "ok"), ("live_write_notes", "ok"), ("live_update_clip", "ok")])
            user("Now duplicate it into the next three scenes and mutate each one a little.")
            bot("Working…", [("live_duplicate", "run")])
