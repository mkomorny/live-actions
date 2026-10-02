---
title: Thick Trick
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_thick_trick
pages: 1
words: 228
source: ableton_dataset.jsonl
---
# Thick Trick

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Thick Trick', created by Huston Singletary. It is structured as a single branch called 'Wet Signal' containing a heavy guitar processing chain.

> **Emotional Vibe:** This preset is designed for massive, thick, and saturated guitar tones. It combines heavy amp simulation with grit from a pedal, rhythmic movement from an echo, and controlled punch via a drum buss and limiter.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) utilizing a complex serial chain of devices within a specific branch ('Wet Signal'). The rack features 12 active Macro controls mapped to various amp, pedal, and delay parameters for real-time timbre shaping.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. The primary signal path is located within the 'Wet Signal' branch. I will trace the devices in order: Gate -> Pedal -> Amp -> Drum Buss -> Echo -> Cabinet -> Limiter. Then, I will extract the Macro mapping which provides the user-facing control interface.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Thick Trick
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Thick Trick"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_thick_trick.xml` (85,622 bytes).
