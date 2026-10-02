---
id: 03_arrangement_automation_and_telemetry_doc_005_session_to_arrangement_sequencing
title: Session-to-Arrangement Clip Transfer & Timeline Sequencing
category: 03_arrangement_automation_and_telemetry
pages: 1
words: 780
source: 03_arrangement_automation_and_telemetry/doc_005_session_to_arrangement_sequencing.md
---
# Session-to-Arrangement Clip Transfer & Timeline Sequencing

## 1. The Bridge Between Loop Jamming and Song Arrangement

In Ableton Live, music production typically starts in Session View (loop-based jamming) and finishes in Arrangement View (linear timeline).

Standard LOM workflows require users to manually record their jams or drag clips between views. `bschoepke/ableton-live-mcp` introduces **`live_clip_duplicate_to_arrangement`**, allowing external agents to stamp Session clips onto the Arrangement timeline programmatically.

---

## 2. Tool Signature & Parameters

```python
live_clip_duplicate_to_arrangement(
    clip_ref="live_set/tracks/0/clip_slots/0/clip",
    time=64.0,              # Bar 17, Beat 1 in 4/4
    destination_track="live_set/tracks/0"
)
```

- `clip_ref` (string, required): Reference to source Session clip.
- `time` (float, required): Start time on Arrangement timeline in beats.
- `destination_track` (string, optional): Target track (defaults to source clip track).

---

## 3. Autonomous Song Arrangement Blueprint

Genius can convert an 8-scene loop sketch into a structured 128-bar song:

```python
def arrange_song_from_scenes(arrangement_map):
    """
    arrangement_map = [
        {"scene_index": 0, "start_bar": 1,  "bars": 16, "name": "Intro"},
        {"scene_index": 1, "start_bar": 17, "bars": 16, "name": "Verse 1"},
        {"scene_index": 2, "start_bar": 33, "bars": 16, "name": "Chorus"},
        {"scene_index": 3, "start_bar": 49, "bars": 16, "name": "Drop"}
    ]
    """
    for section in arrangement_map:
        beat_start = (section["start_bar"] - 1) * 4.0
        # Duplicate clips for all tracks in this scene
        for t_idx in range(track_count):
            client.call("live_clip_duplicate_to_arrangement", {
                "clip_ref": f"live_set/tracks/{t_idx}/clip_slots/{section['scene_index']}/clip",
                "time": beat_start
            })
        # Add a cue locator
        client.call("live_create_locator", {"time": beat_start, "name": section["name"]})
```
