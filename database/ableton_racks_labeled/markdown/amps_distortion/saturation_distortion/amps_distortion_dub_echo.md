---
title: Dub Echo
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_dub_echo
pages: 1
words: 236
source: ableton_dataset.jsonl
---
# Dub Echo

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Dub Echo' designed for heavy, modulated delay effects with saturation and spatial movement.

> **Emotional Vibe:** This sound is thick, swirling, and psychedelic—perfect for dub reggae or lo-fi hip hop textures where the echoes feel like they are breathing and moving through space.

## Technical Architecture & Signal Chain
The preset is a parallel processing rack containing two branches. Branch 0 (Wet) contains a serial chain of Chorus, Saturator, Echo, and Auto Pan. Branch 1 (Dry) is a direct pass-through.

## Chain of Thought Sound Design Breakdown
1. Identify Rack Type: Audio Effect Rack (GroupDevicePreset).
2. Analyze Branches: Branch 0 is the effect chain; Branch 1 is named 'Dry' and contains no devices (direct signal).
3. Map Macros: Extracting MacroDisplayNames and their current Manual values.
4. Deconstruct Branch 0 (Serial Chain):
   - Device 1: Chorus (Modulation/Width)
   - Device 2: Saturator (Harmonic Distortion)
   - Device 3: Echo (Time-based effect/Feedback/Filter)
   - Device 4: Auto Pan (Stereo movement)
5. Extract Parameters: Deep dive into the XML for specific values of Delay, Feedback, Filter, and LFO settings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dub Echo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dub Echo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_dub_echo.xml` (78,103 bytes).
