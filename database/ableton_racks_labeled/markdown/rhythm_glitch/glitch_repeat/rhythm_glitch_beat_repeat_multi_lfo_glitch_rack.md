---
title: Beat Repeat Multi-LFO Glitch Rack
category: rhythm_glitch
subcategory: glitch_repeat
id: rhythm_glitch_beat_repeat_multi_lfo_glitch_rack
pages: 1
words: 233
source: ableton_dataset.jsonl
---
# Beat Repeat Multi-LFO Glitch Rack

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack preset containing a Beat Repeat in the main chain and a nested rack within a branch that contains four identical LFO devices.

> **Emotional Vibe:** This preset is designed for rhythmic chaos and complex, evolving textures, combining heavy beat repetition with a multi-layered, randomized LFO modulation engine.

## Technical Architecture & Signal Chain
The XML defines a Group Device Preset (Audio Effect Rack) with one primary device in the signal path and one parallel/branch path. The branch contains a nested Audio Effect Group containing four instances of the LFO device, all configured with identical parameters for randomized modulation.

## Chain of Thought Sound Design Breakdown
1. Identified root as GroupDevicePreset (Effect Rack).
2. Analyzed Main Chain: Found Beat Repeat (AbletonDevicePreset Id=1).
3. Analyzed Branches: Found one branch (AudioEffectBranchPreset Id=0).
4. Analyzed Branch 0: Contains a nested AudioEffectGroupDevice.
5. Analyzed Nested Group: Found four LFO devices (MxDeviceAudioEffect) with identical parameter settings.
6. Extracted all specific parameter values for Beat Repeat and LFOs via 'Manual' value tags.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Beat Repeat Multi-LFO Glitch Rack
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Beat Repeat Multi-LFO Glitch Rack"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/rhythm_glitch_beat_repeat_multi_lfo_glitch_rack.xml` (136,618 bytes).
