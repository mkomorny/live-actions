---
title: Ghostly Swirls
category: time_based_spatial
subcategory: delay
id: time_based_spatial_ghostly_swirls
pages: 1
words: 272
source: ableton_dataset.jsonl
---
# Ghostly Swirls

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML to identify all devices, their parameters, and the overall sound design intent.

> **Emotional Vibe:** You are a master sound designer. Look at this code and tell me exactly what kind of 'Ghostly Swirls' these settings create. What is the vibe? How is it built?

## Technical Architecture & Signal Chain
Perform a deep-dive structural analysis of the provided Ableton Live XML preset. Extract the device chain, specific parameter values (including LFO/Modulation settings), macro mappings, and snapshot configurations.

## Chain of Thought Sound Design Breakdown
1. Identify Root: It's an Audio Effect Rack (GroupDevicePreset) named 'Ghostly Swirls'.
2. Analyze Macro Controls: 8 macros are mapped to specific parameters (Filter Cutoff, Reso, Pan, Echo FB, etc.).
3. Trace Branch 0 (Wet Chain):
   - Device 1: Auto Filter (Circuit LpHp mode, LFO active at ~0.11Hz).
   - Device 2: Echo (Asymmetric delay times, Feedback Inverted, Ducking ON, Wobble ON, Stereo Width MAX).
   - Device 3: Auto Pan (LFO active, Phase 180°).
   - Device 4: Compressor2 (Gentle Squeeze style, low threshold).
4. Trace Branch 1 (Dry Chain): Pure dry pass-through.
5. Analyze Snapshots: 'Crawl Under', 'Ultrawide', and 'Kicks Only' provide different movement/filtering states.
6. Synthesize Sound Design: The combination of asymmetric delays, inverted feedback, slow filter sweeps, and wobbling creates a complex, evolving, psychedelic spatial texture.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Ghostly Swirls
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Ghostly Swirls"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_ghostly_swirls.xml` (87,077 bytes).
