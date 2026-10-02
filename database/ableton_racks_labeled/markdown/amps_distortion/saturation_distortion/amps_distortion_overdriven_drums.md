---
title: Overdriven Drums
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_overdriven_drums
pages: 1
words: 220
source: ableton_dataset.jsonl
---
# Overdriven Drums

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack preset titled 'Overdriven Drums'. It is designed for drum bus processing, utilizing a single 'Wet' branch containing EQ, Overdrive, and Glue Compression. It features 8 macro controls and 5 distinct snapshots (Gentle, Punch, Overdriven, Even More, Smashed) to quickly transition between subtle tonal shaping and heavy, aggressive saturation/compression.

> **Emotional Vibe:** An aggressive, high-energy drum bus processor that can transform thin drums into a smashed, saturated powerhouse with just one knob turn.

## Technical Architecture & Signal Chain
Audio Effect Rack (AER) with a single 'Wet' branch. The signal chain consists of EQ Eight -> Overdrive -> Glue Compressor. The rack is highly optimized for drum bus processing via 8 macro mappings and 5 macro snapshots.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will first identify the macro structure, then dive into the 'Wet' branch to extract device parameters, and finally list the snapshots which define the preset's character variations.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Overdriven Drums
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Overdriven Drums"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_overdriven_drums.xml` (81,576 bytes).
