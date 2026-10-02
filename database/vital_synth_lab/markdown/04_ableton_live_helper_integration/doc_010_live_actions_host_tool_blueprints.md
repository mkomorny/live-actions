---
id: 04_ableton_live_helper_integration_doc_010_live_actions_host_tool_blueprints
title: Live Actions Host Tool Architecture & Implementation Blueprints
category: 04_ableton_live_helper_integration
pages: 1
words: 672
source: 04_ableton_live_helper_integration/doc_010_live_actions_host_tool_blueprints.md
---
# Live Actions Host Tool Architecture & Implementation Blueprints

## 1. Host Runtime Architecture in Live Actions Helper

In `Live Actions Helper` (`C:\Users\<you>\My Apps\Live Actions Helper`), tools fall into two runtime execution models:

1. **Bridge Runtime (`"runtime": "bridge"`)**:
   Runs inside Max for Live via OSC commands (`/live-actions/run`) to `live-actions-bridge.js`. Restricted strictly to the Live Object Model (LOM) within Ableton Live 12 Standard.
2. **Host Runtime (`"runtime": "host"`)**:
   Runs directly inside the desktop application's Python engine (`app/helper.py`). It is completely free from the Max sandbox, allowing it to perform file operations, subprocess calls, headless synthesis, and audio rendering.

```text
Desktop UI (helper.py)
   ├── "runtime": "host"  --> Python Host Tool (e.g. vital_preset.py, vital_render.py)
   │                             ├── Headless Synthesis (Vita / DawDreamer)
   │                             ├── File I/O (%APPDATA%\Live Actions\...)
   │                             └── Emits audio WAV / .vital preset
   │
   └── "runtime": "bridge" --> OSC Bridge (UDP 11924) --> Live Actions Bridge.amxd
                                                             └── Ableton Live Object Model (LOM)
```

---

## 2. Blueprint A: Vital Preset Generator Tool (`tools/vital-preset`)

### `tools/vital-preset/tool.json`
```json
{
  "id": "vital-preset",
  "name": "Vital Preset Generator",
  "description": "Procedurally generate or mutate custom Vital (.vital) synthesizer presets from archetype styles or text prompts.",
  "accent": "#00F2FE",
  "version": "1.0",
  "enabled": true,
  "runtime": "host",
  "fields": [
    {
      "id": "archetype",
      "label": "Sound Archetype",
      "type": "select",
      "options": ["Reese Bass", "Neo-Soul Pluck", "80s Synthwave Lead", "Ambient Pad", "Super Saw"],
      "default": "Reese Bass",
      "hint": "Base sonic architecture."
    },
    {
      "id": "patch_name",
      "label": "Preset Name",
      "type": "text",
      "default": "Genius Sound 01",
      "hint": "Name saved in the preset header."
    },
    {
      "id": "randomize_rate",
      "label": "Sweet-Spot Randomize (%)",
      "type": "text",
      "default": "15",
      "hint": "0 for pure archetype, 10-30% for subtle variation."
    },
    {
      "id": "destination",
      "label": "Destination",
      "type": "select",
      "options": ["Vital User Library", "Live Actions Presets Folder"],
      "default": "Vital User Library",
      "hint": "Where to write the .vital file on disk."
    }
  ]
}
```

### Python Host Runner: `app/vital_preset.py`
```python
"""Vital Preset Host Runner for Live Actions Helper."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

def run(fields: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    archetype = str(fields.get("archetype") or "Reese Bass")
    patch_name = str(fields.get("patch_name") or "Genius Patch").strip()
    dest_choice = str(fields.get("destination") or "Vital User Library")
    
    # 1. Resolve Target Output Directory
    if dest_choice == "Vital User Library":
        out_dir = Path.home() / "Documents" / "Vital" / "User" / "Presets" / "Live Actions"
    else:
        appdata = Path(os.environ.get("APPDATA", str(Path.home())))
        out_dir = appdata / "Live Actions" / "Presets"
        
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{patch_name}.vital"
    
    # 2. Build Preset JSON (using recipes from doc_003)
    preset_data = {
        "author": "Live Actions Genius",
        "preset_name": patch_name,
        "preset_style": archetype,
        "synth_version": "1.5.5",
        "settings": {
            "polyphony": 1.0 if "Bass" in archetype else 8.0,
            "osc_1_on": 1.0,
            "osc_1_level": 0.75,
            "filter_1_on": 1.0,
            "filter_1_cutoff": 48.0,
            "env_1_attack": 0.005,
            "env_1_decay": 0.8,
            "env_1_sustain": 0.5,
            "env_1_release": 0.2
        }
    }
    
    # 3. Write Output
    out_file.write_text(json.dumps(preset_data, indent=2), encoding="utf-8")
    
    return {
        "ok": True,
        "message": f"Saved '{patch_name}.vital' to {out_dir.name}",
        "path": str(out_file)
    }
```

---

## 3. Blueprint B: Headless Synth Baker Tool (`tools/vital-render`)

### `tools/vital-render/tool.json`
```json
{
  "id": "vital-render",
  "name": "Vital Headless Baker",
  "description": "Render a Vital preset to audio faster-than-realtime via headless Python (DawDreamer/Vita) and inject into the active Live Set.",
  "accent": "#4FACFE",
  "version": "1.0",
  "enabled": true,
  "runtime": "host",
  "fields": [
    {
      "id": "preset_path",
      "label": "Preset (.vital)",
      "type": "text",
      "default": "",
      "hint": "Full path to preset file or leave blank for active."
    },
    {
      "id": "root_note",
      "label": "MIDI Root Note",
      "type": "select",
      "options": ["C1 (24)", "C2 (36)", "C3 (48)", "C4 (60)"],
      "default": "C2 (36)"
    },
    {
      "id": "duration_beats",
      "label": "Duration (Beats)",
      "type": "text",
      "default": "4",
      "hint": "Length of audio render in quarter-note beats."
    },
    {
      "id": "destination",
      "label": "Destination",
      "type": "select",
      "options": ["Add to Live Set", "Save to PC"],
      "default": "Add to Live Set"
    }
  ]
}
```

### Integration into `app/helper.py`
Register the runner in `HOST_TOOLS`:

```python
# app/helper.py
import vital_preset
import vital_render

HOST_TOOLS: dict[str, Any] = {
    "tts-vocal": tts_vocal.run,
    "audio-sample": audio_sample.run,
    "vital-preset": vital_preset.run,
    "vital-render": vital_render.run,
}
```

When `"Add to Live Set"` is selected, `helper.py` runs `_place_generated_file()` on the worker thread, queries available clip slots on the ticked audio track via `bridge.call_live("read_track", ...)`, and invokes `bridge.call_live("create_clip", {"track_index": track_index, "slot_index": slot_index, "sample_file": result_path})` (or with `"arrangement_start"` for Arrangement placement) to instantiate the audio clip directly in the Set.
