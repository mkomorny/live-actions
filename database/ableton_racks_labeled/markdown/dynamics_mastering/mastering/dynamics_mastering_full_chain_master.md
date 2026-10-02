---
title: Full Chain Master
category: dynamics_mastering
subcategory: mastering
id: dynamics_mastering_full_chain_master
pages: 1
words: 140
source: ableton_dataset.jsonl
---
# Full Chain Master

## Sound Character & Overview
> **Layman Description:** Analyze Ableton XML

> **Emotional Vibe:** Precise, professional, and highly detailed

## Technical Architecture & Signal Chain
Expert Sound Designer/Engineer Analysis

## Chain of Thought Sound Design Breakdown
The provided XML is an Audio Effect Rack (AER) preset titled 'Full Chain Master'. It contains a single branch named 'Wet' which houses a serial processing chain for mastering. I will extract the Macro mappings first, then traverse the device chain within the 'Wet' branch to identify every device and its specific parameter settings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Full Chain Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Full Chain Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/dynamics_mastering_full_chain_master.xml` (98,189 bytes).
