---
title: Filter Phaser
category: modulation
subcategory: lfo_modulation
id: modulation_filter_phaser
pages: 1
words: 461
source: ableton_dataset.jsonl
---
# Filter Phaser

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Filter Phaser'. It uses parallel processing (an Audio Effect Rack with branches) to create a multi-band phasing effect. It consists of a main rack containing two primary chains: a complex nested group called 'RS3' and a 'Dry' pass-through. The 'RS3' group contains a Stereo Gain utility followed by three parallel Auto Filters (Low, Mid, and High) that use LFOs to sweep different frequency bands, creating the phaser effect.

> **Emotional Vibe:** A lush, evolving, and wide rhythmic texture. The 'Filter Phaser' creates a sense of movement through sweeping frequency bands, ranging from deep, slow low-end wobbles to bright, shimmering high-end textures, all while maintaining a massive stereo image.

## Technical Architecture & Signal Chain
An Audio Effect Rack ('Filter Phaser') utilizing parallel branching. The primary signal path is split into two branches: a complex 'RS3' chain and a 'Dry' bypass. The 'RS3' chain consists of a Stereo Gain (Utility) in series with a nested Audio Effect Group. This nested group contains three parallel Auto Filter branches (Low, Mid, High) set to Band Pass mode with independent LFO modulations on the cutoff frequencies to simulate multi-band phase shifting.

## Chain of Thought Sound Design Breakdown
1. **Identify Root Device**: The XML starts with `<AudioEffectGroupDevice>`, which is an Audio Effect Rack named 'Filter Phaser'. 
2. **Analyze Macros**: I extracted the 8 visible macro mappings and their current values (e.g., Reso Intensity at 83, Stereo Width at 127).
3. **Deconstruct Branches (Main Rack)**:
    - **Branch 0**: Contains a nested group 'RS3' and a `StereoGain` device. This is the processed path.
    - **Branch 1 ('Dry')**: A simple mixer/pass-through branch.
4. **Analyze Nested Group ('RS3')**:
    - It contains a `StereoGain` (Utility) with specific settings: Stereo mode, Max width, Full Side MS balance, and +2.82dB gain.
    - It contains three parallel branches (Sub-branches):
        - **'Low'**: An Auto Filter set to Band Pass (`Manual Value 2`), Cutoff ~72Hz, Resonance ~0.35, with LFO enabled (~0.07Hz).
        - **'Mid'**: An Auto Filter set to Band Pass, Cutoff ~86Hz, Resonance ~0.39, with LFO enabled (~0.17Hz).
        - **'High'**: An Auto Filter set to Band Pass, Cutoff at Max (127), Resonance ~0.13, with LFO enabled (~0.19Hz).
5. **Synthesize Sound Design Intent**: The combination of three band-pass filters sweeping at different rates and frequencies in parallel is a classic way to build a 'Phaser' or 'Flanger' effect without using the dedicated Phaser device, allowing for much more control over the frequency bands.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filter Phaser
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filter Phaser"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_filter_phaser.xml` (122,736 bytes).
