---
title: Call Back
category: time_based_spatial
subcategory: delay
id: time_based_spatial_call_back
pages: 1
words: 284
source: ableton_dataset.jsonl
---
# Call Back

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Call Back' created by Sean Charles. It uses a parallel processing structure (two branches) to allow for blending between a heavily processed signal and a clean 'Dry' signal.

> **Emotional Vibe:** This preset is designed for 'Space' and 'Call Back' textures—likely intended for cinematic, ambient, or psychedelic soundscapes where you need to transition from a clean signal to a washed-out, modulated, and compressed rhythmic texture.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing two main branches: a complex serial chain in Branch 0 and a clean pass-through in Branch 1. The signal chain in Branch 0 consists of an Auto Filter, followed by an Echo (with heavy internal modulation), and finished with a Compressor. It features 8 user-mapped macros and three distinct macro snapshots for rapid timbre shifting.

## Chain of Thought Sound Design Breakdown
1. Identify the Root: It's an Audio Effect Rack (GroupDevicePreset). 2. Analyze Branches: Branch 0 is the main effect chain; Branch 1 is named 'Dry'. 3. Deconstruct Branch 0: Device 0 = Auto Filter, Device 1 = Echo, Device 2 = Compressor. 4. Extract Parameters: For each device, pull Cutoff, Resonance, Delay Time, Feedback, Threshold, Ratio, etc. 5. Analyze Macros: Map the Macro names to their indices. 6. Analyze Snapshots: Identify 'Low Fonk', 'Hallway Marbles', and 'BG Radiation'.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Call Back
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Call Back"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_call_back.xml` (78,807 bytes).
