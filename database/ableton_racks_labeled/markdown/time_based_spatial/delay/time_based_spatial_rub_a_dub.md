---
title: Rub A Dub
category: time_based_spatial
subcategory: delay
id: time_based_spatial_rub_a_dub
pages: 1
words: 229
source: ableton_dataset.jsonl
---
# Rub A Dub

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Rub A Dub' designed for dub-style spatial effects. It uses a parallel processing structure (two branches) to allow for a dry/wet blend. The main effect chain consists of an Auto Filter, an Echo, and a Compressor, creating a rhythmic, filtered, and ducked delay sound.

> **Emotional Vibe:** A deep, rhythmic, and hypnotic dub delay effect that breathes with movement and provides lush, filtered space.

## Technical Architecture & Signal Chain
Audio Effect Rack with two branches. Branch 0 contains the processing chain (Auto Filter -> Echo -> Compressor). Branch 1 is a dry path. The rack utilizes macro controls for real-time modulation of filter, resonance, wobble, feedback, and volume.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack ('Rub A Dub'). It has two branches: Branch 0 (the main effect chain) and Branch 1 (named 'Dry'). The processing chain in Branch 0 is: Auto Filter -> Echo -> Compressor. I will now extract the specific parameters for each device.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Rub A Dub
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Rub A Dub"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_rub_a_dub.xml` (74,306 bytes).
