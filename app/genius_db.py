"""Structured-database search for Genius: the bundled `database/` folder.

Each dataset folder under the DB root holds a SQLite FTS5 database plus a
`search.py` CLI (see database/build_database.py, which builds both from plain
Markdown). We shell out to that CLI with --json rather than re-implementing the
query here, so a dataset built by other tooling works too, as long as its
search.py accepts `<query> --limit N --json` and prints a JSON list.

A dataset does not have to be listed in TOPICS: any folder directly under the
DB root that has its own search.py is picked up by name, so users can add
their own without touching this file.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB_ROOT = Path(__file__).resolve().parent.parent / "database"

# key -> (folder under the DB root, one-line description shown to the model)
TOPICS: dict[str, tuple[str, str]] = {
    "ableton_god_producer": ("ableton_god_producer", "Beat-making recipes by genre: drum programming, bass sound design, mixing/mastering chains, with ready-to-call live_* action blueprints"),
    "ableton_racks_labeled": ("ableton_racks_labeled", "134 labeled Ableton Live preset racks: signal chain, devices, settings and macro mappings for each"),
    "mixology_db": ("mixology_db", "Mix engineering reference: gain/pan ratios by genre, EQ Eight carving curves per instrument, mix-critique rules"),
    "vital_synth_lab": ("vital_synth_lab", "Vital synth: preset JSON format, headless rendering, wavetable extraction, translation to Live's Drift/Wavetable"),
    "music_theory_basics": ("music_theory_basics", "Beginner music theory course with keyboard practice: notes, intervals, scales, chords, keys, rhythm"),
    "ableton_mcp_extended": ("ableton_mcp_extended", "Notes on jpoindexter/ableton-mcp: Remote Script commands, MIDI capture, locators, drum pad control"),
    "ableton_live_mcp_bschoepke": ("ableton_live_mcp_bschoepke", "Notes on bschoepke/ableton-live-mcp: Live's sound-similarity database, clip automation curves, Session-to-Arrangement"),
    "abletonosc": ("abletonosc", "Notes on ideoforms/AbletonOSC: OSC Remote Script addresses, session dump, bulk track queries"),
}

# Not real topics -- other names people (and older prompts) use for a topic key.
TOPIC_ALIASES = {
    "ableton_live_helper": "ableton_god_producer",
    "music_theory": "music_theory_basics",
    "sound_design": "vital_synth_lab",
    "mixing": "mixology_db",
}


def db_root(settings: dict[str, Any] | None = None) -> Path:
    settings = settings or {}
    return Path(str(settings.get("music_db_dir") or DEFAULT_DB_ROOT))


def _normalize(key: str) -> str:
    return (key or "").strip().lower().replace(" ", "_").replace("-", "_")


def discovered_topics(root: Path) -> dict[str, tuple[str, str]]:
    """Dataset folders under `root` that are not in TOPICS: any direct subfolder with its own search.py."""
    known = {folder for folder, _desc in TOPICS.values()}
    found: dict[str, tuple[str, str]] = {}
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError:
        return found
    for child in children:
        if child.name not in known and (child / "search.py").is_file():
            found[_normalize(child.name)] = (child.name, "your own dataset")
    return found


def resolve_topic(key: str, root: Path | None = None) -> tuple[str, str] | None:
    key = _normalize(key)
    key = TOPIC_ALIASES.get(key, key)
    if key in TOPICS:
        return TOPICS[key]
    return discovered_topics(root).get(key) if root is not None else None


def list_topics(root: Path | None = None) -> str:
    lines = ["Available library_db_search topics:"]
    topics = dict(TOPICS)
    if root is not None:
        topics.update(discovered_topics(root))
    for key, (_folder, desc) in topics.items():
        lines.append(f"  - {key}: {desc}")
    return "\n".join(lines)


def db_search(settings: dict[str, Any], topic: str, query: str, limit: int = 5) -> str:
    root = db_root(settings)
    resolved = resolve_topic(topic, root)
    if not resolved:
        return "Unknown topic %r.\n\n%s" % (topic, list_topics(root))
    folder_name, _desc = resolved

    script = root / folder_name / "search.py"
    if not script.is_file():
        return (
            "Database search script not found: %s (check the Music / audio database folder in Preferences, "
            "or run database/build_database.py)" % script
        )

    try:
        proc = subprocess.run(
            [sys.executable, str(script), query, "--limit", str(max(1, min(limit, 10))), "--json"],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception as exc:
        return "ERROR running %s: %s" % (script, exc)

    if proc.returncode != 0:
        return "ERROR from %s (exit %d): %s" % (script.name, proc.returncode, (proc.stderr or "").strip()[:2000])

    try:
        results = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return (proc.stdout or "").strip()[:4000] or "No output from %s." % script.name

    if not results:
        return "No matches for %r in %s." % (query, folder_name)

    lines = ["%d match(es) in %s for %r:" % (len(results), folder_name, query)]
    for r in results:
        if not isinstance(r, dict):
            # Some search.py builds emit a bare string (or other non-object row)
            # instead of the usual {doc_title, ...} shape -- surface it rather
            # than crashing the whole response.
            lines.append("\n%s" % str(r)[:1200])
            continue
        title = r.get("doc_title") or r.get("title") or "?"
        section = r.get("section_title") or r.get("subcategory") or r.get("category") or ""
        page = r.get("page_number")
        cite = title + (f" — {section}" if section else "") + (f" (p.{page})" if page else "")
        # The field name differs by dataset build: some use "content", others
        # "snippet" with >>> highlighted <<< match markers. Accept either.
        content = str(r.get("content") or r.get("text") or r.get("snippet") or "").strip()
        if len(content) > 1200:
            content = content[:1200] + "…"
        lines.append("\n[%s]\n%s" % (cite, content))
    return "\n".join(lines)
