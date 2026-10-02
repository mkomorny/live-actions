---
title: Loop
category: rhythm_glitch
subcategory: glitch_repeat
id: rhythm_glitch_loop
pages: 1
words: 251
source: ableton_dataset.jsonl
---
# Loop

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Instant Repeat'. It uses a parallel processing structure (Branches) to switch between a rhythmic 'Loop' effect and a clean 'Dry' signal. The core of the effect is a Beat Repeat device configured for specific rhythmic patterns, controlled via Macro Snapshots.

> **Emotional Vibe:** This preset is designed for high-energy performance, allowing a DJ or live performer to instantly transform a steady beat into complex, glitchy rhythmic loops with a single knob turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing two branches: a 'Loop' branch with a Beat Repeat device and a 'Dry' branch. It utilizes Macro Snapshots to automate the transition between different rhythmic loop lengths (1/2, 1/4, and 1/16 notes).

## Chain of Thought Sound Design Breakdown
The XML describes an AudioEffectGroupDevice (an Effect Rack). I will analyze the branches first. Branch 0 is named 'Loop' and contains a Beat Repeat device. Branch 1 is named 'Dry' and is empty (purely for parallel routing). Then, I will extract the specific parameter values from the Beat Repeat device in Branch 0 and the Macro Snapshot settings which define the preset's functionality.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Loop
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Loop"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/rhythm_glitch_loop.xml` (39,749 bytes).
