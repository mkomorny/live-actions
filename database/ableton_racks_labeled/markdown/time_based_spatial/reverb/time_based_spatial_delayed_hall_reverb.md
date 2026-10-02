---
title: Delayed Hall Reverb
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_delayed_hall_reverb
pages: 1
words: 254
source: ableton_dataset.jsonl
---
# Delayed Hall Reverb

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack named 'Delayed Hall Reverb'. It uses parallel processing (two branches) to create a wide, thick spatial effect. Each branch contains a Ping Pong Delay, a Utility device for mid-side/gain control, and a heavy Reverb. The entire rack is controlled via 8 macros.

> **Emotional Vibe:** A massive, lush, and cinematic space maker. It feels huge, wide, and slightly dark due to the filtered delays, perfect for creating 'walls of sound' or ethereal textures.

## Technical Architecture & Signal Chain
Audio Effect Rack with two parallel branches (L and R). Signal flow per branch: Ping Pong Delay -> StereoGain (Utility) -> Reverb. Macro controls are mapped to damping, width, decay, feedback, time, dry/wet, and master volume.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevicePreset). 2. Analyze Branches: Two branches found (L and R). 3. Deconstruct Branch L/R: Both contain a Delay (Ping Pong), StereoGain (Utility), and Reverb. 4. Extract Parameters: Delay time (~375ms), Feedback (~36%), Filter (~555Hz), Reverb Decay (3s), Pre-delay (30ms). 5. Map Macros: 8 macros mapped to specific reverb/delay parameters. 6. Identify Snapshots: 'In A Trance', 'Big House', 'Tiny House', 'Feedback Shine'.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Delayed Hall Reverb
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Delayed Hall Reverb"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_delayed_hall_reverb.xml` (105,681 bytes).
