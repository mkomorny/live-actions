#!/usr/bin/env python3
"""Full-text search over the one .db file that sits next to this script.

    python search.py "sidechain compression" --limit 5
    python search.py "sidechain compression" --json

`build_database.py` copies this file into every dataset folder. The app runs it
with --json and reads the list it prints. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent


def find_db() -> Path | None:
    preferred = HERE / (HERE.name + ".db")
    if preferred.is_file():
        return preferred
    found = sorted(HERE.glob("*.db"))
    return found[0] if found else None


def fts_query(text: str) -> str:
    """Quote each word so dots, hyphens and slashes in a question can never be read as FTS5 syntax."""
    words = re.findall(r"[A-Za-z0-9_\u0080-￿]+", text)
    return " ".join('"%s"' % w for w in words) if words else '""'


def search(query: str, limit: int = 5, category: str | None = None) -> list[dict]:
    db = find_db()
    if db is None:
        raise FileNotFoundError("No .db file next to %s -- run build_database.py first." % Path(__file__).name)
    con = sqlite3.connect("file:%s?mode=ro" % db.as_posix(), uri=True)
    where, params = "chunks_fts MATCH ?", [fts_query(query)]
    if category:
        where += " AND category = ?"
        params.append(category)
    params.append(max(1, min(int(limit), 50)))
    rows = con.execute(
        "SELECT chunk_uid, doc_title, category, section_title,"
        " snippet(chunks_fts, 5, '>>> ', ' <<<', '...', 60), bm25(chunks_fts)"
        " FROM chunks_fts WHERE " + where + " ORDER BY bm25(chunks_fts) LIMIT ?",
        params,
    ).fetchall()
    con.close()
    return [
        {"chunk_uid": r[0], "doc_title": r[1], "category": r[2], "section_title": r[3], "snippet": r[4], "rank": r[5]}
        for r in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search this dataset.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        results = search(args.query, args.limit, args.category)
    except Exception as exc:
        print("Search error: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    print("%d result(s) for %r\n" % (len(results), args.query))
    for r in results:
        print("* [%s] %s -- %s" % (r["category"], r["doc_title"], r["section_title"]))
        print("  %s\n" % r["snippet"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
