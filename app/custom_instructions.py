"""Genius custom instructions — user-authored, always injected, per Live Set.

Distinct from `live_context` in genius_client.py, which is memory Genius writes
about the user's production habits. These are instructions the *user* writes
about how Genius should answer (length, tone, what to assume, house rules), and
they persist until the user removes them.

Shape, per the design agreed for this feature:

- Presets are a **global library** (`settings["custom_instructions"]`), so one
  set of house rules can be reused across every project.
- Which preset is **active is bound per Live Set** (`settings["ci_bindings"]`,
  keyed by a slug of the Set name). Opening a Set restores the preset that Set
  was last using; a Set that has never been bound uses no preset.
- Genius may **add** an instruction when the user explicitly asks it to
  remember something, and may remove a prior line **only** when the new one
  directly conflicts with it. There is deliberately no general delete: see
  `add_instruction`.

Pure functions over a settings dict — no UI, no I/O. Persistence is the
caller's job (settings_store.save_settings), which keeps this testable and
keeps the single source of truth for settings in one place.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

MAX_PRESETS = 50
MAX_BODY_CHARS = 8_000
MAX_NAME_CHARS = 60

PRESETS_KEY = "custom_instructions"
BINDINGS_KEY = "ci_bindings"


# ── keys and slugs ─────────────────────────────────────────────────────────

def set_key(set_name: str | None) -> str:
    """Stable key for a Live Set name.

    Case- and punctuation-insensitive so "Neon Nights 128.als" and
    "neon nights 128" bind to the same preset — Live reports the name with and
    without the extension depending on whether the Set has been saved.
    """
    raw = str(set_name or "").strip()
    raw = re.sub(r"\.als$", "", raw, flags=re.IGNORECASE)
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug or "untitled"


def _presets(settings: dict[str, Any]) -> list[dict[str, Any]]:
    value = settings.get(PRESETS_KEY)
    return [p for p in value if isinstance(p, dict)] if isinstance(value, list) else []


def _bindings(settings: dict[str, Any]) -> dict[str, str]:
    value = settings.get(BINDINGS_KEY)
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items()}


# ── reads ──────────────────────────────────────────────────────────────────

def list_presets(settings: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(p.get("id") or ""),
            "name": str(p.get("name") or "Untitled"),
            "body": str(p.get("body") or ""),
            "updated": p.get("updated"),
        }
        for p in _presets(settings)
        if p.get("id")
    ]


def get_preset(settings: dict[str, Any], preset_id: str) -> dict[str, Any] | None:
    for p in _presets(settings):
        if str(p.get("id")) == str(preset_id):
            return p
    return None


def active_preset_id(settings: dict[str, Any], set_name: str | None) -> str:
    """Which preset this Set is bound to, or "" for none.

    A binding pointing at a deleted preset resolves to "" rather than dangling,
    so removing a preset can never leave a Set silently instruction-less-but-
    claiming-otherwise in the UI.
    """
    bound = _bindings(settings).get(set_key(set_name), "")
    return bound if bound and get_preset(settings, bound) else ""


def active_preset(settings: dict[str, Any], set_name: str | None) -> dict[str, Any] | None:
    pid = active_preset_id(settings, set_name)
    return get_preset(settings, pid) if pid else None


def instruction_lines(body: str) -> list[str]:
    return [ln.strip() for ln in str(body or "").splitlines() if ln.strip()]


def prompt_block(settings: dict[str, Any], set_name: str | None) -> str:
    """The text appended to Genius's system prompt, or "" when nothing is bound.

    Fenced and explicitly labelled as the user's own standing instructions so
    the model treats them as directives rather than as conversational content,
    and so they are visibly separable from the rest of the prompt.
    """
    preset = active_preset(settings, set_name)
    if not preset:
        return ""
    lines = instruction_lines(preset.get("body", ""))
    if not lines:
        return ""
    body = "\n".join("- " + ln.lstrip("- ").strip() for ln in lines)
    return (
        "\n\n## User's custom instructions"
        f" (preset \"{preset.get('name')}\", active for this Live Set)\n"
        "These are standing instructions from the user about how to answer. They outrank "
        "your default style guidance. Follow them for every reply in this conversation "
        "unless the user overrides one in the moment.\n"
        f"{body}\n"
    )


# ── writes (caller persists) ───────────────────────────────────────────────

def _now() -> float:
    return time.time()


def create_preset(settings: dict[str, Any], name: str, body: str = "") -> dict[str, Any]:
    presets = _presets(settings)
    if len(presets) >= MAX_PRESETS:
        raise ValueError(f"preset limit reached ({MAX_PRESETS})")
    preset = {
        "id": "ci-" + uuid.uuid4().hex[:8],
        "name": (str(name).strip() or "Untitled")[:MAX_NAME_CHARS],
        "body": str(body or "")[:MAX_BODY_CHARS],
        "created": _now(),
        "updated": _now(),
    }
    settings[PRESETS_KEY] = presets + [preset]
    return preset


def update_preset(
    settings: dict[str, Any],
    preset_id: str,
    name: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    preset = get_preset(settings, preset_id)
    if preset is None:
        raise ValueError(f"no custom-instruction preset '{preset_id}'")
    if name is not None:
        preset["name"] = (str(name).strip() or "Untitled")[:MAX_NAME_CHARS]
    if body is not None:
        preset["body"] = str(body)[:MAX_BODY_CHARS]
    preset["updated"] = _now()
    settings[PRESETS_KEY] = _presets(settings)
    return preset


def delete_preset(settings: dict[str, Any], preset_id: str) -> bool:
    """Remove a preset and any bindings that pointed at it.

    Only ever reached from the Preferences UI — Genius has no route here, by
    design. Bindings are cleaned up so no Live Set is left pointing at a
    preset that no longer exists.
    """
    remaining = [p for p in _presets(settings) if str(p.get("id")) != str(preset_id)]
    removed = len(remaining) != len(_presets(settings))
    settings[PRESETS_KEY] = remaining
    settings[BINDINGS_KEY] = {
        k: v for k, v in _bindings(settings).items() if v != str(preset_id)
    }
    return removed


def bind(settings: dict[str, Any], set_name: str | None, preset_id: str) -> str:
    """Point this Live Set at a preset. Empty preset_id unbinds it."""
    bindings = _bindings(settings)
    key = set_key(set_name)
    if not preset_id:
        bindings.pop(key, None)
    else:
        if get_preset(settings, preset_id) is None:
            raise ValueError(f"no custom-instruction preset '{preset_id}'")
        bindings[key] = str(preset_id)
    settings[BINDINGS_KEY] = bindings
    return bindings.get(key, "")


def add_instruction(
    settings: dict[str, Any],
    set_name: str | None,
    text: str,
    replaces: str | None = None,
) -> dict[str, Any]:
    """Append one instruction to the Set's active preset.

    This is the only write Genius can perform, and it is additive by
    construction. `replaces` is the single, narrow exception the user asked
    for: when the new instruction *directly contradicts* an existing line, that
    one line may be dropped. It is matched against existing lines rather than
    accepted as free text, so the model cannot use it to delete something
    unrelated, and the result reports exactly what changed for the reply to
    quote back.

    There is deliberately no delete operation. A capability the model cannot
    express is more reliable than one it is merely instructed not to use.
    """
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("instruction text is empty")

    preset = active_preset(settings, set_name)
    if preset is None:
        # Nothing bound yet: create a preset for this Set rather than failing,
        # so "remember that..." works on a fresh project without ceremony.
        preset = create_preset(settings, f"{str(set_name or 'Untitled').strip()} instructions")
        bind(settings, set_name, str(preset["id"]))
        created = True
    else:
        created = False

    lines = instruction_lines(preset.get("body", ""))
    removed: str | None = None

    if replaces:
        wanted = " ".join(str(replaces).split()).lower().lstrip("- ")
        for existing in lines:
            if existing.lower().lstrip("- ") == wanted:
                removed = existing
                break
        if removed is None:
            # Fall back to a containment match so a near-quote still resolves,
            # but never invent a target: if nothing matches, the add still
            # happens and the caller is told the removal did not.
            for existing in lines:
                if wanted and wanted in existing.lower():
                    removed = existing
                    break
        if removed is not None:
            lines = [ln for ln in lines if ln != removed]

    if any(ln.lower().lstrip("- ") == text.lower().lstrip("- ") for ln in lines):
        return {
            "added": False,
            "duplicate": True,
            "text": text,
            "removed": removed,
            "preset_id": preset["id"],
            "preset_name": preset["name"],
            "created_preset": created,
            "total": len(lines),
        }

    lines.append(text)
    update_preset(settings, str(preset["id"]), body="\n".join(lines))
    return {
        "added": True,
        "duplicate": False,
        "text": text,
        "removed": removed,
        "replaces_requested": replaces or None,
        "preset_id": preset["id"],
        "preset_name": preset["name"],
        "created_preset": created,
        "total": len(lines),
    }
