---
title: Knob 1 Super Looper
category: time_based_spatial
subcategory: delay
id: time_based_spatial_knob_1_super_looper
pages: 1
words: 234
source: ableton_dataset.jsonl
---
# Knob 1 Super Looper

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Knob 1 Super Looper'. It uses a parallel processing structure with two branches: a heavy effect chain called 'Luper' and a clean 'Dry' path. The rack is designed for rhythmic manipulation (looper/repeater style) using Beat Repeat, Auto Filter, EQ8, and Delay.

> **Emotional Vibe:** A rhythmic, glitchy looper rack that transforms audio into syncopated, filtered textures using heavy beat repetition and time-based effects.

## Technical Architecture & Signal Chain
Ableton Live 11 Audio Effect Rack: 'Knob 1 Super Looper'. Two-branch architecture. Branch 'Luper' contains a serial chain of Beat Repeat -> Auto Filter -> EQ8 -> Delay. Branch 'Dry' is a bypass/clean path. Macro 1 is mapped to 'Repeat'.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack with two branches. Branch 0 ('Luper') contains four devices: Beat Repeat, Auto Filter, EQ8, and Delay. Branch 1 ('Dry') is empty of effects (only mixer). I will extract the parameters for each device in the 'Luper' branch to provide a complete sound design profile.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Knob 1 Super Looper
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Knob 1 Super Looper"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_knob_1_super_looper.xml` (97,218 bytes).
