---
title: Echo Fuzz
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_echo_fuzz
pages: 1
words: 281
source: ableton_dataset.jsonl
---
# Echo Fuzz

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Echo Fuzz' created by Michele Darling. It uses a parallel processing structure with two branches: a 'Wet' chain containing multiple modulation and time-based effects, and a 'Dry' branch that acts as a pure bypass.

> **Emotional Vibe:** A lush, swirling, and slightly gritty space-maker. It combines rhythmic delays and heavy modulation with a subtle fuzz/pedal grit, all held in check by a limiter for a massive but controlled ambient texture.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) utilizing a dual-branch architecture. Branch 0 contains a serial signal chain of Chorus, Phaser, Pedal, Echo, Auto Pan, and Limiter. Branch 1 is a dry bypass. The rack features 8 active macro controls mapped to various parameters across the chain.

## Chain of Thought Sound Design Breakdown
The analysis begins by identifying the top-level container: an Audio Effect Rack named 'Echo Fuzz'. I then examine the branch structure. Branch 1 is explicitly labeled 'Dry' and contains no devices, serving as a bypass. Branch 0 is the 'Wet' chain. Within Branch 0, there are six devices in a serial chain. For each device, I extract the specific parameter values (converting normalized decimals to percentages or dB where applicable). Finally, I map the Macro Controls which provide user-facing control over the complex internal routing and parameters.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Echo Fuzz
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Echo Fuzz"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_echo_fuzz.xml` (86,387 bytes).
