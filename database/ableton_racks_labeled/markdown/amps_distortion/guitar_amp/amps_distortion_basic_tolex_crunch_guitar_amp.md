---
title: Basic Tolex Crunch Guitar Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_tolex_crunch_guitar_amp
pages: 1
words: 232
source: ableton_dataset.jsonl
---
# Basic Tolex Crunch Guitar Amp

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack titled 'Basic Tolex Crunch Guitar Amp' created by Huston Singletary. It is designed as a guitar signal chain, utilizing a single branch named 'Wet Signal'.

> **Emotional Vibe:** This preset offers a powerful, crunchy guitar tone with highly tactile control over everything from the initial gate snap to the final cabinet resonance, allowing you to transition from clean-ish rhythms to aggressive, breaking fuzz.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (AER) containing a complex serial signal chain within the 'Wet Signal' branch. The rack features 12 mapped macro controls for real-time manipulation of amp and pedal parameters.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will first extract the Macro mappings, then traverse the 'Wet Signal' branch to identify each device and its specific parameter values in order of signal flow (Gate -> Pedal -> Drum Buss -> Amp -> Cabinet). Finally, I will note the Mixer settings for that branch.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Tolex Crunch Guitar Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Tolex Crunch Guitar Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_tolex_crunch_guitar_amp.xml` (62,796 bytes).
