---
title: Punchy Dance Master
category: dynamics_mastering
subcategory: mastering
id: dynamics_mastering_punchy_dance_master
pages: 1
words: 144
source: ableton_dataset.jsonl
---
# Punchy Dance Master

## Sound Character & Overview
> **Layman Description:** Expert Ableton Live Sound Designer & Audio Engineer Analysis

> **Emotional Vibe:** Professional/Analytical

## Technical Architecture & Signal Chain
XML Parsing and Parameter Extraction

## Chain of Thought Sound Design Breakdown
The user provided an Ableton XML preset for a Group Device (Audio Effect Group). My goal is to deconstruct the signal chain, identify every device used within the 'Wet' branch, extract their specific parameter values, and map the Macro controls which are essential for the user to recreate or understand the movement of this preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Punchy Dance Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Punchy Dance Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/dynamics_mastering_punchy_dance_master.xml` (81,207 bytes).
