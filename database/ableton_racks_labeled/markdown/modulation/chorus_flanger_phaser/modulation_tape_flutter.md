---
title: Tape Flutter
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_tape_flutter
pages: 1
words: 251
source: ableton_dataset.jsonl
---
# Tape Flutter

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Tape Flutter' created by Huston Singletary. It uses a combination of a Shaper (Max for Live) and a Phaser-Flanger to create rhythmic, tape-like modulation effects.

> **Emotional Vibe:** A vintage, unstable, and rhythmic tape-saturation style effect. It provides 'flutter' through synchronized frequency shaping and phase-based doubling, perfect for lo-fi textures and psychedelic movement.

## Technical Architecture & Signal Chain
An Ableton Audio Effect Rack (.adg) containing a single branch with two devices in series: a 'Shaper' M4L device and a 'Phaser-Flanger'. The rack features 6 mapped macro controls for real-time modulation of the chain.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (GroupDevicePreset). I will break this down into the Macro mapping first, then analyze the device chain within the active branch. The rack contains one branch (Id 0) which houses two devices: a 'Shaper' and a 'Phaser-Flanger'. Each device has specific parameter values that define its character (e.g., the Shaper is set to a 1/4 note sync rate, and the Phaser is in Flanger mode). Finally, I will list the macro controls which act as the user interface for this preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Tape Flutter
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Tape Flutter"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_tape_flutter.xml` (65,278 bytes).
