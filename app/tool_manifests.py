"""Tool manifest loader -- pure logic, no UI.

Lifted verbatim out of helper.py (slice 1 of the WebView2 redesign) so the Tk
app and the new shell read tool.json files through one implementation. Do not
add a UI dependency here (no tkinter, no pywebview).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tools(folder: Path) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    if not folder.is_dir():
        return tools
    for manifest in sorted(folder.glob("*/tool.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not data.get("id"):
            continue
        data["_path"] = str(manifest.parent)
        tools.append(data)
    return tools
