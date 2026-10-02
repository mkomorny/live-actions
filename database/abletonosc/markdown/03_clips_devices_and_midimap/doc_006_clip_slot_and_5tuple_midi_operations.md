# Clip Slots & 5-Tuple OSC MIDI Note Operations

> **Module:** `abletonosc.clip`, `abletonosc.clip_slot`  
> **Upstream Handlers:** `ClipHandler`, `ClipSlotHandler`  
> **Key Capabilities:** Clip launching, 5-tuple MIDI note creation, bounded note filtering  

---

## 1. Clip Slot Operations

Clip slots are addressed by `(track_index, slot_index)`:

| Endpoint | Parameters | Action |
| :--- | :--- | :--- |
| `/live/clip_slot/fire` | `track, slot` | Launches the clip or begins recording. |
| `/live/clip_slot/stop` | `track, slot` | Stops clip playback in this slot. |
| `/live/clip_slot/create_clip` | `track, slot, length: float` | Creates an empty MIDI clip of specified length in beats. |
| `/live/clip_slot/delete_clip` | `track, slot` | Deletes the clip in this slot. |
| `/live/clip_slot/duplicate_clip_to` | `track, slot, dst_track, dst_slot` | Duplicates clip to another slot. |
| `/live/clip_slot/get/has_clip` | `track, slot` | Returns `1` if slot contains a clip, `0` if empty. |

---

## 2. 5-Tuple Extended MIDI Note Architecture

AbletonOSC standardizes all MIDI note interactions into flat tuples of 5 attributes:
$$\text{Note} = [\text{pitch}, \text{start\_time}, \text{duration}, \text{velocity}, \text{mute}]$$

- `pitch` (`int`): MIDI note number (`0` to `127`, e.g. 60 = C3).
- `start_time` (`float`): Beat position in clip timeline (e.g. `0.0`, `1.5`, `3.25`).
- `duration` (`float`): Note length in beats (e.g. `0.25` for 16th, `1.0` for quarter).
- `velocity` (`float` / `int`): Note velocity (`1` to `127`).
- `mute` (`int`): `0` = active, `1` = muted.

---

## 3. Reading Notes (`/live/clip/get/notes`)

Can be invoked with 0 arguments (queries entire clip) or 4 bounding arguments:
```text
/live/clip/get/notes <track> <slot> [pitch_start pitch_span time_start time_span]
```

### Bounded Window Query Example:
Query notes in Bar 1 (beats 0.0 to 4.0) across all pitches:
```text
/live/clip/get/notes 0 0 0 128 0.0 4.0
```
Returns:
```text
(60, 0.0, 0.5, 100, 0, 64, 1.0, 0.5, 95, 0, 67, 2.0, 1.0, 110, 0)
```

---

## 4. Adding Notes (`/live/clip/add/notes`)

Notes are appended by streaming a flat array of 5-tuples:

```text
/live/clip/add/notes <track> <slot> <p1> <t1> <d1> <v1> <m1> <p2> <t2> <d2> <v2> <m2> ...
```

### Python Helper Example:
```python
def add_notes_to_clip(client, track: int, slot: int, notes: list[dict]):
    params = [track, slot]
    for n in notes:
        params.extend([
            int(n["pitch"]),
            float(n["start_time"]),
            float(n["duration"]),
            int(n.get("velocity", 100)),
            int(n.get("mute", 0))
        ])
    client.send("/live/clip/add/notes", *params)
```

---

## 5. Surgical Note Removal (`/live/clip/remove/notes`)

Removes all notes within a bounding pitch and time box:
```text
/live/clip/remove/notes <track> <slot> <pitch_start> <pitch_span> <time_start> <time_span>
```
To clear an entire 4-bar clip:
```text
/live/clip/remove/notes 0 0 0 128 0.0 16.0
```
