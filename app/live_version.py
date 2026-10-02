"""Live Actions -- the running Ableton Live version, as a fact instead of a guess.

Two feeds record it (genius_client.py after a `live_connect` reply; remote_script_client.py's
probe(), which already runs on a timer) so the version is usually known before a Genius turn
even starts. Everything else reads it through here rather than asserting a fixed requirement,
so a version-gated tool description can state what actually holds for THIS running Live instead
of the model recalling (or the user having to state) a build number.

`at_least()` returns None, never False, when the version has not been read yet -- a gate that
defaults an unknown to "too old" is refuse-by-default with extra steps, which is the exact
failure this module exists to remove: the model should try the tool and report what actually
happened, not decline on a guess.
"""

from __future__ import annotations

import re
from typing import Any

_VERSION_RE = re.compile(r"^\s*(?:live\s+)?(\d+)(?:\.(\d+))?(?:\.(\d+))?", re.IGNORECASE)

_raw = ""
_major = 0
_minor = 0
_patch = 0
_known = False


def record(raw: str) -> None:
    """Record a version string reported by Live ("12.5.15.1b", "Live 12.4.14", "12").

    An unparseable value is ignored rather than clobbering a previously known good reading --
    a bad parse should never make an already-known version look unknown again.
    """
    global _raw, _major, _minor, _patch, _known
    text = str(raw or "").strip()
    if not text:
        return
    m = _VERSION_RE.match(text)
    if not m:
        return
    _raw = text
    _major = int(m.group(1))
    _minor = int(m.group(2)) if m.group(2) else 0
    _patch = int(m.group(3)) if m.group(3) else 0
    _known = True


def current() -> dict[str, Any]:
    return {
        "raw": _raw,
        "major": _major if _known else None,
        "minor": _minor if _known else None,
        "patch": _patch if _known else None,
        "known": _known,
    }


def at_least(major: int, minor: int) -> bool | None:
    """True/False against the known version, or None when it hasn't been read yet.

    None must never be treated as False by a caller -- it means "try it and report what
    actually happened", not "assume too old and refuse"."""
    if not _known:
        return None
    if _major != major:
        return _major > major
    return _minor >= minor


def describe() -> str:
    if not _known:
        return "not read yet"
    return f"Ableton Live {_major}.{_minor}.{_patch}"


def reset() -> None:
    """Back to unknown. Used by tests; also safe to call on a fresh connect."""
    global _raw, _major, _minor, _patch, _known
    _raw, _major, _minor, _patch, _known = "", 0, 0, 0, False
