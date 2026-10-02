#!/usr/bin/env python3
"""Build the Genius knowledge database from plain Markdown.

Every folder next to this file that has a `markdown/` subfolder is one dataset
("topic"). This script turns each one into a small SQLite full-text database
and drops a `search.py` beside it -- which is all the app needs:

    database/
      my_notes/
        markdown/**/*.md      <- you write these
        my_notes.db           <- built here
        search.py             <- copied here

Run it again whenever you add or change Markdown:

    python database/build_database.py            # every dataset
    python database/build_database.py my_notes   # just one

Standard library only. Genius then reaches the dataset as
`library_db_search(topic="my_notes", query="...")`.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEARCH_TEMPLATE = ROOT / "search.py"
CHUNK_CHARS = 1800           # soft size of one searchable chunk
HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)


def read_doc(path: Path) -> tuple[dict[str, str], str]:
    """(front-matter fields, body). Front matter is the optional leading --- block of `key: value` lines."""
    text = path.read_text(encoding="utf-8", errors="replace")
    meta: dict[str, str] = {}
    match = FRONT_MATTER.match(text)
    if match:
        for line in match.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip().lower()] = value.strip()
        text = text[match.end():]
    return meta, text


def sections(body: str) -> list[tuple[str, str]]:
    """Split a document on its headings -> [(section title, text)], then keep each piece near CHUNK_CHARS."""
    out: list[tuple[str, str]] = []
    title, buf = "", []

    def flush() -> None:
        text = "\n".join(buf).strip()
        if not text:
            return
        while len(text) > CHUNK_CHARS * 1.5:
            cut = text.rfind("\n", 0, CHUNK_CHARS)
            if cut < CHUNK_CHARS // 2:
                cut = CHUNK_CHARS
            out.append((title, text[:cut].strip()))
            text = text[cut:].strip()
        out.append((title, text))

    for line in body.splitlines():
        found = HEADING.match(line)
        if found:
            flush()
            title, buf = found.group(2), [line]
        else:
            buf.append(line)
    flush()
    return out


def build(folder: Path) -> tuple[int, int]:
    source = folder / "markdown"
    db_path = folder / (folder.name + ".db")
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(str(db_path))
    con.executescript(
        """
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY, doc_uid TEXT UNIQUE, title TEXT NOT NULL,
            category TEXT NOT NULL, subcategory TEXT, source_file TEXT, word_count INTEGER
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY, chunk_uid TEXT UNIQUE, doc_id INTEGER REFERENCES documents(id),
            doc_title TEXT, category TEXT, subcategory TEXT, section_title TEXT,
            chunk_index INTEGER, content TEXT
        );
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            chunk_uid UNINDEXED, doc_title, category, subcategory, section_title, content,
            tokenize = 'porter unicode61'
        );
        """
    )
    docs = chunks = 0
    for path in sorted(source.rglob("*.md")):
        rel = path.relative_to(source)
        parts = rel.parts[:-1]
        meta, body = read_doc(path)
        first_heading = next((HEADING.match(l).group(2) for l in body.splitlines() if HEADING.match(l)), "")
        title = meta.get("title") or first_heading or path.stem.replace("_", " ")
        category = meta.get("category") or (parts[0] if parts else "general")
        subcategory = meta.get("subcategory") or (parts[1] if len(parts) > 1 else "")
        uid = "/".join(rel.with_suffix("").parts)
        cur = con.execute(
            "INSERT INTO documents (doc_uid, title, category, subcategory, source_file, word_count) VALUES (?,?,?,?,?,?)",
            (uid, title, category, subcategory, rel.as_posix(), len(body.split())),
        )
        docs += 1
        for index, (section, text) in enumerate(sections(body)):
            chunk_uid = "%s#%d" % (uid, index)
            con.execute(
                "INSERT INTO chunks (chunk_uid, doc_id, doc_title, category, subcategory, section_title, chunk_index, content)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (chunk_uid, cur.lastrowid, title, category, subcategory, section, index, text),
            )
            con.execute(
                "INSERT INTO chunks_fts (chunk_uid, doc_title, category, subcategory, section_title, content)"
                " VALUES (?,?,?,?,?,?)",
                (chunk_uid, title, category, subcategory, section, text),
            )
            chunks += 1
    con.commit()
    con.execute("VACUUM")
    con.close()
    if SEARCH_TEMPLATE.is_file():
        shutil.copyfile(SEARCH_TEMPLATE, folder / "search.py")
    return docs, chunks


def main(argv: list[str]) -> int:
    wanted = set(argv)
    folders = [p for p in sorted(ROOT.iterdir()) if (p / "markdown").is_dir() and (not wanted or p.name in wanted)]
    if not folders:
        print("No dataset folders with a markdown/ subfolder found under %s" % ROOT)
        return 1
    for folder in folders:
        docs, chunks = build(folder)
        print("%-32s %4d documents  %5d chunks" % (folder.name, docs, chunks))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
