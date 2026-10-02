---
title: Drumolish Squeeze
category: modulation
subcategory: lfo_modulation
id: modulation_drumolish_squeeze
pages: 1
words: 271
source: ableton_dataset.jsonl
---
# Drumolish Squeeze

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Group (.adg) titled 'Drumolish Squeeze', designed by Huston Singletary. It is a rhythmic and modulation-heavy processing chain, likely intended for drums, utilizing a series of lo-fi, gating, and movement effects.

> **Emotional Vibe:** A gritty, glitchy, and highly rhythmic drum processor that can transform clean percussion into broken, lo-fi, and swirling textures with a single knob turn.

## Technical Architecture & Signal Chain
The preset utilizes an Audio Effect Group with a single branch containing a serial signal chain: Shaper (Max for Live) -> Erosion -> Redux -> Phaser-Flanger. It features 6 macro controls and several specialized snapshots for rapid timbre changes.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It's an AudioEffectGroupDevice (an .adg file). 2. Analyze Macros: There are 6 macros defined (LFO Offset, Little Bits, Erode, Low Grade, Phase, Macro 6). 3. Analyze Branches: One branch is active containing a serial chain of four devices. 4. Device 1 (Shaper): A Max for Live device with specific rhythmic parameters like Grid Size and Sync Rate. 5. Device 2 (Erosion): Native Ableton effect used for bit-crushing/noise. 6. Device 3 (Redux): Native lo-fi bit-crusher. 7. Device 4 (Phaser-Flanger): Native modulation effect for movement. 8. Extract all parameter values from the XML tags (<MxDFloatParameter>, <Erosion>, <Redux2>, etc.).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Drumolish Squeeze
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Drumolish Squeeze"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_drumolish_squeeze.xml` (78,023 bytes).
