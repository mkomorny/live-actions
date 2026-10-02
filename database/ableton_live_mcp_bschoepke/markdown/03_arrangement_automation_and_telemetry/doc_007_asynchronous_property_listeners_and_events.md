---
id: 03_arrangement_automation_and_telemetry_doc_007_asynchronous_property_listeners_and_events
title: Asynchronous Property Observation & Live Event Queue
category: 03_arrangement_automation_and_telemetry
pages: 1
words: 770
source: 03_arrangement_automation_and_telemetry/doc_007_asynchronous_property_listeners_and_events.md
---
# Asynchronous Property Observation & Live Event Queue

## 1. The Need for Event-Driven Agent Observation

Typical AI interactions are strictly request-response: the user asks a question, the agent queries the DAW, and replies.

However, intelligent co-producers need to **observe** Live in the background:
- Detecting when the producer hits Play or Stop.
- Detecting when the producer selects a new track or changes a device.
- Monitoring audio fader tweaks or tempo adjustments in real time.

---

## 2. Tool Interfaces: `live_observe` & `live_events`

### `live_observe`
Attaches or detaches an asynchronous listener to any listenable LOM property:
```json
{
  "ref": "live_set",
  "property": "tempo",
  "enabled": true
}
```

Listenable properties include:
- `live_set`: `tempo`, `is_playing`, `current_song_time`, `signature_numerator`.
- `live_set/view`: `selected_track`, `selected_scene`, `detail_clip`.
- `live_set/tracks/X`: `mute`, `solo`, `arm`, `name`, `color`.
- `live_set/tracks/X/devices/Y/parameters/Z`: `value`.

### `live_events`
Drains the ring buffer of captured listener events:
```json
{
  "events": [
    {"ref": "live_set", "property": "tempo", "value": 128.0, "time": 1726456000.12},
    {"ref": "live_set/view", "property": "selected_track", "value": 2, "time": 1726456002.45}
  ]
}
```

This allows Live Actions Genius to maintain conversational awareness of what you are doing in Ableton without repeated polling!
