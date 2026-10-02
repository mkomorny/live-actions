---
title: EQ & Compressor Master
category: filters_eq
subcategory: filter
id: filters_eq_eq_compressor_master
pages: 1
words: 362
source: ableton_dataset.jsonl
---
# EQ & Compressor Master

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack named 'EQ & Compressor Master'. It is designed for tonal shaping and dynamic control, likely for a master bus or a heavy instrument group. It uses a parallel processing structure (Dry/Wet branches) and includes several macro-controlled snapshots for quick tonal changes.

> **Emotional Vibe:** A professional-grade mastering tool that offers surgical precision and dramatic tonal shifts, allowing the user to move from a 'Flat' response to an aggressive 'Body' or airy 'Presence' with a single knob turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing two main branches: 'Dry' and 'Wet'. The 'Dry' branch utilizes a serial chain of EQ Eight, Compressor 2, and Limiter. The 'Wet' branch contains only a Limiter. It features highly customized Macro controls and Snapshot variations (Flat, Body, Presence, Air, Parallel) to facilitate rapid spectral and dynamic adjustments.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (ADG) named 'EQ & Compressor Master'.
2. Analyze Macro Controls: 8 macros defined, including Bass, Mid, Mid Freq, High, Comp Output, and Dry/Wet.
3. Analyze Branching: Two branches - 'Dry' (contains EQ -> Comp -> Limiter) and 'Wet' (contains Limiter).
4. Deep Dive 'Dry' Branch:
   - Device 1: EQ Eight (Preset: Electric Git EQ 1). Notable bands: Low shelf/bell at ~52Hz, High pass/Low cut at 200Hz, various bell/notch filters in the mids and highs.
   - Device 2: Compressor 2 (Preset: Classical Compression). Parameters: Threshold ~-0.18dB, Ratio ~1.57:1, Attack ~0.22ms, Release 100ms, Gain +1.54dB, Knee 6.33dB.
   - Device 3: Limiter. Parameters: Ceiling -3dB, Release 300ms, Auto-release ON.
5. Deep Dive 'Wet' Branch:
   - Device 1: Limiter. Parameters: Ceiling -3dB, Release 300ms, Auto-release ON.
6. Analyze Snapshots: Five snapshots (Flat, Body, Presence, Air, Parallel) which manipulate the macros to change the EQ and Compression character.

## Live Actions Blueprint
```python
# Live Actions device chain reference for EQ & Compressor Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "EQ & Compressor Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_eq_compressor_master.xml` (94,110 bytes).
