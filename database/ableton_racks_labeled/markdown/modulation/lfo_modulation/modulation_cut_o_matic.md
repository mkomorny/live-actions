---
title: Cut-o-matic
category: modulation
subcategory: lfo_modulation
id: modulation_cut_o_matic
pages: 1
words: 269
source: ableton_dataset.jsonl
---
# Cut-o-matic

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Cut-o-matic'. It uses a parallel processing structure with two branches: a 'Wet' branch containing a chain of effects (Auto Pan -> EQ Eight -> Limiter) and a 'Dry' branch which is empty. The rack is designed to create rhythmic gating effects using the Auto Pan device.

> **Emotional Vibe:** A rhythmic, chopping effect designed for cutting through a mix using precise LFO-driven gating and surgical EQ.

## Technical Architecture & Signal Chain
Audio Effect Rack: Cut-o-matic. Structure: Parallel (Wet/Dry). Wet Chain: [Auto Pan] -> [EQ Eight] -> [Limiter]. Macro Mapping: 8 active macros controlling Filter, AutoPan, and Rack levels.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevicePreset). 2. Analyze Branches: Branch 0 is 'Wet' (contains devices), Branch 1 is 'Dry' (empty). 3. Deconstruct Wet Chain: Device 0 = Auto Pan, Device 1 = EQ Eight, Device 2 = Limiter. 4. Extract Parameters for Auto Pan: LFO On, Freq ~1Hz, Rate Type=Beat, Beat Rate=6, Amount=Full. 5. Extract Parameters for EQ Eight: Global Gain -5.74dB, Scale 1.45, multiple bands active (including a boost at ~142Hz). 6. Extract Parameters for Limiter: On, Ceiling -0.3dB, Release 300ms, Lookahead 1ms. 7. Map Macros: Macro 0-7 mapped to Filter Freq, Amount, AutoPan Rate/Amount/Shape, Stereo Width, Dry/Wet, and Volume.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Cut-o-matic
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Cut-o-matic"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_cut_o_matic.xml` (76,802 bytes).
