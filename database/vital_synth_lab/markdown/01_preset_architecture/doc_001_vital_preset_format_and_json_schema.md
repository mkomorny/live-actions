---
id: 01_preset_architecture_doc_001_vital_preset_format_and_json_schema
title: Vital Preset File Format (.vital) & JSON Schema Architecture
category: 01_preset_architecture
pages: 1
words: 523
source: 01_preset_architecture/doc_001_vital_preset_format_and_json_schema.md
---
# Vital Preset File Format (.vital) & JSON Schema Architecture

## Overview
Unlike proprietary binary VST preset formats (such as VST2 `.fxb`/`.fxp` or Cubase `.vstpreset`), Matt Tytel's **Vital** polyphonic synthesizer stores presets natively as structured JSON documents. A `.vital` file is either a standard UTF-8 JSON text file or a GZIP-compressed JSON container.

When uncompressed, the document reveals a comprehensive parameter dictionary describing the state of all 3 wavetable oscillators, the sample generator, 2 multiband filters, 6 envelopes, 8 LFOs, 4 random modulators, the modulation matrix, and the master effects chain.

---

## Container Structure & File Envelope

At the top level, a `.vital` document contains the following primary keys:

```json
{
  "author": "Live Actions Genius",
  "comments": "Procedurally generated 808 Reese Bass",
  "macro1": "Filter Cutoff",
  "macro2": "Reverb Mix",
  "macro3": "Distortion Drive",
  "macro4": "Unison Spread",
  "preset_name": "Reese Bass Alpha",
  "preset_style": "Bass",
  "synth_version": "1.5.5",
  "settings": {
    "bypass": 0.0,
    "beats_per_minute": 120.0,
    "osc_1_on": 1.0,
    "osc_1_wave_frame": 0.0,
    "osc_1_unison_voices": 4.0,
    "osc_1_detune_power": 1.5,
    "osc_1_detune_range": 2.0,
    "...": "..."
  },
  "wave_data": [
    {
      "name": "Init Wave",
      "author": "Matt Tytel",
      "full_normalize": true,
      "remove_all_dc": true,
      "components": []
    }
  ],
  "sample": {
    "name": "",
    "sample_rate": 44100,
    "samples": []
  }
}
```

### Compression Handling in Python
Vital automatically detects whether a file begins with the GZIP magic header (`0x1F 0x8B`). To ensure 100% interoperability when loading or generating presets from Python:

```python
import gzip
import json
from pathlib import Path

def load_vital_preset(path: Path) -> dict:
    """Load a .vital preset whether it is raw JSON or gzipped."""
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        raw_text = gzip.decompress(data).decode("utf-8")
    else:
        raw_text = data.decode("utf-8")
    return json.loads(raw_text)

def save_vital_preset(preset_dict: dict, out_path: Path, compress: bool = False):
    """Save a .vital preset. Plain text JSON is easier to inspect and debug."""
    raw_text = json.dumps(preset_dict, indent=2)
    if compress:
        out_path.write_bytes(gzip.compress(raw_text.encode("utf-8")))
    else:
        out_path.write_text(raw_text, encoding="utf-8")
```

---

## Critical Settings Dictionary Specifications

All synthesiser controls live in the `"settings"` object. In Vital, float values are normalized according to parameter domain types:

### 1. Master & Voice Settings
| Parameter Key | Type | Valid Range | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `polyphony` | Float (int) | `1.0` - `32.0` | `16.0` | Number of simultaneous voices |
| `voice_priority` | Float (enum) | `0.0` - `3.0` | `0.0` | 0=Drop Oldest, 1=Drop Newest, 2=Drop Lowest, 3=Drop Highest |
| `portamento_time` | Float | `-9.0` - `3.0` | `-4.0` | Logarithmic glide time in seconds (e.g. $2^{\text{val}}$) |
| `portamento_slope` | Float | `-1.0` - `1.0` | `0.0` | Portamento pitch curve (-1.0 = logarithmic, 1.0 = exponential) |
| `legato` | Float (bool) | `0.0` or `1.0` | `0.0` | If 1, legato playing does not retrigger envelopes |
| `volume` | Float | `0.0` - `1.0` | `0.7` | Master output level |

---

## Directory Targets for Generated Presets

When creating Vital presets on Windows, files can be written directly to the user's standard library directory:
- **Vital User Presets**: `%USERPROFILE%\Documents\Vital\User\Presets\`
- **Live Actions Custom Presets**: `%USERPROFILE%\Documents\Vital\User\Presets\Live Actions\`
- **User Library Storage**: `<User Library>\Presets\Instruments\Max Instrument\Live Actions Presets\`

Writing into these paths enables immediate recognition in Vital's preset browser without requiring a DAW restart.
