---
title: Dirty Bounce
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_dirty_bounce
pages: 1
words: 140
source: ableton_dataset.jsonl
---
# Dirty Bounce

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Dirty Bounce' designed for drum processing (tube warming, subtle delay, and compression).

> **Emotional Vibe:** A heavy, saturated, and compressed drum bus processor.

## Technical Architecture & Signal Chain
Analysis of Ableton XML Preset: Dirty Bounce

## Chain of Thought Sound Design Breakdown
The preset is an Audio Effect Rack with two branches (Wet/Dry). The Wet branch contains a complex serial chain of Delay, Saturator, Tube, and Compressor. It uses 8 Macro controls to blend these effects.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dirty Bounce
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dirty Bounce"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_dirty_bounce.xml` (71,723 bytes).
