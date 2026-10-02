---
title: Module Later
category: time_based_spatial
subcategory: delay
id: time_based_spatial_module_later
pages: 1
words: 216
source: ableton_dataset.jsonl
---
# Module Later

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack preset named 'Module Later'. It uses a branching structure to switch between a completely dry signal, a heavy Phaser-based modulation chain, and a lush Chorus-based modulation chain.

> **Emotional Vibe:** This preset is a powerful performance tool designed to transform a sound from clean and dry into a swirling, psychedelic, or 'stunned' texture with just a single knob turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group (Rack) utilizing multiple branches. It features complex macro mapping across two primary effect chains: one focused on high-feedback phasing and another on multi-tap chorus/delay modulation. It includes three distinct snapshots for rapid parameter interpolation.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will break it down by its Branches (Dry, Phasor, Chorus), identify the devices within those branches, extract their specific parameter settings, and then map out the Macro Controls and Snapshots provided.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Module Later
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Module Later"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_module_later.xml` (96,340 bytes).
