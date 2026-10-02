---
title: Drum Transistor
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_drum_transistor
pages: 1
words: 265
source: ableton_dataset.jsonl
---
# Drum Transistor

## Sound Character & Overview
> **Layman Description:** This is an Ableton Audio Effect Rack (.adg) named 'Drum Transistor' created by Huston Singletary. It uses a single effect branch containing a chain of three devices: a custom Max for Live Shaper, Ableton Redux (for bitcrushing), and Ableton Phaser-Flanger (used here as a doubler/phaser). The rack is highly playable via 6 macros and includes 5 distinct snapshots for different textures like 'Crushed' and 'Timpani'.

> **Emotional Vibe:** A heavy, rhythmic drum processing rack called 'Drum Transistor'. It combines precise rhythmic gating/shaping with gritty bitcrushing and wide, swirling phase modulation. Perfect for industrial techno or glitchy percussion.

## Technical Architecture & Signal Chain
Audio Effect Rack: Drum Transistor. Chain: [Shaper (M4L) -> Redux -> Phaser-Flanger]. Macros: 6 active. Snapshots: Default, Crushed, Polar Axis, Timpani, Flux Factor.

## Chain of Thought Sound Design Breakdown
The XML represents an Audio Effect Rack (GroupDevicePreset). I will traverse the <BranchPresets> to find the actual device chain. Inside the first branch, there is a sequence of three devices: 1. A Max for Live 'Shaper' (identified by its .amxd patch slot), 2. Redux, and 3. Phaser-Flanger. Each device has specific parameter values defined in their respective <Device> tags. I will also extract the Macro settings and Snapshots which define the user interface and preset states.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Drum Transistor
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Drum Transistor"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_drum_transistor.xml` (73,315 bytes).
