---
id: 03_arrangement_automation_and_telemetry_doc_006_clip_parameter_and_velocity_automation
title: Clip Automation Envelopes & Velocity-to-Modulation Mapping
category: 03_arrangement_automation_and_telemetry
pages: 1
words: 810
source: 03_arrangement_automation_and_telemetry/doc_006_clip_parameter_and_velocity_automation.md
---
# Clip Automation Envelopes & Velocity-to-Modulation Mapping

## 1. Clip Automation Envelopes (`live_clip_envelope`)

Ableton clips store modulation and automation envelopes for every device parameter on their track.

### Tool Capabilities
- Inspect existing breakpoint curves for a named parameter.
- Inject mathematical automation curves (ramps, LFOs, exponential sweeps).
- Clear or scale envelopes.

```python
# Create an 8-bar low-pass filter opening sweep
client.call("live_clip_envelope", {
    "clip": "live_set/tracks/1/clip_slots/0/clip",
    "parameter": "live_set/tracks/1/devices/0/parameters/1",  # Auto Filter Frequency
    "breakpoints": [
        {"time": 0.0, "value": 200.0},
        {"time": 16.0, "value": 1200.0},
        {"time": 32.0, "value": 20000.0}
    ]
})
```

---

## 2. Note Velocity-to-Modulation Mapping (`live_clip_velocity_envelope`)

`live_clip_velocity_envelope` reads note velocity values inside a MIDI clip and generates an automation curve that dynamically follows note strike intensity:

- Accented notes create peaks in filter cutoff or distortion drive.
- Ghost notes maintain subtle, dark timbre.

---

## 3. Audio Clip Warp Markers (`live_clip_warp_markers`)

Exposes surgical inspection and editing of audio warp markers:
- Adjusts transient alignment points to correct rhythmic drift.
- Locks audio loops to strict musical measure boundaries without re-rendering audio.
