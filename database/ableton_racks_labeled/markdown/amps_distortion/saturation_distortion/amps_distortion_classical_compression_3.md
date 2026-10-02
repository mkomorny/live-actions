---
title: Classical Compression
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_classical_compression_3
pages: 1
words: 232
source: ableton_dataset.jsonl
---
# Classical Compression

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Group preset named 'Overdriven Tape Master'. It uses a parallel processing structure, specifically featuring a 'Wet' branch designed for heavy saturation and controlled dynamics.

> **Emotional Vibe:** This preset is designed to add 'grit', 'weight', and 'glue' to a mix. It feels aggressive yet controlled, moving from clean signal to a heavily driven, compressed, and limited 'Wet' version that can be blended in for character.

## Technical Architecture & Signal Chain
An analysis of the XML reveals a complex mastering/bus processing chain within an Audio Effect Group. The preset utilizes Macro controls to drive multiple devices simultaneously, primarily focusing on harmonic saturation (Overdrive), dynamic control (Compressor and Limiter), and surgical frequency shaping (EQ Eight).

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Group (ADG). 2. Analyze Macros: 8 macros mapped to specific functions. 3. Trace Branches: One branch named 'Wet'. 4. Deconstruct 'Wet' Chain: EQ Eight -> Compressor -> Overdrive -> Limiter. 5. Extract Parameters: For each device, identify the active bands/parameters and their values.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Classical Compression
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Classical Compression"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_classical_compression_3.xml` (89,654 bytes).
