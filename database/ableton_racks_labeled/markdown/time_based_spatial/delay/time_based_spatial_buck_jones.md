---
title: Buck Jones
category: time_based_spatial
subcategory: delay
id: time_based_spatial_buck_jones
pages: 1
words: 236
source: ableton_dataset.jsonl
---
# Buck Jones

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Buck Jones' designed by Huston Singletary. It uses a parallel processing structure (two branches) to allow for dry/wet blending via the rack itself.

> **Emotional Vibe:** This is a highly textured, rhythmic effect rack. It combines heavy modulation (Auto Filter LFO), syncopated stereo delays (Echo with asymmetric left/right times), and subtle dynamics control (Compressor). The inclusion of 'Wobble' and 'Noise' in the Echo suggests it is designed for lo-fi, psychedelic, or experimental percussion/bass textures.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group Device utilizing two branches. Branch 0 contains the primary signal chain, while Branch 1 is a dedicated 'Dry' path. The rack features 8 active Macro controls and 3 user-defined snapshots.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack with two branches. Branch 0 contains a serial chain: Auto Filter -> Echo -> Compressor. Branch 1 is empty (Dry). The rack uses Macros to control specific parameters across these devices and includes three snapshots for different intensity levels of the effect.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Buck Jones
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Buck Jones"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_buck_jones.xml` (78,892 bytes).
