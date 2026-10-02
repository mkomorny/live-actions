---
title: Elephant Smile
category: time_based_spatial
subcategory: delay
id: time_based_spatial_elephant_smile
pages: 1
words: 157
source: ableton_dataset.jsonl
---
# Elephant Smile

## Sound Character & Overview
> **Layman Description:** Elephant Smile

> **Emotional Vibe:** Spacious, modulated, rhythmic, and slightly compressed 'wet' textures with a clean dry path.

## Technical Architecture & Signal Chain
Audio Effect Rack (Parallel Processing)

## Chain of Thought Sound Design Breakdown
The preset is an Audio Effect Rack named 'Elephant Smile'. It uses parallel processing with two branches: a main effect chain (Branch 0) and a completely dry bypass (Branch 1). The main chain consists of an Auto Filter, an Echo (with heavy modulation/ducking), and a Compressor. This setup is designed for rhythmic, modulated spatial effects that maintain the original transient integrity via the dry branch.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Elephant Smile
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Elephant Smile"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_elephant_smile.xml` (74,485 bytes).
