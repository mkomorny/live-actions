"""Wrap Live Actions Bridge.maxpat in a real Max for Live audio-effect .amxd (ampf)."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAXPAT = HERE / "Live Actions Bridge.maxpat"
AMXD = HERE / "Live Actions Bridge.amxd"
AUDIO_EFFECT = 1633771873  # Max for Live audio effect, same as JSON Weather


def pack(src: Path = MAXPAT, dest: Path = AMXD) -> Path:
    data = json.loads(src.read_text(encoding="utf-8"))
    patcher = data.setdefault("patcher", {})
    patcher["devicewidth"] = float(patcher.get("devicewidth") or 420.0)
    project = patcher.setdefault("project", {})
    project.setdefault("version", 1)
    project["amxdtype"] = AUDIO_EFFECT
    project.setdefault("devpath", ".")
    project.setdefault("devpathtype", 0)
    payload = json.dumps(data, indent=2).encode("utf-8")
    # aaaa = Max Audio Effect (track device). natt is a MIDI container
    # and is why Live used to refuse the single device as a MIDI Tool.
    header = (
        b"ampf"
        + struct.pack("<I", 4)
        + b"aaaa"
        + b"meta"
        + struct.pack("<I", 4)
        + struct.pack("<I", 0)
        + b"ptch"
        + struct.pack("<I", len(payload))
    )
    dest.write_bytes(header + payload)
    return dest


if __name__ == "__main__":
    out = pack()
    print("Wrote", out, "(%d bytes)" % out.stat().st_size)
    sys.exit(0)
