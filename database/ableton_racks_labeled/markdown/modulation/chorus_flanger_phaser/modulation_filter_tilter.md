---
title: Filter Tilter
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_filter_tilter
pages: 1
words: 264
source: ableton_dataset.jsonl
---
# Filter Tilter

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Filter Tilter'. It uses a parallel branching structure to allow for seamless Dry/Wet blending using a single macro. The 'Wet' chain is a complex serial processing chain designed for tonal shaping, featuring dual Auto Filters (one for movement and one for tone), saturation via filter drive, and a limiter to catch peaks.

> **Emotional Vibe:** A versatile and cinematic filter tool that can transform sounds from smooth and watery to aggressive and fiery with a single turn of a knob.

## Technical Architecture & Signal Chain
An Audio Effect Rack containing two branches: 'Wet' and 'Dry'. The 'Wet' branch utilizes a serial chain of Utility -> Auto Filter -> Auto Filter -> Utility -> Limiter. It features macro-mapped parameters for filter tilt, cutoff, resonance, modulation, input gain, drive, rack volume, and dry/wet mix. Four snapshots ('Water', 'Earth', 'Air', 'Fire') are included to provide distinct spectral profiles.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (GroupDevicePreset). I will first identify the macro mapping, then analyze each branch ('Wet' and 'Dry') individually, detailing every device and its specific parameter settings found in the <DevicePresets> section. Finally, I will note the snapshots which define the preset's character shifts.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filter Tilter
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filter Tilter"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_filter_tilter.xml` (79,486 bytes).
