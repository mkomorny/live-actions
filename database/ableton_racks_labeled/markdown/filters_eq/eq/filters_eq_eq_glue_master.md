---
title: EQ & Glue Master
category: filters_eq
subcategory: eq
id: filters_eq_eq_glue_master
pages: 1
words: 305
source: ableton_dataset.jsonl
---
# EQ & Glue Master

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'EQ & Glue Master'. It is designed as a parallel processing unit with two main branches: a 'Dry' branch (containing EQ and Compression) and a 'Wet' branch. It uses a Chain Selector to toggle between them, controlled by Macro 6.

> **Emotional Vibe:** This is a professional-grade mastering/mixing tool that gives you surgical control over your low-end and high-end clarity, while allowing you to 'glue' your mix together with a single macro. It’s perfect for adding instant polish or aggressive brightness without losing the punch of your original signal.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing a Chain Selector for Dry/Wet parallel processing. The signal path in the primary branch consists of an EQ Eight followed by a Glue Compressor. The rack features complex macro mapping for tonal shaping and dynamic control, including several snapshots for quick tonal shifts (Low End Boost, Bright, Brighter, Full and Compressed).

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack ('EQ & Glue Master'). The structure uses 'Branches'. Branch 0 is named 'Dry' and contains two devices: EQ Eight and Glue Compressor. Branch 1 is named 'Wet' and only contains a mixer device. A Chain Selector (controlled by Macro 6) determines the balance between these branches. I will now detail the specific parameters of each device found in the Dry branch and the macro mappings provided in the rack header.

## Live Actions Blueprint
```python
# Live Actions device chain reference for EQ & Glue Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "EQ & Glue Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_eq_glue_master.xml` (81,204 bytes).
