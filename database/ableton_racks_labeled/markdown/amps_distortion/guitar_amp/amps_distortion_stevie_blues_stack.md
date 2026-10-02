---
title: Stevie Blues Stack
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_stevie_blues_stack
pages: 1
words: 233
source: ableton_dataset.jsonl
---
# Stevie Blues Stack

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Stevie Blues Stack' created by Huston Singletary. It contains a single branch called 'Wet Signal' that processes audio through a series of guitar-centric effects: a Gate, a Pedal, an Amp simulator, an Echo, and a Cabinet simulation.

> **Emotional Vibe:** This is a high-quality blues guitar tone stack. It uses a gate to clean up noise, a pedal for grit, an amp sim for core character, and a stereo 'Two Analogues' echo for space. The asymmetric delay times in the Echo device will create a wide, lush stereo field.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing one active branch ('Wet Signal'). The signal chain follows a serial routing: Gate -> Pedal -> Amp -> Echo -> Cabinet. It utilizes 16 Macro controls for global parameter manipulation.

## Chain of Thought Sound Design Breakdown
The analysis follows the XML hierarchy: GroupDevicePreset -> BranchPresets (Wet Signal) -> DevicePresets (0 through 4). Each device is then parsed for its specific parameter values and mapping.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Stevie Blues Stack
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Stevie Blues Stack"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_stevie_blues_stack.xml` (72,586 bytes).
