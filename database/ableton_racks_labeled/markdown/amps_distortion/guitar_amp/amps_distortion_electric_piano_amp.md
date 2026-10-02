---
title: Electric Piano Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_electric_piano_amp
pages: 1
words: 183
source: ableton_dataset.jsonl
---
# Electric Piano Amp

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack designed for an electric piano (specifically a Rhodes style), providing amp simulation, drum-style saturation/compression, tonal shaping via EQ, and final peak limiting.

> **Emotional Vibe:** Warm, vintage, and punchy electric piano tones with controlled dynamics and harmonic saturation.

## Technical Architecture & Signal Chain
An Ableton Live Audio Effect Rack containing a single serial processing chain: Amp (Rhodes 2 way) -> Drum Buss -> EQ Three -> Limiter. The rack includes custom macro mappings for Drive, Pressure, and Transient shaping.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (ADG). The signal flows through a single branch containing four devices in series. I will extract the parameters for each device and the macro mappings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Electric Piano Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Electric Piano Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_electric_piano_amp.xml` (46,687 bytes).
