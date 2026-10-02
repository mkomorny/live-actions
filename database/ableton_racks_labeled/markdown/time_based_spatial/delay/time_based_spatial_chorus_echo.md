---
title: Chorus Echo
category: time_based_spatial
subcategory: delay
id: time_based_spatial_chorus_echo
pages: 1
words: 212
source: ableton_dataset.jsonl
---
# Chorus Echo

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack preset named 'Chorus Echo' created by Michele Darling. It uses a parallel processing structure (two branches) to allow crossfading between a heavily processed signal and a clean 'Dry' signal.

> **Emotional Vibe:** A lush, spacey, and slightly gritty ambient effect that can transition from clean to a 'wailing' or 'trashcan' textured sound using the macro controls.

## Technical Architecture & Signal Chain
Audio Effect Rack with two branches. Branch 0 contains a serial chain of Chorus, Pedal, Echo, and Limiter. Branch 1 is a dry pass. The rack features 8 macro controls and 4 custom snapshots.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack (GroupDevicePreset). The structure uses 'Branches'. Branch 0 is the main effect chain. Branch 1 is named 'Dry' and contains no effects, only a mixer, meaning it serves as a clean bypass. I will now detail the devices in Branch 0.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Chorus Echo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Chorus Echo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_chorus_echo.xml` (72,624 bytes).
