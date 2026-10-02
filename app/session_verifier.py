"""Session verification and diffing module for Live Actions Helper / Live Actions Genius.

Ported from Pantani/ableton-mind (Phase 5 verify loop).
Computes deep hierarchical diffs between before/after Live Set snapshots
so agents and users can verify the exact mutations made to the session.
"""

from __future__ import annotations

import time
from typing import Any


def diff_dicts(prev: Any, curr: Any, path: str = "") -> list[dict[str, Any]]:
    """Recursively diff two dictionaries, lists, or primitives.
    
    Returns a list of dicts:
        { "path": str, "before": Any, "after": Any, "kind": "added" | "removed" | "changed" }
    """
    changes: list[dict[str, Any]] = []

    if not isinstance(prev, dict) or not isinstance(curr, dict):
        if prev != curr:
            changes.append({
                "path": path,
                "before": prev,
                "after": curr,
                "kind": "changed"
            })
        return changes

    all_keys = set(prev.keys()) | set(curr.keys())
    for k in sorted(list(all_keys)):
        p = f"{path}.{k}" if path else str(k)
        if k not in prev:
            changes.append({
                "path": p,
                "before": None,
                "after": curr[k],
                "kind": "added"
            })
        elif k not in curr:
            changes.append({
                "path": p,
                "before": prev[k],
                "after": None,
                "kind": "removed"
            })
        else:
            v_prev = prev[k]
            v_curr = curr[k]
            if isinstance(v_prev, dict) and isinstance(v_curr, dict):
                changes.extend(diff_dicts(v_prev, v_curr, p))
            elif isinstance(v_prev, list) and isinstance(v_curr, list):
                # Diff list elements by index
                max_len = max(len(v_prev), len(v_curr))
                for i in range(max_len):
                    idx_path = f"{p}[{i}]"
                    if i >= len(v_prev):
                        changes.append({
                            "path": idx_path,
                            "before": None,
                            "after": v_curr[i],
                            "kind": "added"
                        })
                    elif i >= len(v_curr):
                        changes.append({
                            "path": idx_path,
                            "before": v_prev[i],
                            "after": None,
                            "kind": "removed"
                        })
                    else:
                        changes.extend(diff_dicts(v_prev[i], v_curr[i], idx_path))
            elif v_prev != v_curr:
                changes.append({
                    "path": p,
                    "before": v_prev,
                    "after": v_curr,
                    "kind": "changed"
                })

    return changes


def compute_session_diff(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare a previous session snapshot with a current snapshot."""
    # Exclude volatile timestamp from triggering false diffs
    prev_clean = {k: v for k, v in previous.items() if k != "ts"}
    curr_clean = {k: v for k, v in current.items() if k != "ts"}

    changes = diff_dicts(prev_clean, curr_clean)

    return {
        "ok": True,
        "from_ts": previous.get("ts"),
        "to_ts": current.get("ts") or int(time.time() * 1000),
        "count": len(changes),
        "changes": changes,
        "summary": f"{len(changes)} change(s) detected across Set" if changes else "No structural changes detected."
    }
