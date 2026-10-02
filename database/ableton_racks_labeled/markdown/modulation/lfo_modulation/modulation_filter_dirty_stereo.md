---
title: Filter Dirty Stereo
category: modulation
subcategory: lfo_modulation
id: modulation_filter_dirty_stereo
pages: 1
words: 281
source: ableton_dataset.jsonl
---
# Filter Dirty Stereo

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Filter Dirty Stereo'. It uses a parallel processing structure with three branches: Left, Right, and Dry. The core of the sound comes from two Auto Filters (one per side) that are slightly out of phase/sync to create a wide, moving stereo effect, blended with a completely dry signal.

> **Emotional Vibe:** A wide, swirling, and slightly gritty stereo filter effect. It feels immersive and movement-heavy due to the dual-filter LFO offset, perfect for adding texture to rhythmic elements without losing the original punch via the dry path.

## Technical Architecture & Signal Chain
Analyze the following Ableton Audio Effect Rack structure: A 3-branch parallel chain. Branch 'Left' contains an Auto Filter (Cutoff ~75Hz, Res ~0.64, Drive ~3.4dB, LFO Freq ~0.44Hz) followed by a Utility (Stereo Gain). Branch 'Right' contains an identical Auto Filter but with a different LFO frequency (~0.16Hz) and inverted ModHub (-49.8), followed by a Utility. Branch 'Dry' is a pass-through. The rack features 8 macros including Cutoff, Resonance, Spacing, Drive, and Stereo Width/Dry-Wet controls.

## Chain of Thought Sound Design Breakdown
The user wants a deep dive into an Ableton XML preset. I need to parse this specifically as a sound designer would: looking at the device chain, the macro mapping, and the specific parameter values that define the 'character' of the preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filter Dirty Stereo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filter Dirty Stereo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_filter_dirty_stereo.xml` (81,522 bytes).
