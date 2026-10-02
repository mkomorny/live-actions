---
title: Scream Dream
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_scream_dream
pages: 1
words: 201
source: ableton_dataset.jsonl
---
# Scream Dream

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Scream Dream' created by Huston Singletary. It uses a single branch called 'Wet Signal' which contains a complex chain of guitar-style processing: Gate -> Pedal -> Echo -> Amp -> Cabinet.

> **Emotional Vibe:** This preset feels massive and cinematic. It’s designed for huge, swelling guitar textures or synth pads that bloom with distortion and space.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (AER) utilizing a specific signal path within the 'Wet Signal' branch. The routing follows a non-traditional order where delay/echo precedes the amp stage, creating a highly saturated, ambient wash effect.

## Chain of Thought Sound Design Breakdown
1. Identify Rack Name/Creator -> 2. Map Macro Controls (Crucial for AER) -> 3. Trace Signal Path in 'Wet Signal' branch -> 4. Extract individual device parameters -> 5. Analyze Mixer settings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Scream Dream
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Scream Dream"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_scream_dream.xml` (72,363 bytes).
