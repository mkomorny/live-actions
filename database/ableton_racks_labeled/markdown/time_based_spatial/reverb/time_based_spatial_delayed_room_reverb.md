---
title: Delayed Room Reverb
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_delayed_room_reverb
pages: 1
words: 244
source: ableton_dataset.jsonl
---
# Delayed Room Reverb

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Delayed Room Reverb'. It uses a parallel branching structure to allow crossfading between a completely dry signal and a processed 'Wet' signal. The wet signal consists of a Simple Delay fed into a Reverb, creating a tempo-synced room response.

> **Emotional Vibe:** A lush, rhythmic space maker. Use the macros to transition from a tight, close room ('In the room') to a massive, ethereal wash ('Above the room') or a dark, submerged atmosphere ('Under the room').

## Technical Architecture & Signal Chain
An Audio Effect Rack utilizing two branches: a 'Dry' branch (direct pass-through) and a 'Wet' branch (Series chain: Simple Delay -> Reverb). The rack features 8 macro controls and 3 specific macro snapshots for spatial movement.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (GroupDevicePreset). It has two branches: 'Wet' and 'Dry'. The Wet branch contains a series of devices: Simple Delay followed by Reverb. The Dry branch is empty (direct signal). There are 8 macros mapped to specific parameters across the chain, and three macro snapshots defined for preset-like transitions.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Delayed Room Reverb
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Delayed Room Reverb"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_delayed_room_reverb.xml` (58,796 bytes).
