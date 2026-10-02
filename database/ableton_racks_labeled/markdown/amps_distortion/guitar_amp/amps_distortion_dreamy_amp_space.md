---
title: Dreamy Amp Space
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_dreamy_amp_space
pages: 1
words: 248
source: ableton_dataset.jsonl
---
# Dreamy Amp Space

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack titled 'Dreamy Amp Space', designed for ambient/dreamy guitar tones. It utilizes a serial chain of five devices: an Amp simulator, a Chorus-Ensemble, a Delay, a Hybrid Reverb, and a Glue Compressor. The rack features 8 macro controls (with specific names assigned to some) to allow for real-time manipulation of the tone's brightness, modulation depth, time-based effects, and compression.

> **Emotional Vibe:** A lush, ethereal, and expansive guitar tone that can shift from a dry, biting amp sound to a massive, swirling space-scape using macro controls.

## Technical Architecture & Signal Chain
Audio Effect Rack: 'Dreamy Amp Space'. Chain order: Amp -> Chorus-Ensemble -> Delay -> Hybrid Reverb -> Glue Compressor. Macro Mapping: Macro 3 (Treble), Macro 4 (Chorus), Macro 5 (Delay), Macro 6 (Reverb), Macro 7 (Comp).

## Chain of Thought Sound Design Breakdown
The XML represents an Audio Effect Rack (ADG). I will traverse the 'DevicePresets' section to identify each device in the signal chain and extract their specific parameter settings. Then, I will map the Macro Display Names to their respective indices to understand how a user interacts with this preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dreamy Amp Space
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dreamy Amp Space"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_dreamy_amp_space.xml` (89,889 bytes).
