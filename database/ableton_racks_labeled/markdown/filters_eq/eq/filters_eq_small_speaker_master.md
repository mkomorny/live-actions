---
title: Small Speaker Master
category: filters_eq
subcategory: eq
id: filters_eq_small_speaker_master
pages: 1
words: 246
source: ableton_dataset.jsonl
---
# Small Speaker Master

## Sound Character & Overview
> **Layman Description:** This is a mastering chain preset titled 'Small Speaker Master'. It is designed to compensate for the frequency response limitations of small speakers by providing macro-controlled boosts in the bass, mid, and high frequencies, alongside controlled compression and limiting.

> **Emotional Vibe:** This preset feels like a 'rescue' tool—it's designed to bring life, weight, and clarity back to a mix that sounds thin or small, giving it a sense of 'Air' and 'Presence' through highly controlled macro movements.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group (ADG) containing a single branch named 'Wet'. The signal chain consists of EQ Eight, Glue Compressor, and Limiter. It utilizes 8 macro controls to map specific parameters across the chain and includes five distinct macro snapshots for rapid tonal and dynamic shifts.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Group ('Small Speaker Master'). 2. Identify Branch: 'Wet'. 3. Analyze Device Chain in 'Wet': EQ Eight -> Glue Compressor -> Limiter. 4. Extract Parameters for each device. 5. Map Macro Controls (Macros 0-7). 6. Analyze Snapshots (Flat, Light Comp, Heavy Comp, Presence, Air).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Small Speaker Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Small Speaker Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_small_speaker_master.xml` (81,266 bytes).
