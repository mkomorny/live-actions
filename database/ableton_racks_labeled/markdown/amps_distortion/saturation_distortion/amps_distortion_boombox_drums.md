---
title: Boombox Drums
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_boombox_drums
pages: 1
words: 304
source: ableton_dataset.jsonl
---
# Boombox Drums

## Sound Character & Overview
> **Layman Description:** Analyze this Ableton XML preset code. Identify all the effects, devices, and specific parameter values used within the structure.

> **Emotional Vibe:** You are a world-class mix engineer. Look at this 'Boombox Drums' preset code. Tell me exactly what kind of sonic character is being sculpted here by analyzing the EQ, compression, and saturation settings within the XML.

## Technical Architecture & Signal Chain
Perform a deep-dive structural analysis of the provided Ableton Live 11.3 Audio Effect Group (.adg) XML. Extract the device chain, individual device parameters (including non-obvious ones like expansion ratios), macro mappings, and snapshot states.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It's an Audio Effect Group (adg) named 'Boombox Drums'.
2. Identify the structure: It uses a Branching system. There is one branch visible called 'Wet'.
3. Trace the 'Wet' chain:
    - Device 1: EQ Eight
    - Device 2: Compressor (specifically Compressor2, the Live 11 version)
    - Device 3: Saturator
4. Extract EQ Eight details: Multiple bands active, including low-pass/high-pass filters and specific frequency notches.
5. Extract Compressor details: High ratio (40:1), fast attack (0.15ms), fast release (25ms), parallel mix at 50%.
6. Extract Saturator details: Pre-drive (+11dB), Post-drive (-4.9dB), Color frequency at 1kHz, Type mode 6.
7. Analyze Macros: Map the macro names to their default values.
8. Analyze Snapshots: 'Boombox', 'Cheap Unit', 'Push To Punch', and 'Hifi Pumper' have distinct parameter sets.
9. Synthesize: This is a drum processing rack designed for character, impact (punch), and lo-fi textures.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Boombox Drums
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Boombox Drums"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_boombox_drums.xml` (87,378 bytes).
