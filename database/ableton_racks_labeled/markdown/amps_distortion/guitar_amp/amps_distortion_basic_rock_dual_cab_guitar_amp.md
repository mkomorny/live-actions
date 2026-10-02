---
title: Basic Rock Dual Cab Guitar Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_rock_dual_cab_guitar_amp
pages: 1
words: 209
source: ableton_dataset.jsonl
---
# Basic Rock Dual Cab Guitar Amp

## Sound Character & Overview
> **Layman Description:** This is a high-gain guitar amp simulation rack designed for 'Basic Rock' tones. It uses a complex signal chain including a gate, saturation, an amp modeler, a dual-cabinet sub-rack (stereo), compression, and a spring reverb.

> **Emotional Vibe:** Aggressive, heavy, and textured rock guitar tones with a wide, immersive stereo field and lush spring reverb tails.

## Technical Architecture & Signal Chain
An Ableton Live Audio Effect Rack containing a serial signal chain: Gate -> Saturator -> Amp -> [Sub-Rack: Cabinets] -> Compressor2 -> Hybrid Reverb. The rack features 12 mapped macro controls for real-time tone shaping and includes a stereo cabinet spread via parallel branching.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will trace the signal path through the main chain and descend into the nested 'Cabinets' rack to identify all devices and their specific settings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Rock Dual Cab Guitar Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Rock Dual Cab Guitar Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_rock_dual_cab_guitar_amp.xml` (129,211 bytes).
