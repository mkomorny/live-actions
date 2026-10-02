---
title: Jamaica Plains
category: time_based_spatial
subcategory: delay
id: time_based_spatial_jamaica_plains
pages: 1
words: 238
source: ableton_dataset.jsonl
---
# Jamaica Plains

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Jamaica Plains' designed by Huston Singletary. It uses a parallel processing structure with two branches: one heavily processed effect chain (Echo + Compressor) and one 'Dry' branch for blending.

> **Emotional Vibe:** A lush, rhythmic, and textured space effect. It combines syncopated delays with heavy modulation (wobble, noise, and reverb) and a controlled compression stage to glue the echoes together, creating a 'wall of sound' that can be blended with a clean signal.

## Technical Architecture & Signal Chain
An Ableton Live 11 Audio Effect Rack utilizing parallel branching. Branch 0 contains a highly modulated Echo device followed by a Compressor2. Branch 1 is a dedicated Dry path. The rack features 8 macro controls mapped to delay time, modulation, feedback, and dry/wet levels.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack ('Jamaica Plains'). It has two branches. Branch 0 is the effect chain: Echo -> Compressor2. Branch 1 is named 'Dry' and contains only a mixer (volume). The macro controls are mapped to specific parameters in the Echo device.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Jamaica Plains
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Jamaica Plains"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_jamaica_plains.xml` (60,967 bytes).
