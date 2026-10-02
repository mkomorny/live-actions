---
id: 02_tools_reference_and_schemas_doc_006_devices_drum_racks_and_simpler
title: Drum Rack Pad Inspection, Simpler Slicing & Device Re-Ordering
category: 02_tools_reference_and_schemas
pages: 1
words: 860
source: 02_tools_reference_and_schemas/doc_006_devices_drum_racks_and_simpler.md
---
# Drum Rack Pad Inspection, Simpler Slicing & Device Re-Ordering

## 1. Drum Rack 128-Pad Introspection & Pad Mute/Solo

Standard LOM implementations often treat a Drum Rack as a single black-box device. `AbletonMCP` exposes pad-level introspection and control across all 128 MIDI notes (0 to 127):

### Pad Inspection: `get_drum_rack_pads(track_index, device_index)`
Returns a catalog of active pads:
```json
{
  "pads": [
    {"note": 36, "name": "Kick 808", "has_sample": true, "mute": false, "solo": false},
    {"note": 38, "name": "Snare Clap", "has_sample": true, "mute": false, "solo": false},
    {"note": 42, "name": "Closed Hat", "has_sample": true, "mute": false, "solo": false}
  ]
}
```

### Pad Control Commands
- `set_drum_rack_pad_mute(track_index, device_index, note, mute_state)`.
- `set_drum_rack_pad_solo(track_index, device_index, note, solo_state)`.
- `set_drum_pad_name(track_index, device_index, note, new_name)`.

This enables conversational mixing: *"Mute the hats and open cymbals on Drum Rack track 1 for the verse breakdown."*

---

## 2. Simpler & Sampler Sample Introspection

- `get_simpler_sample_info(track_index, device_index)`:
  Returns:
  - `sample_path`: Absolute path to source WAV/AIF on disk.
  - `sample_length`: Total sample frames.
  - `start_marker` / `end_marker`: Current crop points.
  - `playback_mode`: `0` = Classic, `1` = 1-Shot, `2` = Slicing.
  - `warp_enabled`: Whether warping is active inside Simpler.

---

## 3. Dynamic Device Re-ordering on Tracks

`AbletonMCP` allows an AI agent to reorganize the signal chain order:

- `move_device(track_index, from_index, to_index)`.
- `move_device_left(track_index, device_index)`.
- `move_device_right(track_index, device_index)`.
- `set_device_collapsed(track_index, device_index, collapsed)`.
- `toggle_device(track_index, device_index)` (turns device on/off).

### Example Use Case: Automated Signal Chain Repair
If an analysis detects a Reverb placed *before* a high-gain Saturator, Genius invokes:
```python
client.send({
    "type": "move_device",
    "params": {"track_index": 2, "from_index": 1, "to_index": 2}
})
```
