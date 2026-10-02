"""Live Actions — Offline Ableton Live (.als) Project Tools.

Inspects, parses, diffs, extracts MIDI, and lints saved Ableton Live .als projects
offline without needing Ableton Live to be open or running.
"""

from __future__ import annotations

import gzip
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

_TRACK_KIND = {
    "MidiTrack": "midi",
    "AudioTrack": "audio",
    "ReturnTrack": "return",
    "GroupTrack": "group",
    "MasterTrack": "master",
    "MainTrack": "master",
}

_RACK_TAGS = {
    "AudioEffectGroupDevice",
    "InstrumentGroupDevice",
    "MidiEffectGroupDevice",
    "DrumGroupDevice",
}

_PLUGIN_TAGS = {"PluginDevice", "AuPluginDevice", "Vst3PluginDevice", "VstPluginDevice"}


# ── XML Helper Utilities ──────────────────────────────────────────────────────

def _val(elem: ET.Element | None, default: Any = None) -> str | None:
    if elem is None:
        return default
    return elem.get("Value", default)


def _fnum(elem: ET.Element | None, default: float | None = None) -> float | None:
    v = _val(elem)
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def _inum(elem: ET.Element | None, default: int | None = None) -> int | None:
    v = _val(elem)
    if v is None:
        return default
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return default


def _flag(elem: ET.Element | None, default: bool = False) -> bool:
    v = _val(elem)
    if v is None:
        return default
    return str(v).lower() in ("true", "1")


def _afloat(elem: ET.Element | None, attr: str, default: float = 0.0) -> float:
    if elem is None:
        return default
    v = elem.get(attr)
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def _aint(elem: ET.Element | None, attr: str, default: int | None = None) -> int | None:
    if elem is None:
        return default
    v = elem.get(attr)
    if v is None:
        return default
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return default


def load_als_xml(path: str | Path) -> tuple[ET.Element | None, str | None]:
    """Read and decompress an .als file into an XML ElementTree root."""
    p = Path(path)
    if not p.is_file():
        return None, f"File not found: {p}"

    try:
        with gzip.open(p, "rb") as gz:
            content = gz.read()
        return ET.fromstring(content), None
    except gzip.BadGzipFile:
        # Try uncompressed fallback
        try:
            tree = ET.parse(p)
            return tree.getroot(), None
        except Exception as e:
            return None, f"Failed to parse XML from {p.name}: {e}"
    except Exception as e:
        return None, f"Error reading {p.name}: {e}"


# ── Internal Extractors ───────────────────────────────────────────────────────

def _extract_clip_notes(clip_elem: ET.Element) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    # Shape 1: KeyTrack grouping
    for kt in clip_elem.iter("KeyTrack"):
        pitch = _inum(kt.find("MidiKey"))
        for ev in kt.iter():
            if ev.tag in ("MidiNoteEvent", "MidiNote"):
                p = pitch if pitch is not None else _aint(ev, "Pitch", 60)
                notes.append({
                    "pitch": int(p if p is not None else 60),
                    "start_time": round(_afloat(ev, "Time", 0.0), 4),
                    "duration": round(_afloat(ev, "Duration", 0.0), 4),
                    "velocity": int(_afloat(ev, "Velocity", 100.0)),
                    "mute": False,
                })

    # Shape 2: Flat MidiNoteEvent / MidiNote tags
    if not notes:
        for ev in clip_elem.iter():
            if ev.tag in ("MidiNoteEvent", "MidiNote"):
                p = _aint(ev, "Pitch")
                if p is not None:
                    notes.append({
                        "pitch": int(p),
                        "start_time": round(_afloat(ev, "Time", 0.0), 4),
                        "duration": round(_afloat(ev, "Duration", 0.0), 4),
                        "velocity": int(_afloat(ev, "Velocity", 100.0)),
                        "mute": False,
                    })

    notes.sort(key=lambda n: (n["start_time"], n["pitch"]))
    return notes


def _extract_clip(clip_elem: ET.Element, is_midi: bool) -> dict[str, Any]:
    start = _fnum(clip_elem.find("CurrentStart"), 0.0) or 0.0
    end = _fnum(clip_elem.find("CurrentEnd"), start) or start
    sample_path = None
    if not is_midi:
        ref = clip_elem.find(".//SampleRef/FileRef")
        if ref is not None:
            sample_path = _val(ref.find("Path")) or _val(ref.find("RelativePath")) or _val(ref.find("Name"))

    notes = _extract_clip_notes(clip_elem) if is_midi else []
    return {
        "name": _val(clip_elem.find("Name"), "") or "",
        "is_midi": is_midi,
        "start": start,
        "length": round(max(0.0, end - start), 4),
        "looping": _flag(clip_elem.find("Loop/LoopOn")),
        "sample_path": sample_path,
        "note_count": len(notes),
        "notes": notes,
    }


def _extract_track_clips(track_elem: ET.Element) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    stack = list(track_elem)
    while stack:
        e = stack.pop()
        if e.tag == "FreezeSequencer":
            continue
        if "MidiClip" in e.tag:
            clips.append(_extract_clip(e, True))
        elif "AudioClip" in e.tag:
            clips.append(_extract_clip(e, False))
        else:
            stack.extend(e)
    return clips


def _device_name(dev: ET.Element) -> str:
    name = _val(dev.find("UserName"))
    if not name and dev.tag in _PLUGIN_TAGS:
        desc = dev.find("PluginDesc")
        if desc is not None:
            name = _val(desc.find(".//PlugName")) or _val(desc.find(".//Name"))
    if not name:
        name = _val(dev.find("Name"))
    return name or dev.tag


def _extract_devices(track_elem: ET.Element) -> list[dict[str, Any]]:
    outer = track_elem.find("DeviceChain")
    if outer is None:
        return []
    inner = outer.find("DeviceChain")
    chain = inner.find("Devices") if inner is not None else None
    if chain is None:
        chain = outer.find("Devices")
    if chain is None:
        return []

    devices = []
    for dev in list(chain):
        devices.append({
            "name": _device_name(dev),
            "kind": dev.tag,
            "is_plugin": dev.tag in _PLUGIN_TAGS,
        })
        if dev.tag in _RACK_TAGS:
            for sub in dev.findall(".//Devices/*"):
                devices.append({
                    "name": _device_name(sub),
                    "kind": sub.tag,
                    "is_plugin": sub.tag in _PLUGIN_TAGS,
                    "in_rack": True,
                })
    return devices


def _extract_track(elem: ET.Element, index: int) -> dict[str, Any]:
    kind = _TRACK_KIND.get(elem.tag, "unknown")
    name = _val(elem.find(".//Name/EffectiveName")) or _val(elem.find(".//Name/UserName")) or f"Track {index}"
    clips = _extract_track_clips(elem) if kind in ("midi", "audio") else []
    mixer_speaker = elem.find("DeviceChain/Mixer/Speaker/Manual")
    color = elem.find("Color")

    return {
        "index": index,
        "kind": kind,
        "name": name,
        "muted": not _flag(mixer_speaker, True),
        "soloed": _flag(elem.find("DeviceChain/Mixer/SoloSink")),
        "color_index": _inum(color) if color is not None else _inum(elem.find("ColorIndex")),
        "volume": _fnum(elem.find("DeviceChain/Mixer/Volume/Manual")),
        "pan": _fnum(elem.find("DeviceChain/Mixer/Pan/Manual")),
        "devices": _extract_devices(elem),
        "clips": clips,
        "note_count": sum(c["note_count"] for c in clips),
    }


def parse_als_project(path: str | Path) -> tuple[dict[str, Any] | None, str | None]:
    """Parse complete .als file into a structured dictionary."""
    root, err = load_als_xml(path)
    if err or root is None:
        return None, err

    live_set = root.find("LiveSet")
    if live_set is None:
        live_set = root

    tempo = _fnum(live_set.find(".//Tempo/Manual"))
    if tempo is None:
        tempo = _fnum(live_set.find(".//MainTrack//Tempo/Manual"))
    if tempo is None:
        tempo = _fnum(live_set.find(".//MasterTrack//Tempo/Manual"), 120.0)

    tracks: list[dict[str, Any]] = []
    parent = next(live_set.iter("Tracks"), None)
    if parent is not None:
        for i, t in enumerate(list(parent)):
            if t.tag in _TRACK_KIND:
                tracks.append(_extract_track(t, i))

    master_elem = live_set.find("MainTrack")
    if master_elem is None:
        master_elem = live_set.find("MasterTrack")

    scenes = [_val(s.find("Name"), "") or "" for s in live_set.findall(".//Scenes/Scene")]
    locators = [
        {"time": _fnum(loc.find("Time")), "name": _val(loc.find("Name"), "") or ""}
        for loc in live_set.findall(".//Locators/Locators/Locator")
    ]

    scale_root = _inum(live_set.find(".//ScaleInformation/RootNote"))
    scale_name = _val(live_set.find(".//ScaleInformation/Scale"))

    return {
        "path": str(path),
        "creator": root.get("Creator", "Unknown"),
        "minor_version": root.get("MinorVersion", ""),
        "tempo": tempo,
        "time_signature": f"{_inum(live_set.find('.//TimeSignatureNumerator'), 4)}/{_inum(live_set.find('.//TimeSignatureDenominator'), 4)}",
        "scale": f"{scale_root} {scale_name}" if (scale_root is not None and scale_name) else None,
        "tracks": tracks,
        "master": _extract_track(master_elem, -1) if master_elem is not None else None,
        "scenes": scenes,
        "locators": locators,
    }, None


# ── Public API Tools ──────────────────────────────────────────────────────────

def als_summary(path: str) -> dict[str, Any]:
    """Summarize an Ableton Live set without opening Ableton."""
    data, err = parse_als_project(path)
    if err or not data:
        return {"ok": False, "error": err}

    midi_tracks = [t for t in data["tracks"] if t["kind"] == "midi"]
    audio_tracks = [t for t in data["tracks"] if t["kind"] == "audio"]
    return_tracks = [t for t in data["tracks"] if t["kind"] == "return"]
    total_clips = sum(len(t["clips"]) for t in data["tracks"])

    return {
        "ok": True,
        "file": Path(path).name,
        "creator": data["creator"],
        "tempo": data["tempo"],
        "time_signature": data["time_signature"],
        "scale": data["scale"] or "None",
        "track_counts": {
            "total": len(data["tracks"]),
            "midi": len(midi_tracks),
            "audio": len(audio_tracks),
            "return": len(return_tracks),
        },
        "clip_count": total_clips,
        "scene_count": len(data["scenes"]),
        "locator_count": len(data["locators"]),
        "tracks": [{"index": t["index"], "name": t["name"], "kind": t["kind"], "clips": len(t["clips"])} for t in data["tracks"]],
        "locators": data["locators"],
    }


def als_list_tracks(path: str) -> dict[str, Any]:
    """List detailed track and clip breakdown from an .als file."""
    data, err = parse_als_project(path)
    if err or not data:
        return {"ok": False, "error": err}

    result_tracks = []
    for t in data["tracks"]:
        result_tracks.append({
            "index": t["index"],
            "name": t["name"],
            "kind": t["kind"],
            "volume": t["volume"],
            "pan": t["pan"],
            "muted": t["muted"],
            "soloed": t["soloed"],
            "devices": [d["name"] for d in t["devices"]],
            "clips": [{"name": c["name"], "length": c["length"], "is_midi": c["is_midi"], "notes": c["note_count"]} for c in t["clips"]],
        })

    return {
        "ok": True,
        "file": Path(path).name,
        "tracks": result_tracks,
    }


def als_extract_midi(path: str, track_index: int, clip_index: int = 0) -> dict[str, Any]:
    """Extract MIDI notes from a saved .als clip without launching Live."""
    data, err = parse_als_project(path)
    if err or not data:
        return {"ok": False, "error": err}

    target_track = next((t for t in data["tracks"] if t["index"] == track_index), None)
    if not target_track:
        return {"ok": False, "error": f"Track index {track_index} not found in project."}

    midi_clips = [c for c in target_track["clips"] if c["is_midi"]]
    if not midi_clips:
        return {"ok": False, "error": f"Track '{target_track['name']}' has no MIDI clips."}

    if clip_index >= len(midi_clips):
        return {"ok": False, "error": f"Clip index {clip_index} out of range ({len(midi_clips)} MIDI clips on track)."}

    clip = midi_clips[clip_index]
    return {
        "ok": True,
        "file": Path(path).name,
        "track_name": target_track["name"],
        "clip_name": clip["name"],
        "length": clip["length"],
        "note_count": len(clip["notes"]),
        "notes": clip["notes"],
    }


def als_diff(path_a: str, path_b: str) -> dict[str, Any]:
    """Diff two saved .als files to identify structural and parameter changes."""
    data_a, err_a = parse_als_project(path_a)
    if err_a or not data_a:
        return {"ok": False, "error": f"Error in file A: {err_a}"}
    data_b, err_b = parse_als_project(path_b)
    if err_b or not data_b:
        return {"ok": False, "error": f"Error in file B: {err_b}"}

    diff: dict[str, Any] = {
        "tempo_changed": None,
        "tracks_added": [],
        "tracks_removed": [],
        "tracks_renamed": [],
        "clip_changes": [],
    }

    if data_a["tempo"] != data_b["tempo"]:
        diff["tempo_changed"] = {"before": data_a["tempo"], "after": data_b["tempo"]}

    names_a = {t["name"]: t for t in data_a["tracks"]}
    names_b = {t["name"]: t for t in data_b["tracks"]}

    for name in names_b:
        if name not in names_a:
            diff["tracks_added"].append(name)
    for name in names_a:
        if name not in names_b:
            diff["tracks_removed"].append(name)

    for i, ta in enumerate(data_a["tracks"]):
        if i < len(data_b["tracks"]):
            tb = data_b["tracks"][i]
            if ta["name"] != tb["name"] and ta["name"] not in diff["tracks_removed"] and tb["name"] not in diff["tracks_added"]:
                diff["tracks_renamed"].append({"from": ta["name"], "to": tb["name"]})

            len_a = len(ta["clips"])
            len_b = len(tb["clips"])
            if len_a != len_b:
                diff["clip_changes"].append({
                    "track": tb["name"],
                    "clips_before": len_a,
                    "clips_after": len_b,
                })

    return {
        "ok": True,
        "file_a": Path(path_a).name,
        "file_b": Path(path_b).name,
        "diff": diff,
    }


def als_find_unfinished(path: str) -> dict[str, Any]:
    """Lint an .als project for common unfinished work, omissions, and risks."""
    data, err = parse_als_project(path)
    if err or not data:
        return {"ok": False, "error": err}

    issues: list[str] = []
    warnings: list[str] = []

    # 1. Master limiter check
    master = data.get("master")
    has_limiter = False
    if master:
        for d in master.get("devices", []):
            dname = d["name"].lower()
            if "limiter" in dname or "maximizer" in dname or "glue" in dname:
                has_limiter = True
                break
        if not has_limiter:
            warnings.append("Master track does not have a Limiter or brickwall compressor loaded.")

        # Master fader check (0.85 = 0 dB)
        if master.get("volume") is not None and master["volume"] > 0.85:
            issues.append(f"Master fader set above 0 dB ({master['volume']:.3f} > 0.850). High risk of clipping.")

    # 2. Track checks
    for t in data["tracks"]:
        tname = t["name"].strip()
        # Default unnamed tracks
        if tname.lower() in ("1-audio", "2-midi", "3-audio", "4-midi", "audio", "midi"):
            warnings.append(f"Track {t['index']} is still using generic name '{tname}'.")

        # Empty active tracks
        if not t["clips"] and not t["muted"]:
            warnings.append(f"Track '{tname}' (index {t['index']}) is active but contains no clips.")

        # Soloed tracks
        if t["soloed"]:
            warnings.append(f"Track '{tname}' is left soloed.")

        # Fader clipping risk
        if t.get("volume") is not None and t["volume"] > 0.95:
            warnings.append(f"Track '{tname}' fader pushed high ({t['volume']:.3f} > 0.950).")

    # 3. Arrangement structure check
    if not data["locators"]:
        warnings.append("Project contains 0 arrangement locators (no labeled sections e.g. Intro, Verse, Chorus).")

    return {
        "ok": True,
        "file": Path(path).name,
        "critical_issues_count": len(issues),
        "warnings_count": len(warnings),
        "issues": issues,
        "warnings": warnings,
    }
