---
title: Compressed Room Reverb
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_compressed_room_reverb
pages: 1
words: 269
source: ableton_dataset.jsonl
---
# Compressed Room Reverb

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Compressed Room Reverb'. It uses a parallel processing structure with two branches: a 'Wet' branch containing a reverb and a compressor, and a 'Dry' branch for the original signal. It features 8 custom macro controls designed to shape the room's character and compression intensity.

> **Emotional Vibe:** A tight, controlled, and punchy room sound. It feels 'small' but dense, perfect for adding weight to drums without washing them out in a long tail.

## Technical Architecture & Signal Chain
Audio Effect Rack (AER) utilizing parallel branching. Branch 0 ('Wet') contains a Reverb device (preset: Drums Room) followed by a Compressor2 device. Branch 1 ('Dry') is a clean pass-through. The rack includes 8 mapped macro controls and 4 user-defined snapshots.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevicePreset). 2. Analyze Branches: Branch 0 is 'Wet', Branch 1 is 'Dry'. 3. Inspect 'Wet' Branch Devices: Device 1 is Reverb (Drums Room), Device 2 is Compressor2. 4. Extract Parameters for Reverb: Pre-delay, Decay, Room Size, etc. 5. Extract Parameters for Compressor: Threshold, Ratio, Attack, Release, etc. 6. Map Macros: Identify the names and current values of the 8 macro knobs. 7. Identify Snapshots: Basement, Bright Room, In The Attic, Moon's Hangar.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Compressed Room Reverb
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Compressed Room Reverb"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_compressed_room_reverb.xml` (61,304 bytes).
