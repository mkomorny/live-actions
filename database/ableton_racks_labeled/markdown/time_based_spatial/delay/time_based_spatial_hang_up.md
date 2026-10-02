---
title: Hang Up
category: time_based_spatial
subcategory: delay
id: time_based_spatial_hang_up
pages: 1
words: 256
source: ableton_dataset.jsonl
---
# Hang Up

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Hang Up', created by Sean Charles. It is a complex spatial/dub-style effect chain designed to add warmth, rhythmic movement, and filtered echoes to a signal.

> **Emotional Vibe:** A lush, vintage-style space effect that feels warm, rhythmic, and slightly unstable, perfect for adding depth and character to drums or melodic elements.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing a single processing branch (Wet) and one bypass branch (Dry). The wet chain utilizes a combination of filtering, saturation, multi-tap delay, and dynamic compression to create a modulated, dub-influenced texture.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It's an Audio Effect Rack ('Hang Up').
2. Analyze Macro Controls: 8 macros are mapped (Filter Cutoff, Filter Reso, Tube Warmth, Feed Back, Rack Dry/Wet, Rack Volume, and two unassigned).
3. Branch Analysis:
   - Branch 0 (Wet): Contains Auto Filter -> Dynamic Tube -> Echo (Dub Syndicate) -> Compressor (Gentle Squeeze).
   - Branch 1 (Dry): Empty mixer channel for dry/wet crossfading.
4. Parameter Extraction: Deep dive into each device in the wet chain to extract specific values for Cutoff, Resonance, Drive, Delay Times, Feedback, and Compression ratios.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Hang Up
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Hang Up"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_hang_up.xml` (80,528 bytes).
