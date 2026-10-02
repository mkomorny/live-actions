---
title: Alien Ice Cream
category: time_based_spatial
subcategory: delay
id: time_based_spatial_alien_ice_cream
pages: 1
words: 226
source: ableton_dataset.jsonl
---
# Alien Ice Cream

## Sound Character & Overview
> **Layman Description:** This is an analysis of the Ableton Live preset 'Alien Ice Cream' created by Huston Singletary. It is a complex Audio Effect Rack (ADG) utilizing parallel processing (branches) and custom Max for Live devices to create highly modulated, rhythmic, and lo-fi textures.

> **Emotional Vibe:** This preset is designed to transform clean audio into 'alien' textures—think glitchy, bit-crushed, swirling, and rhythmic movement that feels otherworldly and unpredictable.

## Technical Architecture & Signal Chain
The XML describes an Audio Effect Group Device containing a single branch with three devices in series/parallel configuration. It features 4 user-defined Macro Controls and 4 distinct Macro Snapshots for dramatic timbre shifts.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (ADG). 2. Analyze Macros: 4 macros mapped to specific names. 3. Analyze Snapshots: 'Default', 'Alien Signals', 'Deep Space', 'Light Cycle'. 4. Deep Dive into Branch 0: Device 1 is a custom M4L Shaper; Device 2 is Redux (Bitcrusher); Device 3 is Phaser-Flanger. 5. Extract Parameter Values for each device.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Alien Ice Cream
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Alien Ice Cream"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_alien_ice_cream.xml` (70,612 bytes).
