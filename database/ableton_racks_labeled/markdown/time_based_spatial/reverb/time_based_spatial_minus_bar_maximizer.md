---
title: Minus Bar Maximizer
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_minus_bar_maximizer
pages: 1
words: 226
source: ableton_dataset.jsonl
---
# Minus Bar Maximizer

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML preset to identify its structure, devices, and settings.

> **Emotional Vibe:** You are an expert mastering engineer. Look at this preset code and tell me exactly what kind of sonic character it has by analyzing its internal settings and signal chain.

## Technical Architecture & Signal Chain
Perform a deep-dive analysis of this Ableton Live Audio Effect Group (.adg) XML. Extract the macro mapping, the device chain within the 'Wet' branch, and all specific parameter values for each device.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It is a Group Device (Audio Effect Group) named 'Minus Bar Maximizer'.
2. Analyze Macros: Extract the 8 user-facing macro controls.
3. Navigate to Branches: The processing is contained within an AudioEffectBranchPreset named 'Wet'.
4. Iterate through Devices in 'Wet' branch:
   a. Drum Buss (Custom/Preset based)
   b. EQ Eight
   c. Reverb
   d. Compressor2
   e. Limiter
5. Extract parameters for each device: Frequencies, Gains, Ratios, Times, etc.
6. Synthesize the findings into a structured report.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Minus Bar Maximizer
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Minus Bar Maximizer"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_minus_bar_maximizer.xml` (106,521 bytes).
