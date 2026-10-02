---
title: Basic Twin Tremolo Guitar Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_twin_tremolo_guitar_amp
pages: 1
words: 213
source: ableton_dataset.jsonl
---
# Basic Twin Tremolo Guitar Amp

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Basic Twin Tremolo Guitar Amp'. It contains a single signal chain (the 'Wet' branch) designed for guitar processing, featuring amp simulation, pedal emulation, spring reverb, and dynamics control.

> **Emotional Vibe:** A lush, vintage-style guitar tone that balances gritty overdrive with shimmering spring reverb and rhythmic tremolo movement.

## Technical Architecture & Signal Chain
The preset is an Ableton Live Audio Effect Rack containing a serial chain of seven devices within the 'Wet' branch. It utilizes a complex macro mapping system (12 active macros) to control various parameters across the chain, including amp character, pedal drive, and reverb depth.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will trace the signal path through the 'Wet' branch, identifying each device and its specific parameter settings, then list the macro mappings which allow for global control of the preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Twin Tremolo Guitar Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Twin Tremolo Guitar Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_twin_tremolo_guitar_amp.xml` (95,519 bytes).
