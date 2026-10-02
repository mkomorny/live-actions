---
title: Big Boom Master
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_big_boom_master
pages: 1
words: 236
source: ableton_dataset.jsonl
---
# Big Boom Master

## Sound Character & Overview
> **Layman Description:** This is a complex Ableton Live Audio Effect Rack titled 'Big Boom Master', designed for mastering. It utilizes a parallel processing structure (specifically a 'Wet' branch) containing a heavy-hitting chain of drum enhancement, surgical EQ, character reverb, compression, and final limiting.

> **Emotional Vibe:** A powerful, aggressive mastering chain designed to add massive low-end weight ('Boom'), transient punch, and wide stereo depth while maintaining controlled loudness.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (.adg) featuring 16 macro controls and a single active branch named 'Wet'. The signal chain follows a serial architecture: Drum Buss -> EQ Eight -> EQ Three -> Reverb -> Compressor (Mk2) -> Limiter.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevicePreset). 2. Analyze Macros: 8 visible macros mapped to gain, drive, boom, transients, space, and limiter. 3. Trace Branch 'Wet': Drum Buss -> EQ Eight -> EQ Three -> Reverb -> Compressor -> Limiter. 4. Extract Parameters: For each device, extract specific manual values (Freq, Gain, Time, etc.). 5. Synthesize Engineer's Analysis.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Big Boom Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Big Boom Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_big_boom_master.xml` (111,431 bytes).
