"""Windows loopback audio capture via ffmpeg DirectShow for Live Actions / Live Actions Genius.

Captures real-time audio output from Ableton Live via a virtual loopback audio
device (Voicemeeter, Virtual Audio Cable, Stereo Mix, etc.).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

LOOPBACK_NAME_HINTS = (
    "voicemeeter",
    "virtual",
    "loopback",
    "stereo mix",
    "cable",
    "moises",
    "blackhole",
)

INSTALL_HINT = (
    "No loopback audio device found. To let Genius capture & analyze Live's output in real time:\n"
    "  1. Ensure a virtual audio device (such as Voicemeeter VAIO or VB-Cable) is enabled in Windows Sound settings.\n"
    "  2. In Ableton Live (Preferences -> Audio), set Audio Output to your virtual device (or Multi-Output/Voicemeeter).\n"
    "  3. Retry."
)


class LoopbackNotFound(RuntimeError):
    """Raised when no loopback audio capture device can be located."""


def ensure_ffmpeg(ffmpeg_path: str = "ffmpeg") -> str:
    """Validate ffmpeg path or locate it on system PATH."""
    ff = shutil.which(ffmpeg_path)
    if not ff:
        raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg or configure ffmpeg_path in settings.")
    return ff


def list_dshow_audio_devices(ffmpeg_path: str = "ffmpeg") -> list[str]:
    """Return a list of DirectShow audio input device names on Windows."""
    ff = ensure_ffmpeg(ffmpeg_path)
    proc = subprocess.run(
        [ff, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        capture_output=True,
        text=True,
        timeout=15,
        encoding="utf-8",
        errors="replace",
    )

    devices: list[str] = []
    # ffmpeg dshow lists devices with lines like:
    # [dshow @ ...] "Device Name" (audio)
    for line in proc.stderr.splitlines():
        line = line.strip()
        if "(audio)" in line:
            m = re.search(r'"([^"]+)"\s+\(audio\)', line)
            if m:
                devices.append(m.group(1))
    return devices


def find_loopback_device(preferred: Optional[str] = None, ffmpeg_path: str = "ffmpeg") -> str:
    """Find a loopback or virtual audio capture device name."""
    devices = list_dshow_audio_devices(ffmpeg_path=ffmpeg_path)
    if not devices:
        raise LoopbackNotFound("No audio input devices found via DirectShow.\n" + INSTALL_HINT)

    if preferred:
        pref_low = preferred.lower()
        for d in devices:
            if pref_low in d.lower():
                return d

    for hint in LOOPBACK_NAME_HINTS:
        for d in devices:
            if hint in d.lower():
                return d

    # If no obvious loopback keyword matches, return first available device or raise
    raise LoopbackNotFound(
        f"Found audio devices: {devices}, but none matched loopback hints ({LOOPBACK_NAME_HINTS}).\n" + INSTALL_HINT
    )


def record_audio(
    seconds: float = 4.0,
    out_path: Optional[str] = None,
    device_name: Optional[str] = None,
    samples_dir: Optional[str] = None,
    ffmpeg_path: str = "ffmpeg",
) -> str:
    """Capture real-time audio output via DirectShow loopback to a WAV file."""
    ff = ensure_ffmpeg(ffmpeg_path)
    dev = device_name or find_loopback_device(ffmpeg_path=ffmpeg_path)

    if not out_path:
        base_dir = Path(samples_dir) / "Live Actions Recordings" if samples_dir else Path.home() / "Documents" / "Live Actions Recordings"
        base_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = str(base_dir / f"rec_{ts}.wav")
    else:
        out_path = os.path.expanduser(out_path)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ff,
        "-y",
        "-f",
        "dshow",
        "-i",
        f"audio={dev}",
        "-t",
        str(max(0.5, float(seconds))),
        "-ar",
        "48000",
        "-ac",
        "2",
        out_path,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=int(seconds) + 15, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg recording failed (exit code {proc.returncode}): {proc.stderr}")

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError(f"Recorded output file {out_path} is missing or empty.")

    return out_path
