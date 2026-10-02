"""Build the Genius Guide v2 PDF set (5 books).

    python docs/guide-v2-build/build_guide_v2.py

Book 5's action list is NOT hand-maintained. It is extracted from
`app/genius_client.py`'s LIVE_TOOLS at build time via AST, then cross-checked
against the human annotations in data_actions.py. If a tool is added, removed or
renamed in code without updating the annotations, this script raises before
writing a single PDF -- which is exactly how the v1 guide silently went stale at
108 tools while the code had moved on to 122.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

import theme as T
from data_actions import CATEGORIES
from data_creative import THEMES
from data_limits import GROUPS, MISCONCEPTIONS
from data_prompts import SECTIONS

REPO = HERE.parent.parent
CLIENT = REPO / "app" / "genius_client.py"
OUT_DIR = REPO / "Genius User Guide"

VERSION = "v1.0.0"
LIVE_TESTED = "Ableton Live 12.4.15b3"
DB_DATASETS = 8


# ── Truth extraction ─────────────────────────────────────────────────────────
def extract_tools() -> dict[str, dict]:
    """Parse LIVE_TOOLS out of genius_client.py without importing it."""
    tree = ast.parse(CLIENT.read_text(encoding="utf-8"))
    node = None
    for n in tree.body:
        targets = n.targets if isinstance(n, ast.Assign) else (
            [n.target] if isinstance(n, ast.AnnAssign) else [])
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "LIVE_TOOLS":
                node = n.value
    if node is None:
        raise SystemExit("LIVE_TOOLS not found in genius_client.py")

    out: dict[str, dict] = {}
    for el in node.elts:
        if not (isinstance(el, ast.Call) and getattr(el.func, "id", None) == "_tool"):
            continue
        a = el.args
        name = ast.literal_eval(a[0])
        desc = ast.literal_eval(a[1]) if len(a) > 1 else ""
        props = (ast.literal_eval(a[2]) if len(a) > 2 else {}) or {}
        req = (ast.literal_eval(a[3]) if len(a) > 3 else []) or []
        params = []
        for pn, ps in props.items():
            ps = ps if isinstance(ps, dict) else {}
            ptype = ps.get("type", "")
            if ptype == "array":
                items = ps.get("items") or {}
                inner = items.get("type", "")
                ptype = f"array of {inner}" if inner else "array"
                if items.get("enum"):
                    ptype = "array: " + " | ".join(str(e) for e in items["enum"])
            elif ps.get("enum"):
                ptype = " | ".join(str(e) for e in ps["enum"])
            params.append({
                "name": pn, "type": ptype, "required": pn in req,
                "desc": ps.get("description", ""),
            })
        params.sort(key=lambda p: (not p["required"], p["name"]))
        out[name] = {"name": name, "desc": desc, "params": params}
    return out


def validate(tools: dict[str, dict]) -> None:
    """Fail loudly on any drift between code, the action notes and the prompts."""
    code = set(tools)

    documented: list[str] = []
    for _cat, _blurb, items in CATEGORIES:
        documented.extend(i[0] for i in items)
    docset = set(documented)

    dupes = sorted({d for d in documented if documented.count(d) > 1})
    missing = sorted(code - docset)
    extra = sorted(docset - code)

    problems = []
    if dupes:
        problems.append(f"documented twice in data_actions.py: {dupes}")
    if missing:
        problems.append(f"in code but NOT documented in data_actions.py: {missing}")
    if extra:
        problems.append(f"documented but NO LONGER in code: {extra}")

    bad_refs: set[str] = set()
    for _sec, _blurb, prompts in SECTIONS:
        for p in prompts:
            bad_refs |= {a for a in p[3] if a not in code}
    if bad_refs:
        problems.append(f"prompts reference nonexistent actions: {sorted(bad_refs)}")

    bad_creative: set[str] = set()
    for _th, _blurb, ideas in THEMES:
        for idea in ideas:
            bad_creative |= {a for a in idea[3] if a not in code}
    if bad_creative:
        problems.append(f"creative ideas reference nonexistent actions: {sorted(bad_creative)}")

    if problems:
        raise SystemExit("GUIDE IS OUT OF DATE WITH THE CODE:\n  - " + "\n  - ".join(problems))

    print(f"  validated: {len(code)} tools, all annotated, all references resolve")


# ── Helpers ──────────────────────────────────────────────────────────────────
def esc(text: str) -> str:
    """Escape authored prose, tidying ASCII double-hyphens into em dashes."""
    return re.sub(r"(?<=\s)--(?=\s)", "—", escape(str(text)))


def esc_verbatim(text: str) -> str:
    """Escape text quoted from source. No tidying -- Book 5 claims this is verbatim."""
    return escape(str(text))


def mono(text: str) -> str:
    return f'<font face="Courier-Bold" color="#0F766E">{esc(text)}</font>'


def badge_row(pairs, gap=4):
    """Lay several badges out side by side."""
    cells, widths = [], []
    for label, color in pairs:
        b = T.badge(label, color)
        cells.append(b)
        widths.append(b._argW[0])
        cells.append("")
        widths.append(gap)
    cells, widths = cells[:-1], widths[:-1]
    t = Table([cells], colWidths=widths, rowHeights=[12])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build(path: Path, running: str, footer: str, story: list) -> None:
    d = T.doc(str(path), running)
    d.build(story, canvasmaker=T.make_canvas(running, footer))
    print(f"  wrote {path.name}")


FOOTER = f"Live Actions {VERSION}  |  128 actions  |  {DB_DATASETS} bundled datasets"


# ── Book 1: Overview ─────────────────────────────────────────────────────────
def book1(s, tools):
    st: list = []
    T.cover(
        st, s, "1", "What This Actually Is",
        "An orientation to Live Actions Genius",
        "Genius is an AI assistant wired directly into a running copy of Ableton Live. It can read "
        "your Set, write real MIDI into it, load and configure devices, drive the transport, and "
        "measure your audio — through 128 purpose-built actions rather than by pretending to type "
        "at your keyboard. This book explains what that means in practice, what the moving parts are, "
        "and how to get a useful answer out of it on the first try.",
        ["How the pieces fit together, and what breaks when one is missing",
         "The three things Genius can do that a normal chatbot cannot",
         "Where its music knowledge comes from, and why there are two sources",
         "Choosing a chat model for the job in front of you",
         "The habits that separate good results from frustrating ones"],
        f"Built against Live Actions {VERSION}. Action surface extracted directly from the "
        f"shipping code. Behaviour verified against {LIVE_TESTED}.")

    st += [Paragraph("The one-paragraph version", s["h1"]), T.rule()]
    st.append(Paragraph(
        "You type a request in plain English. Genius decides which of its 128 actions to call, in "
        "what order, with what arguments. Those calls travel over a local bridge into a Max for Live "
        "device sitting in your Set, which talks to Ableton through Live's own scripting interface. "
        "Real things change in your project. Genius reads the results back and tells you what "
        "happened. Your audio and project files stay on your machine. What you type, and what "
        "the actions read back from your Set and the knowledge base, is sent to the AI provider "
        "whose API key you entered, as part of the conversation.", s["body"]))

    st += [Paragraph("The moving parts", s["h1"]), T.rule()]
    st.append(Paragraph(
        "Five things have to be true for a Live action to work. When something is broken, it is "
        "almost always one of these, and they are listed in the order worth checking.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("Part", "What it does", "How you know it's wrong")]]
    for part, does, wrong in [
        ("Ableton Live", "Hosts your project and does the actual work. Live 12 with Max for Live.",
         "Nothing responds at all; live_connect fails immediately."),
        ("The bridge device", "A Max for Live device in your Set. Without it loaded, Live cannot "
         "hear the app, no matter how healthy everything else is.",
         "live_connect fails but Live is clearly running and fine."),
        ("Live Actions", "The desktop app. Holds your settings, ports, folder paths and API keys.",
         "Settings look right but the app can't reach the bridge — check the port pair."),
        ("A chat model", "The brain choosing which actions to call. Needs your own API key from xAI, "
         "OpenAI, Google or Anthropic, entered in Preferences. Your provider bills you for use.",
         "Actions run but the choices are poor, or it narrates work it never did."),
        ("The knowledge base", "A bundled database of 8 datasets, plus a Knowledge folder for your own "
         "notes and manuals. Genius searches these before answering from memory.",
         "Theory answers are vague or it says it has no source for something it should know."),
    ]:
        rows.append([Paragraph(f"<b>{esc(part)}</b>", s["cell"]),
                     Paragraph(esc(does), s["cell"]), Paragraph(esc(wrong), s["cell"])])
    st.append(T.data_table(rows, [88, 218, 226]))

    st.append(Spacer(1, 10))
    st.append(T.callout([
        Paragraph("If only one thing sticks", s["h3"]),
        Paragraph(
            "The bridge device has to be present <b>in the Set you have open</b>. It is not a global "
            "setting. Open a different project and the device is not there until you add it — which "
            "is the single most common reason Genius appears to have stopped working.", s["note"]),
    ]))

    st += [Paragraph("What makes this different from a chatbot", s["h1"]), T.rule()]
    st.append(Paragraph(
        "Any AI can describe a chord progression. Three things here are genuinely different in kind, "
        "not just degree.", s["body"]))
    for n, title, body in [
        ("1", "It changes your actual project",
         "When Genius writes a bassline, real MIDI notes appear in a real clip that you can then edit "
         "by hand. It is not producing a description, a MIDI file to import, or a suggestion. The "
         "change has already happened in Live by the time it finishes replying."),
        ("2", "The music comes from real algorithms, not improvisation",
         "Euclidean rhythms use Bjorklund's algorithm. Key detection uses Krumhansl-Schmuckler. "
         "Chord voicings follow actual voice-leading rules. The language model decides <i>which</i> "
         "generator to call and with what settings — it does not invent notes one at a time. That is "
         "why the same request twice gives you the same pattern twice, and why the output is "
         "musically coherent rather than plausible-sounding."),
        ("3", "It can measure what it did",
         "Genius can capture Live's output and analyse it for real: LUFS, true peak, crest factor, "
         "spectrum. That makes a closed loop possible — change something, measure it, adjust based on "
         "the result. This is the one capability that feels like an assistant rather than a tool, and "
         "it is covered in Book 2."),
    ]:
        st.append(T.callout([
            Paragraph(f"{n}. {title}", s["h3"]),
            Paragraph(body, s["note"]),
        ], fill=T.BAND2, border=T.LINE))
        st.append(Spacer(1, 6))

    st.append(PageBreak())
    st += [Paragraph("The 128 actions at a glance", s["h1"]), T.rule()]
    st.append(Paragraph(
        "Book 5 documents every one of these in full. This is the shape of the toolset, so you know "
        "roughly what exists before you go looking.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("Family", "Count", "What it covers")]]
    for cat, _blurb, items in CATEGORIES:
        rows.append([Paragraph(f"<b>{esc(cat)}</b>", s["cell"]),
                     Paragraph(str(len(items)), s["cell"]),
                     Paragraph(esc(_blurb.split(".")[0] + "."), s["cell"])])
    rows.append([Paragraph("<b>Total</b>", s["cellb"]),
                 Paragraph(f"<b>{len(tools)}</b>", s["cellb"]), Paragraph("", s["cell"])])
    st.append(T.data_table(rows, [150, 38, 344]))

    st += [Paragraph("Where its knowledge comes from", s["h1"]), T.rule()]
    st.append(Paragraph(
        "There are two separate local sources, and Genius is instructed to try them in a strict "
        "order. Knowing which one an answer came from tells you how much to trust it.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("Source", "Contents", "When it's used")]]
    rows += [
        [Paragraph("<b>Music/Audio database</b><br/>" + mono("library_db_search"), s["cell"]),
         Paragraph(f"{DB_DATASETS} bundled datasets: beat-making recipes by genre, preset-rack "
                   "breakdowns, mix engineering figures, Vital sound design, beginner music theory, "
                   "notes on Ableton remote-control projects. You can add your own.", s["cell"]),
         Paragraph("<b>Always first.</b> Fast indexed search over material that was deliberately "
                   "curated and structured.", s["cell"])],
        [Paragraph("<b>Knowledge folder</b><br/>" + mono("library_search") + "<br/>" + mono("library_read"), s["cell"]),
         Paragraph("Your own files: notes, manuals you own, exports. It ships empty; drop "
                   ".md, .txt or .pdf files into it.", s["cell"]),
         Paragraph("<b>Fallback</b>, when the database has nothing — typically a named "
                   "third-party plugin or a specific piece of hardware you have a manual for.", s["cell"])],
    ]
    st.append(T.data_table(rows, [122, 220, 190]))
    st.append(Spacer(1, 8))
    st.append(Paragraph(
        "Both live on your own drive and are searched locally. The passages a search finds are then "
        "sent to your AI provider so the model can read them. The router document that decides "
        "between sources, <font face=\"Courier\">INDEX.md</font>, ships with the app; put your own "
        "INDEX.md in the Knowledge folder to replace it.", s["small"]))

    st.append(PageBreak())
    st += [Paragraph("Choosing a model", s["h1"]), T.rule()]
    st.append(Paragraph(
        "Genius runs on whichever chat model you configure in Settings, and the choice matters more "
        "than people expect. Driving six dependent tool calls in the right order is a genuinely "
        "different skill from explaining modal harmony well. Every prompt in Book 3 carries a "
        "suggested tag.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("Tag", "Best at", "Reach for it when")]]
    for tag in ("CLAUDE", "GPT", "GROK", "GEMINI", "ANY"):
        rows.append([
            badge_row([(tag, T.MODEL_COLORS[tag])]),
            Paragraph(esc(T.MODEL_WHY[tag]), s["cell"]),
            Paragraph(esc({
                "CLAUDE": "The job is multi-step, touches several tracks, or must not go wrong.",
                "GPT": "You want a solid all-rounder, or Claude is unavailable.",
                "GROK": "You want teaching, theory, or a long discursive answer.",
                "GEMINI": "You want one fact, fast and cheap.",
                "ANY": "It's a single obvious action with no ambiguity.",
            }[tag]), s["cell"]),
        ])
    st.append(T.data_table(rows, [58, 230, 244]))

    st += [Paragraph("Getting good results", s["h1"]), T.rule()]
    for head, body in [
        ("Let it look before it leaps",
         "The highest-leverage habit there is. “Read my Set, then…” costs one action and "
         "prevents most of the failures in this guide. A model that has read your project makes "
         "dramatically better choices than one guessing at its shape."),
        ("Name things, don't number them",
         "Track numbers are positions as Live displays them — a track <i>called</i> “Track 3” "
         "may sit in position 7, and digits in a name mean nothing. Say “the track called Bass”, "
         "or ask what's selected and say “this one”."),
        ("Say where output should go",
         "“Put the variation in slot 4” protects the original. Without it you may get the "
         "source overwritten, which is undoable but annoying."),
        ("Ask it to check unfamiliar parameters",
         "“Tell me the range first” makes it call " + mono("live_read_param_range") +
         " instead of assuming a filter cutoff runs 0–1 when it actually runs 0–127."),
        ("Verify anything that matters",
         "A model can produce a confident summary of work it did not do. Snapshot before, diff "
         "after, or simply re-read the thing it claims to have changed. Believe the read, not the "
         "summary. This is the most important habit in the entire guide."),
        ("Break big builds into checkpoints",
         "A twelve-step build that goes wrong at step four spends the next eight steps compounding "
         "the error. Stop and look at stages you can actually verify."),
    ]:
        st.append(Paragraph(head, s["h3"]))
        st.append(Paragraph(body, s["body"]))

    st.append(Spacer(1, 8))
    st.append(T.callout([
        Paragraph("Where to go next", s["h3"]),
        Paragraph(
            "<b>Book 2</b> makes the case for what to actually try. <b>Book 3</b> is the prompt "
            "library — paste-ready, tagged by difficulty and model. <b>Book 4</b> is the honest "
            "list of what this cannot do, and is worth reading <i>before</i> you hit a limit rather "
            "than after. <b>Book 5</b> documents all 128 actions individually.", s["note"]),
    ]))
    return st


# ── Book 2: Creative playbook ────────────────────────────────────────────────
def book2(s, tools):
    st: list = []
    T.cover(
        st, s, "2", "What To Actually Do With It",
        "A creative playbook",
        "Book 3 tells you what to type. This one argues for what is worth trying. The workflows "
        "here are chosen because delegating them changes what you would realistically attempt — "
        "not merely how quickly you would do something you were going to do anyway.",
        [f"{sum(len(i) for _t, _b, i in THEMES)} worked ideas across {len(THEMES)} themes",
         "Beating the blank page, and why disposability is the point",
         "Delegating the boring half of production",
         "Learning theory with your own project as the worked example",
         "Things that are musically interesting but impractical by hand",
         "Closed loops: change it, measure it, adjust"],
        "Every idea names the actions that carry it, so you can cross-reference Book 5 for the detail.")

    st.append(Paragraph(
        "A note on how to read this: each idea has a rough prompt attached, but they are starting "
        "points rather than incantations. Genius responds to intent, so adapt the wording to your "
        "project. The actions listed underneath are what the request is expected to reach for.",
        s["body"]))
    st.append(Spacer(1, 6))

    for theme, blurb, ideas in THEMES:
        st.append(Paragraph(esc(theme), s["h1"]))
        st.append(T.rule())
        st.append(Paragraph(esc(blurb), s["body"]))
        for title, idea, how, actions in ideas:
            block = [
                Paragraph(esc(title), s["h2"]),
                Paragraph(esc(idea), s["body"]),
                Paragraph("<b>Try:</b> " + esc(how), s["prompt"]),
                Paragraph("<b>Uses:</b> " + " · ".join(mono(a) for a in actions), s["small"]),
            ]
            st.append(KeepTogether(block))
            st.append(Spacer(1, 7))
        st.append(Spacer(1, 4))

    st.append(PageBreak())
    st.append(Paragraph("A suggested first session", s["h1"]))
    st.append(T.rule())
    st.append(Paragraph(
        "If you have never used Genius for real work, this sequence gets you from nothing to a "
        "finished sketch while touching most of what matters. Expect it to take under an hour.",
        s["body"]))
    steps = [
        ("Confirm the connection", "“Connect to Ableton and tell me what you can see.”",
         "If this fails, fix it before anything else. Book 4 has the triage order."),
        ("Set the foundation", "“Set the tempo to 124 and the global scale to G minor.”",
         "Setting the scale makes everything generated later agree with Live's own scale awareness."),
        ("Build the skeleton", "“Make four MIDI tracks named Drums, Bass, Chords and Lead, each a "
         "different colour, and put a Drum Rack on Drums.”",
         "One sentence, roughly six actions."),
        ("Get a beat down", "“Read my drum rack, then write a 2-bar house beat using only pads that "
         "actually have samples loaded.”",
         "The read-first habit, immediately. Without it you get notes on empty pads."),
        ("Add harmony", "“Write a i–VI–III–VII progression in G minor on the Chords track, "
         "then a walking bass underneath it on Bass.”",
         "The bass has to read the chords first — let it."),
        ("Make it move", "“Put a slow sine filter sweep on the Chords track, one cycle per clip.”",
         "Procedural movement is the fastest cure for a static loop."),
        ("Arrange it", "“Build a 32-bar arrangement from these clips: 8 intro, 16 main, 8 outro, "
         "with locators.”",
         "Instant, not real time — this is copying, not recording."),
        ("Check your work", "“Audit the mix and tell me the three biggest problems. Don't fix "
         "anything yet.”",
         "Structural, not acoustic. Ask for the list before the fixes."),
    ]
    rows = [[Paragraph(h, s["cellb"]) for h in ("#", "Step", "Prompt", "Why")]]
    for i, (stepname, prompt, why) in enumerate(steps, 1):
        rows.append([Paragraph(str(i), s["cell"]),
                     Paragraph(f"<b>{esc(stepname)}</b>", s["cell"]),
                     Paragraph(f"<i>{esc(prompt)}</i>", s["cell"]),
                     Paragraph(esc(why), s["cell"])])
    st.append(T.data_table(rows, [16, 86, 216, 214]))
    st.append(Spacer(1, 10))
    st.append(T.callout([
        Paragraph("The thing most people get wrong", s["h3"]),
        Paragraph(
            "Treating Genius as a vending machine — one big request, one finished result. It is far "
            "better as a conversation: read, propose, adjust, commit. The prompts that fail are "
            "almost always the ones that asked for twelve things at once with no checkpoint in the "
            "middle.", s["note"]),
    ]))
    return st


# ── Book 3: Prompt library ───────────────────────────────────────────────────
def book3(s, tools):
    total = sum(len(p) for _sec, _b, p in SECTIONS)
    st: list = []
    T.cover(
        st, s, "3", "The Prompt Library",
        f"{total} paste-ready prompts, tagged and categorised",
        "Every prompt here can be pasted into Genius as-is. Each one is tagged with how demanding "
        "it is, which chat model suits it, and which actions it is expected to call — so you can "
        "see what a request is about to do before you run it. They run from single-action starters "
        "to expert closed loops that measure their own results.",
        [f"{total} prompts across {len(SECTIONS)} categories",
         "Complexity tags from Starter to Expert",
         "A suggested model for every prompt, and why",
         "The expected action list for each, cross-referenced to Book 5",
         "Practical notes: what to expect, what it costs, what to watch for"],
        "Every action named in this book is verified at build time to exist in the shipping code.")

    st.append(Paragraph("How to read an entry", s["h1"]))
    st.append(T.rule())
    rows = [
        [Paragraph("<b>Complexity</b>", s["cell"]),
         Paragraph("How much can go wrong. <b>Starter</b> is one action with no prerequisites. "
                   "<b>Intermediate</b> chains a few, or needs real parameters. <b>Advanced</b> reads "
                   "state then acts on it. <b>Expert</b> runs loops, verifies itself, or builds for a "
                   "long time unattended.", s["cell"])],
        [Paragraph("<b>Model</b>", s["cell"]),
         Paragraph("A suggestion, not a requirement. It reflects what the job actually demands — "
                   "precise sequencing, long-form explanation, or just speed.", s["cell"])],
        [Paragraph("<b>Uses</b>", s["cell"]),
         Paragraph("The actions the prompt is expected to call. Genius may choose differently; this "
                   "tells you the intended shape and points you at Book 5 for the detail.", s["cell"])],
        [Paragraph("<b>Note</b>", s["cell"]),
         Paragraph("What to expect, what it costs, or the trap to avoid.", s["cell"])],
    ]
    st.append(T.data_table(rows, [70, 462], header=False))
    st.append(Spacer(1, 8))
    st.append(Paragraph("Complexity tags used in this book:", s["h3"]))
    st.append(badge_row([(c, col) for c, col in T.COMPLEXITY_COLORS.items()], gap=6))
    st.append(Spacer(1, 10))

    counts = [[Paragraph(h, s["cellb"]) for h in ("Category", "Prompts")]]
    for sec, _b, prompts in SECTIONS:
        counts.append([Paragraph(esc(sec), s["cell"]), Paragraph(str(len(prompts)), s["cell"])])
    counts.append([Paragraph("<b>Total</b>", s["cellb"]), Paragraph(f"<b>{total}</b>", s["cellb"])])
    st.append(T.data_table(counts, [420, 112]))
    st.append(PageBreak())

    for sec, blurb, prompts in SECTIONS:
        st.append(Paragraph(esc(sec), s["h1"]))
        st.append(T.rule())
        st.append(Paragraph(esc(blurb), s["body"]))
        for ptext, cx, model, actions, note in prompts:
            body = esc(ptext).replace("\n", "<br/>")
            block = [
                badge_row([(cx, T.COMPLEXITY_COLORS[cx]), (model, T.MODEL_COLORS[model])]),
                Spacer(1, 3),
                Paragraph(f"“{body}”", s["prompt"]),
                Paragraph("<b>Uses:</b> " + " · ".join(mono(a) for a in actions), s["small"]),
                Paragraph("<b>Note:</b> " + esc(note), s["small"]),
            ]
            st.append(KeepTogether(T.callout(block, fill=T.WHITE, border=T.HAIR, pad=7)))
            st.append(Spacer(1, 5))
        st.append(Spacer(1, 6))

    st.append(PageBreak())
    st.append(Paragraph("Writing your own", s["h1"]))
    st.append(T.rule())
    st.append(Paragraph(
        "The prompts that work share a shape. Most of it is just being explicit about things you "
        "were assuming.", s["body"]))
    for head, body in [
        ("Start with a read when the request depends on what's there",
         "“Read my drum rack, <i>then</i> write a beat using loaded pads only” succeeds where "
         "“write me a beat” writes notes to empty pads."),
        ("Say where the output goes",
         "Naming a destination slot turns a destructive operation into a non-destructive one."),
        ("Give it a measurable target when there is one",
         "“Until it measures between −15 and −13 LUFS” is actionable. “Until it sounds "
         "loud enough” is not — and Book 4 explains why it cannot hear it anyway."),
        ("Ask for the plan before the execution on anything big",
         "“Tell me what you're going to do first” costs one turn and has saved a great many "
         "projects."),
        ("Cap the iterations on anything that loops",
         "Each pass of a record-and-measure loop costs real wall-clock time. “Maximum five "
         "attempts” keeps it bounded."),
        ("Ask for verification, not reassurance",
         "“Diff it and show me what changed” beats “did that work?”, because the first "
         "one is checked against Live and the second one is a model's opinion of its own work."),
    ]:
        st.append(Paragraph(head, s["h3"]))
        st.append(Paragraph(body, s["body"]))
    return st


# ── Book 4: Limits ───────────────────────────────────────────────────────────
def book4(s, tools):
    n = sum(len(g[2]) for g in GROUPS)
    st: list = []
    T.cover(
        st, s, "4", "What It Cannot Do",
        "Honest limits, with the evidence",
        "The most useful documentation any tool can give you is a clear account of where it stops. "
        "Everything here is traceable to something real: a probe run against a live Ableton session, "
        "a verification pass, or the shape of the architecture itself. Nothing in this book is a "
        "guess, and several entries describe actions that ship today and quietly do nothing.",
        [f"{n} documented limits across {len(GROUPS)} categories",
         "Actions that ship but are confirmed inert — and what to do instead",
         "Limits that come from Ableton rather than from this app",
         "Why it cannot hear your music, and what to use instead",
         "The failure modes of the chat model itself",
         "Common misconceptions that are not actually limits"],
        f"Evidence drawn from live probe runs against {LIVE_TESTED}, the LOM truth table, and the "
        f"{VERSION} verification pass.")

    st.append(T.callout([
        Paragraph("Read this one first", s["h3"]),
        Paragraph(
            "Most frustration with Genius comes from expecting one of the things in this book. Ten "
            "minutes here will save you an afternoon of trying to make an inert action work. The "
            "single most important entry is “It cannot hear your music” — it is the "
            "assumption people most often make without noticing.", s["note"]),
    ], fill=T.BAND, border=T.TEAL))
    st.append(Spacer(1, 10))

    for group, blurb, limits in GROUPS:
        st.append(Paragraph(esc(group), s["h1"]))
        st.append(T.rule())
        st.append(Paragraph(esc(blurb), s["body"]))
        for head, body, ev in limits:
            block = [
                Paragraph(esc(head), s["h2"]),
                Paragraph(esc(body), s["body"]),
                Paragraph("<b>Evidence:</b> " + esc(ev), s["small"]),
            ]
            st.append(KeepTogether(block))
            st.append(Spacer(1, 7))
        st.append(Spacer(1, 4))

    st.append(PageBreak())
    st.append(Paragraph("Things that are not actually limits", s["h1"]))
    st.append(T.rule())
    st.append(Paragraph(
        "These come up often enough to be worth correcting directly.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("The assumption", "Actually")]]
    for claim, reality in MISCONCEPTIONS:
        rows.append([Paragraph(f"<i>{esc(claim)}</i>", s["cell"]), Paragraph(esc(reality), s["cell"])])
    st.append(T.data_table(rows, [176, 356]))

    st.append(Spacer(1, 12))
    st.append(Paragraph("Triage order when something breaks", s["h1"]))
    st.append(T.rule())
    st.append(Paragraph(
        "Work down this list. It is ordered by how common the cause is, not how likely it is to be "
        "interesting.", s["body"]))
    rows = [[Paragraph(h, s["cellb"]) for h in ("#", "Check", "How", "If that's it")]]
    for i, (check, how, fix) in enumerate([
        ("Is the bridge device in THIS Set?",
         "Look in Live for the Live Actions device.",
         "Add it. This is the most common cause by a wide margin — it is per-project, not global."),
        ("Is a dialog blocking Live?",
         mono("live_read_dialog"),
         "A stuck modal silently blocks every other action. Dismiss it and retry."),
        ("Does the connection work at all?",
         mono("live_connect"),
         "If this fails, nothing downstream can work. Check Live is running and the ports match."),
        ("Is Live overloaded?",
         mono("live_read_cpu"),
         "A struggling audio engine makes calls time out. Freeze or remove something."),
        ("Is the action one of the inert ones?",
         "Check the first section of this book.",
         "It will appear to succeed and change nothing. Use the documented alternative."),
        ("Did it actually do what it claimed?",
         mono("live_session_diff") + " or just re-read it.",
         "If the diff is empty, it did not. Believe the read, not the summary."),
    ], 1):
        rows.append([Paragraph(str(i), s["cell"]), Paragraph(f"<b>{esc(check)}</b>", s["cell"]),
                     Paragraph(how, s["cell"]), Paragraph(esc(fix), s["cell"])])
    st.append(T.data_table(rows, [16, 150, 128, 238]))
    return st


# ── Book 5: Complete action reference ────────────────────────────────────────
def book5(s, tools):
    st: list = []
    T.cover(
        st, s, "5", "Every Action, Explained",
        f"The complete reference — all {len(tools)} actions",
        "Every action Genius can take, with the exact name it is called by, what it does in plain "
        "English, whether Ableton has to be running, how expensive it is, and every argument it "
        "accepts. The names, descriptions and arguments in this book are extracted directly from "
        "the shipping source at build time, so they cannot drift out of date the way a hand-written "
        "list does.",
        [f"All {len(tools)} actions in {len(CATEGORIES)} families",
         "A plain-English explanation of each, not just its machine description",
         "Cost weighting, so you know what's cheap and what's expensive",
         "Whether Ableton needs to be running — more actions work offline than people expect",
         "Every argument, which are required, and what each one means",
         "Inert and unreliable actions flagged in place"],
        f"Extracted from app/genius_client.py at build time. Behaviour verified against {LIVE_TESTED}.")

    st.append(Paragraph("How to read an entry", s["h1"]))
    st.append(T.rule())
    rows = [[Paragraph(h, s["cellb"]) for h in ("Field", "Meaning")]]
    rows += [
        [Paragraph("<b>Weight</b>", s["cell"]),
         Paragraph("Roughly what the call costs to run. " + "; ".join(
             f"<b>{k}</b> — {v}" for k, v in T.WEIGHT_MEANING.items()) + ".", s["cell"])],
        [Paragraph("<b>Needs Live</b>", s["cell"]),
         Paragraph("<b>Yes</b> — requires Ableton running with the bridge device loaded. "
                   "<b>No</b> — runs entirely locally; Ableton can be closed. "
                   "<b>Hybrid</b> — computes locally, then writes the result into Live.", s["cell"])],
        [Paragraph("<b>In plain terms</b>", s["cell"]),
         Paragraph("What it actually does and why you'd want it — written for a musician, not a "
                   "developer.", s["cell"])],
        [Paragraph("<b>Machine description</b>", s["cell"]),
         Paragraph("The exact text Genius itself sees when deciding whether to call this action. "
                   "Extracted verbatim from the source.", s["cell"])],
        [Paragraph("<b>Arguments</b>", s["cell"]),
         Paragraph("Every parameter, required ones first. You rarely need to supply these yourself "
                   "— Genius fills them in — but they tell you exactly what the action can be "
                   "asked to vary.", s["cell"])],
        [Paragraph("<b>Note</b>", s["cell"]),
         Paragraph("Practical guidance: gotchas, costs, whether it's destructive, and any known "
                   "problems.", s["cell"])],
    ]
    st.append(T.data_table(rows, [112, 420]))
    st.append(Spacer(1, 8))
    st.append(Paragraph("Weight scale used throughout:", s["h3"]))
    st.append(badge_row([(k, v) for k, v in T.WEIGHT_COLORS.items()], gap=6))
    st.append(Spacer(1, 10))
    st.append(T.callout([
        Paragraph("Flagged actions", s["h3"]),
        Paragraph(
            "Five actions in this book carry a warning in their note: four are confirmed inert or "
            "unreliable, and one is shipping but under-tested. They are documented rather than "
            "hidden because they are still in the tool list and Genius may still call them. Book 4 "
            "has the full evidence.", s["note"]),
    ], fill=T.BAND2, border=T.LINE))
    st.append(PageBreak())

    # Family index
    st.append(Paragraph("The families", s["h1"]))
    st.append(T.rule())
    rows = [[Paragraph(h, s["cellb"]) for h in ("Family", "n", "Actions")]]
    for cat, _blurb, items in CATEGORIES:
        names = ", ".join(i[0] for i in items)
        rows.append([Paragraph(f"<b>{esc(cat)}</b>", s["cell"]),
                     Paragraph(str(len(items)), s["cell"]),
                     Paragraph(f'<font face="Courier" size="7">{esc(names)}</font>', s["cell"])])
    st.append(T.data_table(rows, [124, 20, 388]))
    st.append(PageBreak())

    for cat, blurb, items in CATEGORIES:
        st.append(Paragraph(esc(cat), s["h1"]))
        st.append(T.rule())
        st.append(Paragraph(esc(blurb), s["body"]))
        st.append(Spacer(1, 4))

        for name, plain, live, weight, note in items:
            meta = tools[name]
            header = Table(
                [[Paragraph(f'<font face="Courier-Bold" size="10.5" color="#0F172A">{esc(name)}</font>',
                            s["cell"]),
                  badge_row([(weight, T.WEIGHT_COLORS[weight]),
                             (f"Live: {live}", T.TEAL_DK if live == "Yes"
                              else (T.MUTE if live == "No" else T.SLATE))])]],
                colWidths=[300, 232])
            header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, T.TEAL),
            ]))

            intro = [header, Spacer(1, 4), Paragraph(esc(plain), s["body"])]
            st.append(KeepTogether(intro))

            st.append(Paragraph(
                "<b>Machine description:</b> <i>" + esc_verbatim(meta["desc"]) + "</i>", s["small"]))

            if meta["params"]:
                prows = [[Paragraph(h, s["cellb"]) for h in ("Argument", "Type", "", "What it's for")]]
                for p in meta["params"]:
                    prows.append([
                        Paragraph(f'<font face="Courier">{esc(p["name"])}</font>', s["cell"]),
                        Paragraph(f'<font size="7">{esc(p["type"])}</font>', s["cell"]),
                        Paragraph('<font color="#B91C1C" size="7"><b>req</b></font>'
                                  if p["required"] else '<font color="#94A3B8" size="7">opt</font>',
                                  s["cell"]),
                        Paragraph(f'<font size="7.6">{esc_verbatim(p["desc"]) or "—"}</font>', s["cell"]),
                    ])
                st.append(T.data_table(prows, [104, 96, 26, 306], font_size=7.6))
            else:
                st.append(Paragraph("<b>Arguments:</b> none — just call it.", s["small"]))

            flagged = any(k in note for k in ("INERT", "UNRELIABLE", "least battle-tested"))
            st.append(T.callout(
                [Paragraph("<b>Note:</b> " + esc(note), s["note"])],
                fill=T.colors.HexColor("#FEF2F2") if flagged else T.BAND,
                border=T.colors.HexColor("#B91C1C") if flagged else T.TEAL, pad=6))
            st.append(Spacer(1, 11))
        st.append(PageBreak())

    st.append(Paragraph("Alphabetical index", s["h1"]))
    st.append(T.rule())
    st.append(Paragraph(
        f"All {len(tools)} actions with their family and weight.", s["body"]))
    lookup = {n: (cat, w) for cat, _b, items in CATEGORIES for n, _p, _l, w, _nt in items}
    rows = [[Paragraph(h, s["cellb"]) for h in ("Action", "Family", "Weight")]]
    for name in sorted(tools):
        cat, w = lookup[name]
        rows.append([
            Paragraph(f'<font face="Courier" size="7.6">{esc(name)}</font>', s["cell"]),
            Paragraph(f'<font size="7.6">{esc(cat)}</font>', s["cell"]),
            Paragraph(f'<font size="7.6" color="{T.WEIGHT_COLORS[w].hexval()[2:]}">'
                      f'<b>{esc(w)}</b></font>'.replace("color=\"", "color=\"#"), s["cell"]),
        ])
    st.append(T.data_table(rows, [196, 216, 120], font_size=7.6))
    return st


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    print("Genius User Guide")
    tools = extract_tools()
    print(f"  extracted {len(tools)} tools from {CLIENT.name}")
    validate(tools)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    s = T.styles()

    books = [
        ("1 - Genius Guide - Overview.pdf", "BOOK 1 — OVERVIEW", book1),
        ("2 - Genius Guide - Creative Playbook.pdf", "BOOK 2 — CREATIVE PLAYBOOK", book2),
        ("3 - Genius Guide - Prompt Library.pdf", "BOOK 3 — PROMPT LIBRARY", book3),
        ("4 - Genius Guide - Limits.pdf", "BOOK 4 — LIMITS", book4),
        ("5 - Genius Guide - Action Reference.pdf", "BOOK 5 — ACTION REFERENCE", book5),
    ]
    for fname, running, fn in books:
        build(OUT_DIR / fname, running, FOOTER, fn(s, tools))

    print(f"\nDone -- {len(books)} PDFs in {OUT_DIR}")


if __name__ == "__main__":
    main()
