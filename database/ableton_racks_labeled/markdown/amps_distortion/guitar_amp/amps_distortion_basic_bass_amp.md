---
title: Basic Bass Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_bass_amp
pages: 1
words: 149
source: ableton_dataset.jsonl
---
# Basic Bass Amp

## Sound Character & Overview
> **Layman Description:** Basic Bass Amp

> **Emotional Vibe:** A heavy, versatile bass tone engine with multiple character snapshots.

## Technical Architecture & Signal Chain
Audio Effect Rack (Group Device)

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack containing a serial chain of four devices: a Gate, Stereo Gain, Amp, and Cabinet. It includes extensive macro mapping and five distinct snapshots for different tonal characters (Crisp, Chest, Middle Earth, Chubby, Fat). The rack is designed to provide a complete bass amplification solution from input cleaning to cabinet simulation.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Bass Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Bass Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_bass_amp.xml` (56,576 bytes).
