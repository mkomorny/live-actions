---
title: Core Drum Master
category: time_based_spatial
subcategory: delay
id: time_based_spatial_core_drum_master
pages: 1
words: 238
source: ableton_dataset.jsonl
---
# Core Drum Master

## Sound Character & Overview
> **Layman Description:** This is a professional drum mastering/bus processing chain titled 'Core Drum Master'. It uses a combination of surgical EQ, dynamic compression, and character-driven drum bussing to glue a drum kit together.

> **Emotional Vibe:** This preset provides a powerful, cohesive, and aggressive 'glue' for your drums, allowing you to transition from clean, punchy overheads to heavy, smashed room sounds with a single macro turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group containing a serial chain: EQ Eight -> Compressor -> Drum Buss. It features 8 macro controls for parallel processing and tonal shaping, along with 5 specific snapshots for different drum scenarios (e.g., 'Room Smasher', 'Transient Killer').

## Chain of Thought Sound Design Breakdown
The XML represents an Audio Effect Group. I will traverse the <BranchPresets> to find the active device chain. The devices are nested within an 'AudioEffectBranchPreset'. The order of operations is EQ Eight, then Compressor, then Drum Buss. Each device's parameters are extracted from its respective <Device> tag. Finally, Macro controls and Snapshots are mapped from the top-level Group Device settings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Core Drum Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Core Drum Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_core_drum_master.xml` (87,669 bytes).
