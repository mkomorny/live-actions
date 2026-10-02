---
title: Filter Driver
category: filters_eq
subcategory: filter
id: filters_eq_filter_driver
pages: 1
words: 219
source: ableton_dataset.jsonl
---
# Filter Driver

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Filter Driver'. It is designed as a parallel processing unit with two branches: a 'Wet' branch containing a filter and limiter chain, and a 'Dry' branch which acts as a clean pass-through.

> **Emotional Vibe:** A high-performance DJ-style filter rack. The 'Wet' chain provides a saturated, limited filter effect, while the 'Dry' chain ensures the original signal remains intact for parallel blending.

## Technical Architecture & Signal Chain
The preset is an Ableton Audio Effect Rack (ADG) utilizing a dual-branch architecture for parallel processing. It features macro-mapped controls for real-time performance/DJing, specifically targeting filter frequency, resonance, drive, and dry/wet balance.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack ('Filter Driver'). I will break this down by its two branches: 'Wet' and 'Dry'. For each branch, I will identify the device chain and their specific parameter settings. Finally, I will list the Macro controls which are mapped to the user interface.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filter Driver
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filter Driver"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_filter_driver.xml` (59,551 bytes).
