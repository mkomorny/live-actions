# Live Actions Genius Action Blueprints

> **Module:** `app.genius_client`  
> **Target Toolset:** Live Actions Helper & Live Actions Genius  
> **Schema Standard:** `live_*` callable tool signatures  

---

## 1. Blueprint: Full Session Structural Dump (`live_export_project_structure`)

```python
def live_export_project_structure() -> dict:
    """
    Triggers AbletonOSC to dump the complete structural hierarchy of the Live Set
    (all tracks, nested groups, clips, loaded devices, and parameters) into a local JSON file.
    """
    import tempfile, json, os, time
    
    # 1. Trigger export via OSC
    osc_client.send_message("/live/song/export/structure", [])
    
    target_path = os.path.join(tempfile.gettempdir(), "abletonosc-structure.json")
    
    # 2. Wait up to 500ms for file write
    for _ in range(10):
        if os.path.exists(target_path) and (time.time() - os.path.getmtime(target_path)) < 2.0:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"ok": True, "tracks_count": len(data), "structure": data}
        time.sleep(0.05)
        
    return {"ok": False, "error": "Export timed out"}
```

---

## 2. Blueprint: Multi-Track Bulk Query (`live_bulk_track_query`)

```python
def live_bulk_track_query(track_start: int = 0, track_count: int = 12, properties: list[str] = None) -> dict:
    """
    Queries multi-track names, volumes, pans, and clip states in a single UDP packet.
    """
    if properties is None:
        properties = ["track.name", "track.volume", "track.mute", "track.num_devices"]
        
    params = [track_start, track_start + track_count] + properties
    raw_data = osc_client.query("/live/song/get/track_data", tuple(params))
    
    return {"ok": True, "raw_batch": raw_data}
```

---

## 3. Blueprint: Track Bus & Sidechain I/O Routing (`live_route_track_io`)

```python
def live_route_track_io(track_index: int, output_type: str = None, output_channel: str = None) -> dict:
    """
    Configures audio or MIDI output routing for submix bussing (e.g. routing to 'Drum Bus').
    """
    if output_type:
        osc_client.send_message("/live/track/set/output_routing_type", [track_index, output_type])
    if output_channel:
        osc_client.send_message("/live/track/set/output_routing_channel", [track_index, output_channel])
        
    return {"ok": True, "track_index": track_index, "output_type": output_type}
```

---

## 4. Blueprint: Dynamic MIDI CC Mapping (`live_map_parameter_to_cc`)

```python
def live_map_parameter_to_cc(track_index: int, device_index: int, parameter_index: int, channel: int, cc: int) -> dict:
    """
    Binds a physical or virtual MIDI CC directly to a device parameter via AbletonOSC.
    """
    osc_client.send_message("/live/midimap/map_cc", [track_index, device_index, parameter_index, channel, cc])
    return {
        "ok": True,
        "mapped": {
            "target": f"Track {track_index} -> Device {device_index} -> Param {parameter_index}",
            "midi": f"Ch {channel} CC {cc}"
        }
    }
```

---

## 5. Blueprint: 5-Tuple OSC Clip Notes (`live_osc_batch_clip_notes`)

```python
def live_osc_batch_clip_notes(track_index: int, slot_index: int, notes: list[dict], action: str = "add") -> dict:
    """
    Reads, adds, or clears 5-tuple MIDI notes over OSC.
    Notes format: [{'pitch': 60, 'start_time': 0.0, 'duration': 0.5, 'velocity': 100, 'mute': 0}]
    """
    if action == "add":
        params = [track_index, slot_index]
        for n in notes:
            params.extend([int(n['pitch']), float(n['start_time']), float(n['duration']), int(n.get('velocity', 100)), int(n.get('mute', 0))])
        osc_client.send_message("/live/clip/add/notes", params)
        return {"ok": True, "added_notes": len(notes)}
    elif action == "get":
        raw = osc_client.query("/live/clip/get/notes", (track_index, slot_index))
        # unpack 5-tuples
        parsed = []
        for i in range(2, len(raw), 5):
            parsed.append({"pitch": raw[i], "start_time": raw[i+1], "duration": raw[i+2], "velocity": raw[i+3], "mute": raw[i+4]})
        return {"ok": True, "notes": parsed}
```
