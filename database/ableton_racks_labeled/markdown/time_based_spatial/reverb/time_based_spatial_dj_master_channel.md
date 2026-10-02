---
title: DJ Master Channel
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_dj_master_channel
pages: 1
words: 234
source: ableton_dataset.jsonl
---
# DJ Master Channel

## Sound Character & Overview
> **Layman Description:** This is a 'DJ Master Channel' Audio Effect Rack designed for live performance, featuring two main chains: a 'Wet' processing chain and a 'Dry' bypass chain. It uses Macro controls to allow a DJ to quickly sweep filters, adjust EQ, control reverb, and transition between different energy levels via snapshots.

> **Emotional Vibe:** This toolkit feels professional and high-energy, built for a DJ who needs instant control over the 'vibe' of a track—moving from clean/dry to lush/filtered/reverberated with single-knob sweeps.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group (Rack) containing two branches: 'Wet' and 'Dry'. The Wet branch contains an Auto Filter, Reverb, and EQ Three. The Dry branch is a clean pass-through. Macro controls are mapped to specific parameters across these devices to facilitate rapid tonal shaping.

## Chain of Thought Sound Design Breakdown
The XML structure reveals an Audio Effect Rack. I will first identify the Macro controls (the user interface), then dissect the device chains (Wet vs Dry), and finally detail the specific parameter settings for each device.

## Live Actions Blueprint
```python
# Live Actions device chain reference for DJ Master Channel
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "DJ Master Channel"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_dj_master_channel.xml` (66,120 bytes).
