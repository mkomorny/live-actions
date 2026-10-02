---
title: Ample Space Delay
category: time_based_spatial
subcategory: delay
id: time_based_spatial_ample_space_delay
pages: 1
words: 216
source: ableton_dataset.jsonl
---
# Ample Space Delay

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Ample Space Delay'. It is designed for subtle stereo enhancement and filtered delay effects, utilizing three distinct branches: a chorused panning branch, a flanged ping-pong delay branch, and a pure dry branch.

> **Emotional Vibe:** Create a lush, wide, and swirling soundscape that feels like it's breathing. Use rhythmic delays and chorusing to add depth without washing out the original signal.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (AER) containing 8 macro controls and 3 parallel processing branches. It uses complex modulation via Auto Pan, Chorus, Ping Pong Delay, and Flanger to create wide, moving textures.

## Chain of Thought Sound Design Breakdown
The user wants an analysis of an Ableton XML preset. I must identify: 1. The overall structure (Audio Effect Rack). 2. Macro controls (names and values). 3. Each branch's contents (devices and parameters). 4. The specific settings for each device.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Ample Space Delay
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Ample Space Delay"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_ample_space_delay.xml` (72,583 bytes).
