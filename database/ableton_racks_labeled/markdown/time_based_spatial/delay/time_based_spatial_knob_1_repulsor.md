---
title: Knob 1 RePulsor
category: time_based_spatial
subcategory: delay
id: time_based_spatial_knob_1_repulsor
pages: 1
words: 200
source: ableton_dataset.jsonl
---
# Knob 1 RePulsor

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Knob 1 RePulsor'. It uses a three-branch system (Dry, Force, and Pump) to allow for smooth transitions between a clean signal and two different rhythmic/spatial processing states.

> **Emotional Vibe:** A rhythmic, pulsing texture generator that can morph from a clean signal into a swirling, delayed 'Force' or a heavy, pumping 'Pump' effect with just one knob.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing Parallel Branching. It features highly synchronized Auto Pan and Delay chains across its active branches, controlled via 8 mapped Macro Controls.

## Chain of Thought Sound Design Breakdown
The XML defines an Audio Effect Rack. I will break this down by its Macro Controls and then by its three distinct branches (Dry, Force, Pump) to show exactly what is happening in each signal path.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Knob 1 RePulsor
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Knob 1 RePulsor"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_knob_1_repulsor.xml` (69,203 bytes).
