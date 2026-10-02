---
title: Stun Echo
category: time_based_spatial
subcategory: delay
id: time_based_spatial_stun_echo
pages: 1
words: 204
source: ableton_dataset.jsonl
---
# Stun Echo

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Stun Echo', created by Michele Darling. It is a complex parallel processing chain designed for heavy, modulated, rhythmic delays with significant spatial depth and saturation.

> **Emotional Vibe:** The sound is likely massive, shimmering, slightly metallic due to the ring modulation, and highly rhythmic. It creates a sense of 'stunned' or 'dazed' space through heavy echo and reverb tails.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group (Rack) utilizing two branches: a heavily processed 'Wet' chain (Branch 0) and a clean 'Dry' pass-through (Branch 1). The crossfade between these branches is controlled by the Rack Dry/Wet macro.

## Chain of Thought Sound Design Breakdown
1. Identify Rack Name/Creator -> 2. Analyze Macro Mapping -> 3. Deconstruct Branch 0 (Wet) device by device -> 4. Deconstruct Branch 1 (Dry) -> 5. Synthesize sound design character.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Stun Echo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Stun Echo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_stun_echo.xml` (102,889 bytes).
