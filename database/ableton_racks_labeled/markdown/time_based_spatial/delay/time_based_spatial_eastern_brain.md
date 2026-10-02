---
title: Eastern Brain
category: time_based_spatial
subcategory: delay
id: time_based_spatial_eastern_brain
pages: 1
words: 255
source: ableton_dataset.jsonl
---
# Eastern Brain

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Eastern Brain' created by Huston Singletary. It uses a parallel processing structure (two branches) to allow for a dry/wet blend of a heavily processed signal.

> **Emotional Vibe:** A lush, evolving, and slightly gritty space-maker. It combines rhythmic delays with deep modulation and controlled saturation, perfect for creating 'Eastern Brain' style ambient textures that feel both massive and contained.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing two branches: Branch 0 contains a serial chain of Echo, Compressor, and Limiter, while Branch 1 is a clean 'Dry' path. This setup is designed for complex, modulated delay textures with heavy compression and limiting to control the output energy.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (GroupDevicePreset). I will analyze the branches first. Branch 0 is the effect branch; Branch 1 is the dry branch. Inside Branch 0, there is a device chain: Echo -> Compressor -> Limiter. I will then extract the specific parameter values for each of these devices and note the macro mappings provided in the XML header to understand how a user would interact with this preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Eastern Brain
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Eastern Brain"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_eastern_brain.xml` (70,166 bytes).
