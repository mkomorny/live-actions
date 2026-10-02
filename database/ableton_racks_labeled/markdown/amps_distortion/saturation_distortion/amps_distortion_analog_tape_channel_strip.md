---
title: Analog Tape Channel Strip
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_analog_tape_channel_strip
pages: 1
words: 273
source: ableton_dataset.jsonl
---
# Analog Tape Channel Strip

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Analog Tape Channel Strip', designed as a vintage mastering processor. It uses a parallel Dry/Wet structure via branches, where the 'Wet' branch contains a serial chain of EQ, Compression, Saturation, and Utility (Stereo Gain) to emulate tape character.

> **Emotional Vibe:** This preset provides a warm, vintage, and 'gluey' analog tape feel. It allows for smooth saturation and controlled dynamics, perfect for adding character and weight to a master bus or a drum group without losing the original punch.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing two branches. The Wet branch implements a signal path consisting of: 1. EQ Three (Low-shelf/High-shelf filtering), 2. Compressor (configured with an 'Opto' style timing), 3. Saturator (with heavy Pre-Drive and Color settings), and 4. Utility (for Mid-Side balance). The rack is controlled via 8 primary macros.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (AER). I will first identify the macro controls which act as the user interface. Then, I will traverse the 'Wet' branch to map out the serial device chain: EQ Three -> Compressor -> Saturator -> Utility. Finally, I will extract specific parameter values for each device and note the existence of Macro Snapshots.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Analog Tape Channel Strip
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Analog Tape Channel Strip"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_analog_tape_channel_strip.xml` (68,465 bytes).
