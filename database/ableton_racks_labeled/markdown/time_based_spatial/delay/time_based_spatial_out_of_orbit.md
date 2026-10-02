---
title: Out Of Orbit
category: time_based_spatial
subcategory: delay
id: time_based_spatial_out_of_orbit
pages: 1
words: 216
source: ableton_dataset.jsonl
---
# Out Of Orbit

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Out Of Orbit' created by Sean Charles. It uses a dual-branch structure (Wet/Dry) to allow for parallel processing and precise dry/wet blending via the rack macros.

> **Emotional Vibe:** An expansive, spacey, and evolving texture generator that feels like drifting through a nebula—pulsating with rhythmic movement and deep, filtered echoes.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing a complex signal chain of four devices in the main branch, utilizing LFO modulation, ducking, and frequency-dependent filtering. It features 8 mapped macro controls for real-time performance.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack. I will analyze the Macro controls first, then dive into each branch. Branch 0 is the 'Wet' chain containing Auto Filter -> Echo -> Auto Pan -> Compressor (Gentle Squeeze). Branch 1 is a 'Dry' chain with no devices. This confirms it's a parallel dry/wet rack.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Out Of Orbit
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Out Of Orbit"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_out_of_orbit.xml` (82,613 bytes).
