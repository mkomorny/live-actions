---
title: Warm & Wide Drums
category: filters_eq
subcategory: eq
id: filters_eq_warm_wide_drums
pages: 1
words: 209
source: ableton_dataset.jsonl
---
# Warm & Wide Drums

## Sound Character & Overview
> **Layman Description:** This is a professional Drum Mix Buss preset titled 'Warm & Wide Drums'. It uses an Audio Effect Group to allow for parallel processing (Branches). The design focuses on tonal shaping (Bass/Mid/High), stereo widening, and glue compression, all controlled via 8 macro knobs.

> **Emotional Vibe:** A powerful, polished drum bus processor designed to add weight, width, and cohesive 'glue' to drum transients while maintaining clarity.

## Technical Architecture & Signal Chain
Analysis of Ableton XML: Audio Effect Group with Parallel Branching. Macro-mapped architecture for tonal balance and dynamic control.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Group (ADG). 2. Analyze Macros: Mapping of user-facing controls. 3. Analyze Snapshots: Preset states within the macro system. 4. Analyze Branches: The 'Wet' branch contains a specific serial chain of EQ, Utility, and Glue Compressor. 5. Extract Parameters: Precise values for every device in the wet path.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Warm & Wide Drums
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Warm & Wide Drums"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_warm_wide_drums.xml` (92,093 bytes).
