---
title: Worn Out Vinyl Master
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_worn_out_vinyl_master
pages: 1
words: 235
source: ableton_dataset.jsonl
---
# Worn Out Vinyl Master

## Sound Character & Overview
> **Layman Description:** This is a mastering-style Audio Effect Rack named 'Worn Out Vinyl Master'. It is designed to emulate the character of a worn vinyl record by combining surgical EQ, vinyl surface noise (crackle/dust), tube saturation, and final peak limiting.

> **Emotional Vibe:** A nostalgic, dusty, and warm 'Worn Out Vinyl' mastering chain that can transform clean digital audio into a lo-fi, crackly, and vintage record playback experience.

## Technical Architecture & Signal Chain
An Ableton Live Audio Effect Rack containing a single 'Wet' branch. The signal chain consists of an EQ Eight for tonal shaping, a Vinyl emulator for texture, a Tube saturator for harmonic enhancement, and a Limiter for peak control. It includes 8 user-mapped macro controls and 5 custom snapshots for rapid character changes.

## Chain of Thought Sound Design Breakdown
The XML represents an Audio Effect Rack. I will trace the signal path through the 'Wet' branch: EQ Eight -> Vinyl -> Tube -> Limiter. Then, I will extract macro mappings and snapshot data to provide a complete overview of the preset's functionality.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Worn Out Vinyl Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Worn Out Vinyl Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_worn_out_vinyl_master.xml` (84,214 bytes).
