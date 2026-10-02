---
id: 02_tools_reference_and_schemas_doc_005_note_editing_and_midi_capture
title: Instant MIDI Capture & Advanced Note Manipulation
category: 02_tools_reference_and_schemas
pages: 1
words: 810
source: 02_tools_reference_and_schemas/doc_005_note_editing_and_midi_capture.md
---
# Instant MIDI Capture & Advanced Note Manipulation

## 1. Instant "Capture MIDI" Recovery

Live 12 features a continuous circular MIDI buffer that records all incoming MIDI notes even when the transport is stopped and the record button is inactive.

### Commands
- `get_can_capture_midi()`: Returns `True` if notes exist in Live's internal retrospective buffer.
- `capture_midi()`: Triggers Live's native `song.capture_midi()`. Instantly dumps the buffered notes into a newly created clip on the armed/ticked MIDI track and matches tempo to the player's cadence!

```python
# Retrospective MIDI recovery
res = client.send({"type": "get_can_capture_midi"})
if res.get("result"):
    client.send({"type": "capture_midi"})
    print("Captured improvisation into a new clip!")
```

---

## 2. Note Manipulation Operations

`AbletonMCP` provides surgical note editing tools without requiring full clip re-writes:

### 1. `get_notes_in_range(track_index, slot_index, start_time, time_span, start_pitch, pitch_span)`
Queries a specific bounding box of notes (e.g. only notes in bar 2 between C1 and C2).

### 2. `move_clip_notes(track_index, slot_index, note_ids, time_offset, pitch_offset)`
Shifts existing notes forward/backward in time or up/down in pitch without deleting and recreating them.

### 3. `transpose_notes(track_index, slot_index, semitones)`
Transposes all notes in a clip by semitone intervals (-12 for octave down, +7 for fifth up).

### 4. `remove_notes(track_index, slot_index, pitch, start_time, duration)`
Deletes specific notes matching pitch and timeline coordinates.

### 5. `remove_all_notes(track_index, slot_index)`
Clears the clip's note canvas while preserving clip length, loop brace, and automation envelopes.

### 6. `duplicate_clip_loop(track_index, slot_index)`
Doubles the length of the clip (e.g. 2 bars -> 4 bars) and duplicates all notes into the second half, identical to pressing `Duplicate Loop` in Live's GUI.
