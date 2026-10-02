---
title: Guitar Echo
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_guitar_echo
pages: 1
words: 189
source: ableton_dataset.jsonl
---
# Guitar Echo

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Guitar Echo' created by Michele Darling. It uses parallel processing (two branches) to blend a heavily processed signal with a clean dry signal.

> **Emotional Vibe:** This preset is designed for lush, expansive guitar textures, blending gritty overdrive with rhythmic echoes and spacey modulation.

## Technical Architecture & Signal Chain
Analysis of the XML reveals an Audio Effect Group utilizing a dual-branch architecture for parallel saturation and time-based processing.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevice). 2. Identify Branches: Branch 0 (Wet/FX) and Branch 1 (Dry). 3. Trace Signal Path in Branch 0: Chorus -> Tube -> Pedal -> Echo -> Saturator -> Limiter. 4. Extract Parameters for each device. 5. Map Macro Controls. 6. Analyze Snapshots.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Guitar Echo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Guitar Echo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_guitar_echo.xml` (87,187 bytes).
