---
title: Thinn
category: filters_eq
subcategory: filter
id: filters_eq_thinn
pages: 1
words: 269
source: ableton_dataset.jsonl
---
# Thinn

## Sound Character & Overview
> **Layman Description:** This is an analysis of the Ableton Live Audio Effect Rack preset named 'Thinn'. It is designed to shape the frequency response and stereo width of an audio signal, likely used for thinning out a sound by cutting lows and highs while narrowing the stereo field.

> **Emotional Vibe:** This preset feels surgical and corrective. It's built to strip away weight and width, making it perfect for cleaning up muddy low-end or creating a 'distant' and narrow mono-ish effect.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) containing a single device chain. The signal path consists of an EQ Eight followed by a Utility device (specifically utilizing the Stereo Gain section).

## Chain of Thought Sound Design Breakdown
1. Identify the root: An Audio Effect Rack named 'Thinn'.
2. Identify the branch: A single active branch containing two devices.
3. Device 1 Analysis (EQ Eight): Examine all 8 bands. Note that EQ Eight uses ParameterA and ParameterB for its dual-mode capability per band. Filter out inactive bands to find the actual sonic footprint.
4. Device 2 Analysis (Utility/Stereo Gain): Identify specific settings like Stereo Width and Gain.
5. Synthesize: Combine findings into a coherent technical summary of how this rack processes audio (Low cut, High cut, and Stereo narrowing).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Thinn
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Thinn"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_thinn.xml` (64,010 bytes).
