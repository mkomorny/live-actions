---
id: 02_tools_reference_and_schemas_doc_004_track_clip_and_warp_operations
title: Track Lifecycle, Clip Warping & Generative Follow Actions
category: 02_tools_reference_and_schemas
pages: 1
words: 840
source: 02_tools_reference_and_schemas/doc_004_track_clip_and_warp_operations.md
---
# Track Lifecycle, Clip Warping & Generative Follow Actions

## 1. Track Lifecycle Operations

`AbletonMCP` exposes deep track management beyond simple volume/pan:

- `create_midi_track(index)`, `create_audio_track(index)`, `create_return_track()`.
- `delete_track(track_index)`: Safely removes track at index.
- `duplicate_track(track_index)`: Duplicates track with all devices and clips.
- `set_track_name(track_index, name)`: Renames track.
- `set_track_color(track_index, color_hex_or_index)`: Sets track visual tint.
- `set_track_delay(track_index, delay_ms)`: Injects microsecond/millisecond track delay compensation.
- `get_track_is_foldable(track_index)`, `fold_track(track_index, folded)`: Expands or collapses grouped track folders.

---

## 2. Audio Clip Warping & Markers

Audio clips in Live 12 can be warped to match project BPM using various time-stretching algorithms.

### Warp Modes
- `0`: Beats (transient-based, ideal for drums/percussion).
- `1`: Tones (pitch-consistent, ideal for vocals/monophonic synths).
- `2`: Texture (polyphonic ambient textures).
- `3`: Re-Pitch (tape-style speed/pitch lock).
- `4`: Complex (high-fidelity polyphonic music).
- `5`: Complex Pro (advanced formant preservation).

### Warp Commands
- `set_clip_warp_mode(track_index, slot_index, warp_mode)`.
- `get_warp_markers(track_index, slot_index)`: Returns list of beat-to-sample anchor pairs.
- `add_warp_marker(track_index, slot_index, beat_time, sample_time)`.
- `delete_warp_marker(track_index, slot_index, marker_index)`.

---

## 3. Audio Fades & Generative Follow Actions

### Clip Fades
- `set_clip_fade_in(track_index, slot_index, length_beats)`.
- `set_clip_fade_out(track_index, slot_index, length_beats)`.
Eliminates audio clicks at sample boundaries programmatically.

### Generative Follow Actions
Follow actions instruct Live to automatically trigger another clip after a specified number of bars:
- Follow Action Targets: `next`, `previous`, `first`, `last`, `any` (random), `other`, `play_again`, `stop`.
- `set_clip_follow_action(track_index, slot_index, action_a, chance_a, action_b, chance_b, length)`:
  Allows AI to generate self-evolving, generative ambient or drum arrangements that loop probabilistically.
