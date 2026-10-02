---
title: Smokey Water
category: filters_eq
subcategory: eq
id: filters_eq_smokey_water
pages: 1
words: 362
source: ableton_dataset.jsonl
---
# Smokey Water

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Group preset named 'Smokey Water' created by Huston Singletary. It utilizes a single effect branch containing a heavy saturation and drum-processing chain, ending with EQ and limiting. The preset features custom Macro controls for 'Drive', 'Pressure', and 'Hi Freq', along with three specific snapshots: 'Hook', 'Middle Rhythm', and 'Lower Drive'.

> **Emotional Vibe:** A thick, gritty, and controlled distortion preset designed to add 'smokey' character and weight to drums or instruments. It provides aggressive drive and pressure with a high-frequency roll-off for a warm, vintage saturation feel.

## Technical Architecture & Signal Chain
Audio Effect Group Preset Analysis: 'Smokey Water'. Structure: Single Branch (Branch 0). Chain: Amp -> Drum Buss -> EQ Three -> Limiter -> Mixer. Macro Mapping: Custom names for Macros 3 (Drive), 4 (Pressure), and 6 (Hi Freq). Snapshots defined: Hook, Middle Rhythm, Lower Drive.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Group ('Smokey Water').
2. Analyze Branching: One branch detected (Branch 0).
3. Device 1 Analysis: Amp (Preset: 'Rhodes 2 way Amp'). Parameters: Bass ~8.5, Mid 10, Treble ~1.1, Presence ~7.6, Gain ~5.6, Vol ~6.7, Dry/Wet ~80%, Dual Mono ON.
4. Device 2 Analysis: Drum Buss. Parameters: Compression OFF, Drive ~0.93, Crunch ~0.96, Damping ~9.9kHz, Transient Shaping ~-0.83, Boom Freq ~65Hz, Boom Amt ~0.63, Boom Decay ~0.92, Input Trim 1.0, Output Gain ~0.63, Dry/Wet ~78%.
5. Device 3 Analysis: EQ Three. Parameters: Low Gain ~1.2, Mid Gain ~1.79, High Gain ~0.89, Freq Lo ~2.6kHz, Freq Hi ~4kHz, Low ON, Mid ON, High OFF (Band-pass/Low-mid focus).
6. Device 4 Analysis: Limiter. Parameters: Gain ~-0.2dB, Ceiling ~-0.3dB, Release 300ms, Auto-Release ON, Link Channels ON, Lookahead 1ms.
7. Macro Mapping: Macros 3 (Drive), 4 (Pressure), and 6 (Hi Freq) are explicitly named.
8. Snapshots Analysis: 'Hook', 'Middle Rhythm', and 'Lower Drive' provide distinct macro-controlled states.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Smokey Water
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Smokey Water"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_smokey_water.xml` (50,775 bytes).
