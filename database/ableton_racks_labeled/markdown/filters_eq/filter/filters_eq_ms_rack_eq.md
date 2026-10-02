---
title: MS Rack EQ
category: filters_eq
subcategory: filter
id: filters_eq_ms_rack_eq
pages: 1
words: 298
source: ableton_dataset.jsonl
---
# MS Rack EQ

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML to identify the device structure, effects used in each chain, macro mappings, and snapshot settings.

> **Emotional Vibe:** You are an elite mix engineer. Look at this MS Rack EQ preset. Tell me exactly how it's built—what chains are used, what the macros control, and how the Mid/Side processing is configured so I can recreate this professional workflow perfectly.

## Technical Architecture & Signal Chain
Perform a deep-structure analysis of the provided Ableton Audio Effect Rack XML. Extract the parallel branch architecture (Mid/Sides), the specific device parameters for Utility and EQ Eight within those branches, the Macro Control assignments, and the Snapshot parameter states.

## Chain of Thought Sound Design Breakdown
1. Identify Root: It is a 'GroupDevicePreset', specifically an Audio Effect Rack (indicated by branches). 
2. Analyze Macro Controls: Extract names and default values for all 8 visible macros.
3. Branch Analysis - Branch 0 ('Mid'):
    - Device 1: Utility (StereoGain). Mode: Mid/Side Balance (set to Mid). Parameters: Gain ~0dB, Width 1.
    - Device 2: EQ Eight. Note the band modes (High Pass, Low Pass, Notch) and frequencies used for filtering.
4. Branch Analysis - Branch 1 ('Sides'):
    - Device 1: Utility (StereoGain). Mode: Mid/Side Balance (set to Sides).
    - Device 2: EQ Eight. Note the band modes and frequency settings.
5. Snapshot Analysis: Identify 'Flat', 'Drum Buss Wide', 'Synth Bass Wide', and 'Guitars Wide' and their macro influences.
6. Synthesize into a structured report.

## Live Actions Blueprint
```python
# Live Actions device chain reference for MS Rack EQ
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "MS Rack EQ"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_ms_rack_eq.xml` (122,187 bytes).
