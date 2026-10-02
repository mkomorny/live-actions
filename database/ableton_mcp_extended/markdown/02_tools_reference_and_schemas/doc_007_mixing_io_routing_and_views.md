---
id: 02_tools_reference_and_schemas_doc_007_mixing_io_routing_and_views
title: Mix Routing, Return Tracks, Metering & Session Safety Resets
category: 02_tools_reference_and_schemas
pages: 1
words: 830
source: 02_tools_reference_and_schemas/doc_007_mixing_io_routing_and_views.md
---
# Mix Routing, Return Tracks, Metering & Session Safety Resets

## 1. Return / Send Tracks Control

- `get_return_tracks()`: Returns list of all return buses (`A-Reverb`, `B-Delay`, etc.).
- `set_send_level(track_index, send_index, level)`: Adjusts send amount (0.0 to 1.0).
- `set_return_volume(return_index, volume)`: Sets return fader gain.
- `set_return_pan(return_index, pan)`: Sets return stereo panning.

---

## 2. I/O Routing & Crossfader

### Routing Matrices
- `get_available_inputs(track_index)`: Discovers external audio inputs and internal track taps.
- `set_track_input_routing(track_index, input_type, input_channel)`: Routes hardware mic/synth or sidechain sources.
- `get_available_outputs(track_index)`: Returns Master, Ext Out, or group buses.
- `set_track_output_routing(track_index, output_type, output_channel)`.

### DJ Crossfader
- `set_track_crossfade_assign(track_index, assign)`: `0` = None, `1` = A, `2` = B.
- `set_crossfader(position)`: Panning between -1.0 (Deck A) and +1.0 (Deck B).

---

## 3. Real-Time Metering & CPU Load

- `get_cpu_load()`: Returns Live's DSP audio engine load percentage (0.0 to 100.0%).
- `get_track_output_meter(track_index)`: Returns real-time peak levels `[left_meter, right_meter]` for gain staging.
- `get_master_output_meter()`: Checks master output levels to prevent digital clipping.

---

## 4. Session Panic & Safety Resets

During complex sessions with 40+ tracks, tracks can accidentally remain muted or soloed. `AbletonMCP` provides 1-shot batch reset commands:

- `solo_exclusive(track_index)`: Solos specified track, un-solos all other tracks.
- `unsolo_all()`: Clears solo states across all tracks.
- `unmute_all()`: Un-mutes all tracks.
- `unarm_all()`: Disarms all recording tracks.

```python
def reset_session_monitoring():
    client.send({"type": "unsolo_all"})
    client.send({"type": "unmute_all"})
    client.send({"type": "unarm_all"})
```
