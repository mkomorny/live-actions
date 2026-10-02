---
id: 02_tools_reference_and_schemas_doc_003_transport_arranger_and_locators
title: Arrangement View, Timeline Locators & Transport Operations
category: 02_tools_reference_and_schemas
pages: 1
words: 790
source: 02_tools_reference_and_schemas/doc_003_transport_arranger_and_locators.md
---
# Arrangement View, Timeline Locators & Transport Operations

## 1. Arrangement Timeline Control

While traditional M4L tools focus almost entirely on Session clips, `AbletonMCP` provides complete programmatic control over Live's linear Arrangement timeline.

### Key Tools & Commands

- `get_arrangement_length()`: Returns total song duration in beats or seconds.
- `set_arrangement_loop(start_time, length, enabled)`: Sets the global arrangement loop brace.
- `jump_to_time(time)`: Moves the playhead to any specific beat (e.g. `16.0` = bar 5, beat 1 in 4/4).
- `scrub_by(amount)`: Jumps forward or backward relative to the current position.

```python
# Move playhead to bar 17 (beat 64.0) and loop 16 bars
client.send({
    "type": "set_arrangement_loop",
    "params": {"start_time": 64.0, "length": 64.0, "enabled": True}
})
client.send({"type": "jump_to_time", "params": {"time": 64.0}})
```

---

## 2. Arrangement Cue Points & Locators

Locators are visual marker flags along Live's Arrangement timeline used to divide songs into sections (Intro, Verse, Chorus, Bridge, Drop, Outro).

### Commands
- `get_locators()`: Returns list of all locators: `[{"time": 0.0, "name": "Intro"}, {"time": 32.0, "name": "Verse 1"}]`.
- `create_locator(time, name)`: Adds a new cue point at a specific beat location.
- `delete_locator(index)`: Removes a locator by index.
- `jump_to_cue_point(name_or_index)`: Jumps playhead to named section.
- `jump_to_next_cue()`, `jump_to_prev_cue()`: Skips between sections.

### Live Actions Blueprint: 1-Click Song Structure Generator
```python
def generate_song_structure(structure_map=[("Intro", 0), ("Verse 1", 32), ("Chorus", 64), ("Verse 2", 96), ("Chorus 2", 128), ("Outro", 160)]):
    for name, beat in structure_map:
        client.send({"type": "create_locator", "params": {"time": float(beat), "name": name}})
```

---

## 3. Transport, Metronome & Count-In

- `set_tempo(tempo)`: Sets BPM (20.0 to 999.0).
- `start_playback()`, `stop_playback()`, `continue_playing()`.
- `set_metronome(enabled)`: Toggles click track on/off.
- `set_count_in_duration(bars)`: Sets 0, 1, 2, or 4 bars count-in before recording.
- `tap_tempo()`: Simulates tap-tempo button clicks.
- `set_punch_in(enabled)`, `set_punch_out(enabled)`: Configures arrangement punch boundaries.
