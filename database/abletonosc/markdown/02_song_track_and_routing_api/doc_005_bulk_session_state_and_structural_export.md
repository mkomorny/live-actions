# Bulk Session State Query & Structural JSON Export

> **Module:** `abletonosc.song`  
> **Key Endpoints:** `/live/song/get/track_data`, `/live/song/export/structure`  
> **Performance:** Multi-track bulk queries in <5ms, full session dump in 1 shot  

---

## 1. The Bulk Track Data Engine (`/live/song/get/track_data`)

In complex Live sessions with 20-50 tracks, sending individual OSC messages for every fader, name, clip, and device creates network overhead.  
AbletonOSC provides a unified batch endpoint:

```text
/live/song/get/track_data <track_min> <track_max> [properties...]
```

### Supported Properties:
- `track.name`, `track.volume`, `track.panning`, `track.mute`, `track.solo`, `track.arm`
- `track.color`, `track.num_devices`
- `clip.name`, `clip.length`, `clip.color`, `clip.is_playing`

### Example Query:
```text
/live/song/get/track_data 0 4 track.name track.volume clip.name
```
Returns a single flattened tuple:
```text
[
  track_0_name, track_0_volume, clip_0_0_name, clip_0_1_name, ...,
  track_1_name, track_1_volume, clip_1_0_name, clip_1_1_name, ...,
  ...
]
```
Passing `track_max = -1` queries all tracks in the Live Set up to the end!

---

## 2. Full Session Structural Export (`/live/song/export/structure`)

AbletonOSC implements an atomic structural serialization engine:

```python
# In song.py:
def song_export_structure(params):
    tracks = []
    for track_index, track in enumerate(self.song.tracks):
        group_track = None
        if track.group_track is not None:
            group_track = list(self.song.tracks).index(track.group_track)
        track_data = {
            "index": track_index,
            "name": track.name,
            "is_foldable": track.is_foldable,
            "group_track": group_track,
            "clips": [],
            "devices": []
        }
        for clip_index, clip_slot in enumerate(track.clip_slots):
            if clip_slot.clip:
                track_data["clips"].append({
                    "index": clip_index,
                    "name": clip_slot.clip.name,
                    "length": clip_slot.clip.length,
                })
        for device_index, device in enumerate(track.devices):
            track_data["devices"].append({
                "class_name": device.class_name,
                "type": device.type,
                "name": device.name,
                "parameters": [
                    {
                        "name": p.name,
                        "value": p.value,
                        "min": p.min,
                        "max": p.max,
                        "is_quantized": p.is_quantized
                    } for p in device.parameters
                ]
            })
        tracks.append(track_data)

    output_path = os.path.join(tempfile.gettempdir(), "abletonosc-structure.json")
    with open(output_path, "w") as f:
        json.dump(tracks, f, indent=2)
```

### Live Actions Genius Workflow:
1. Send `/live/song/export/structure` via UDP.
2. Read `%TEMP%\abletonosc-structure.json` locally in Python.
3. In under 10ms, Genius has the complete structural model of every track, group, clip, device, and parameter in the project!
