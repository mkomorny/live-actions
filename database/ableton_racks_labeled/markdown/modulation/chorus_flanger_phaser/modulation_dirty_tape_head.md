---
title: Dirty Tape Head
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_dirty_tape_head
pages: 1
words: 232
source: ableton_dataset.jsonl
---
# Dirty Tape Head

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML preset.

> **Emotional Vibe:** Act as an expert sound designer. Break down this 'Dirty Tape Head' rack so I can recreate it perfectly.

## Technical Architecture & Signal Chain
Identify all devices, their signal chain order, and specific parameter values from the provided XML structure.

## Chain of Thought Sound Design Breakdown
1. Identify the root device: It is an Audio Effect Rack (AudioEffectGroupDevice) named 'Dirty Tape Head'.
2. Trace the signal chain within the branch: The devices are contained in a single branch and follow a serial path.
3. Device 1 Analysis: A Max for Live device ('Shaper.amxd') with specific parameters like Depth, Rate, Grid Size, etc.
4. Device 2 Analysis: Ableton's 'Redux' bitcrusher. Note the Bit Depth (6) and Dry/Wet settings.
5. Device 3 Analysis: Ableton's 'Phaser-Flanger'. Note it is in Phaser mode with specific feedback and center frequency.
6. Parameter Extraction: Extract 'Manual' values which represent the actual preset state, rather than 'Default' values.
7. Final Synthesis: Organize into a clear, professional report for an audio engineer.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dirty Tape Head
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dirty Tape Head"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_dirty_tape_head.xml` (70,142 bytes).
