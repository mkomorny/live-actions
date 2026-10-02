---
title: Basic Lead Guitar Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_lead_guitar_amp
pages: 1
words: 261
source: ableton_dataset.jsonl
---
# Basic Lead Guitar Amp

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML to identify the signal chain, devices, and settings.

> **Emotional Vibe:** You are an expert sound designer. Break down this complex guitar amp rack so a producer can recreate it perfectly.

## Technical Architecture & Signal Chain
Perform a deep-structure analysis of the Audio Effect Rack (AER) provided in the XML. Identify the device hierarchy, specific plugin instances, parameter values, and macro mappings.

## Chain of Thought Sound Design Breakdown
1. Identify the root device: It is an Audio Effect Rack named 'Basic Lead Guitar Amp'.
2. Analyze the signal chain structure: The rack contains three main components (Gate $\rightarrow$ Amp $\rightarrow$ Cabinet Rack).
3. Deconstruct Device 1 (Gate): Found in the 'Wet' branch, it uses a user-library preset 'Guitar Gate'.
4. Deconstruct Device 2 (Amp): An Ableton Core Library 'Amp' device with specific gain/EQ settings.
5. Deconstruct Device 3 (Cabinets Rack): A nested Audio Effect Rack containing two parallel branches ('Cond Far' and 'Dyn Near') each utilizing a 'Cabinet' device.
6. Map Macros: Connect the Macro controls to their respective parameters (Gain, Bass, Mid, Treble, Volume, Cabinet Mix, Gate Intensity).
7. Extract Snapshots: Identify the four distinct tonal presets (Default, Extreme, Nasal Lead, Little Old Amp).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Lead Guitar Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Lead Guitar Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_lead_guitar_amp.xml` (79,040 bytes).
