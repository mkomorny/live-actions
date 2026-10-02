---
title: Shortwave Dial
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_shortwave_dial
pages: 1
words: 142
source: ableton_dataset.jsonl
---
# Shortwave Dial

## Sound Character & Overview
> **Layman Description:** Shortwave Dial

> **Emotional Vibe:** Lo-fi, Radio-like, Rhythmic, Gritty, Textural

## Technical Architecture & Signal Chain
Audio Effect Rack (Group Device)

## Chain of Thought Sound Design Breakdown
The preset is an Audio Effect Rack containing a single branch. The signal chain consists of three devices in series: a custom Max for Live Shaper, Ableton's Phaser-Flanger (set to 'Tape Doubler'), and Redux. This configuration is designed to emulate the unstable, filtered, and bit-crushed sound of an old shortwave radio through rhythmic modulation and sample rate reduction.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Shortwave Dial
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Shortwave Dial"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_shortwave_dial.xml` (70,605 bytes).
