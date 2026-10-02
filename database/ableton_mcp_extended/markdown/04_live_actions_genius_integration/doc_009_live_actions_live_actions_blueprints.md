---
id: 04_live_actions_genius_integration_doc_009_live_actions_live_actions_blueprints
title: 'Live Actions Genius Blueprints: Extended Actions Suite'
category: 04_live_actions_genius_integration
pages: 1
words: 850
source: 04_live_actions_genius_integration/doc_009_live_actions_live_actions_blueprints.md
---
# Live Actions Genius Blueprints: Extended Actions Suite

## 1. Blueprint: Instant Capture MIDI (`live_capture_midi`)

```python
def live_capture_midi():
    """Recovers unrecorded MIDI improvisation from Live 12's retrospective buffer."""
    client = get_mcp_socket_client()
    res = client.send({"type": "get_can_capture_midi"})
    if not res.get("result"):
        return {"ok": False, "message": "No retrospective MIDI notes found in buffer."}
    
    capture_res = client.send({"type": "capture_midi"})
    return {"ok": True, "message": "Retrospective MIDI captured successfully into new clip."}
```

---

## 2. Blueprint: Arrangement Cue Locator Manager (`live_create_locator`)

```python
def live_create_locator(name: str, bar_number: int):
    """Adds a cue marker flag on the Arrangement timeline at the specified bar."""
    beat_time = (bar_number - 1) * 4.0  # 4/4 assumption
    client = get_mcp_socket_client()
    res = client.send({
        "type": "create_locator",
        "params": {"time": float(beat_time), "name": name}
    })
    return {"ok": True, "message": f"Created locator '{name}' at bar {bar_number}."}
```

---

## 3. Blueprint: Drum Rack Pad-Level Mixer (`live_get_drum_rack_pads`, `live_mute_drum_pad`)

```python
def live_get_drum_rack_pads(track_index: int, device_index: int = 0):
    """Scans all 128 Drum Rack pads and returns populated instruments and mute states."""
    client = get_mcp_socket_client()
    return client.send({
        "type": "get_drum_rack_pads",
        "params": {"track_index": track_index, "device_index": device_index}
    })

def live_set_drum_pad_mute(track_index: int, note: int, mute: bool, device_index: int = 0):
    """Mutes or un-mutes an individual drum pad by MIDI note number."""
    client = get_mcp_socket_client()
    return client.send({
        "type": "set_drum_rack_pad_mute",
        "params": {"track_index": track_index, "device_index": device_index, "note": note, "mute": mute}
    })
```

---

## 4. Blueprint: Audio Clip Warp Mode Configurator (`live_set_clip_warp`)

```python
def live_set_clip_warp(track_index: int, slot_index: int, warp_mode: str = "complex_pro"):
    """Configures audio clip time-stretching algorithm."""
    mode_map = {"beats": 0, "tones": 1, "texture": 2, "repitch": 3, "complex": 4, "complex_pro": 5}
    code = mode_map.get(warp_mode.lower(), 4)
    client = get_mcp_socket_client()
    return client.send({
        "type": "set_clip_warp_mode",
        "params": {"track_index": track_index, "slot_index": slot_index, "warp_mode": code}
    })
```

---

## 5. Blueprint: Session Panic & Emergency Reset (`live_reset_mix_states`)

```python
def live_reset_mix_states():
    """Un-solos, un-mutes, and disarms all tracks in the Live Set."""
    client = get_mcp_socket_client()
    client.send({"type": "unsolo_all"})
    client.send({"type": "unmute_all"})
    client.send({"type": "unarm_all"})
    return {"ok": True, "message": "All tracks un-soloed, un-muted, and disarmed."}
```
