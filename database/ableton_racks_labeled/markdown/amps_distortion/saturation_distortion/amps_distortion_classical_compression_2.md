---
title: Classical Compression
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_classical_compression_2
pages: 1
words: 201
source: ableton_dataset.jsonl
---
# Classical Compression

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Aggressive Dance Master', designed for mastering or heavy bus processing in a dance music context.

> **Emotional Vibe:** This preset is built to add aggression, punch, and controlled loudness to a mix, moving from clean limiting to 'brutal' saturated textures.

## Technical Architecture & Signal Chain
The preset utilizes an Audio Effect Group with a single 'Wet' branch containing a serial chain of EQ Eight, Compressor (v2), Saturator, and Limiter. It features 8 complex macros and 7 macro snapshots for rapid tonal shaping.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (ADG). 2. Analyze Macros: Mapped to EQ gains, Compression, and Limiting. 3. Trace Branch: 'Wet' branch contains the signal path. 4. Deconstruct Devices: EQ Eight -> Compressor -> Saturator -> Limiter. 5. Extract Parameters: Detailed values for every device in the chain.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Classical Compression
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Classical Compression"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_classical_compression_2.xml` (96,072 bytes).
