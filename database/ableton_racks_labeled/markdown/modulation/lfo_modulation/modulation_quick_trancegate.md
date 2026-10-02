---
title: Quick TranceGate
category: modulation
subcategory: lfo_modulation
id: modulation_quick_trancegate
pages: 1
words: 198
source: ableton_dataset.jsonl
---
# Quick TranceGate

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Quick TranceGate'. It uses a combination of LFO and Shaper to create rhythmic gating, followed by two Auto Pan devices for stereo movement.

> **Emotional Vibe:** A rhythmic, pulsing, and wide-stereo trance gating effect that chops audio into precise 1/4 note patterns with swirling movement.

## Technical Architecture & Signal Chain
Audio Effect Rack: Quick TranceGate. Signal path consists of a gated branch (LFO -> Shaper) followed by serial Auto Pan modulation.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. The first branch (Chain 0) contains a nested rack with an LFO and a Shaper. This is the core 'Trance Gate' engine. Following this chain, there are two Auto Pan devices in series. The macros are mapped to control speed, strength, and the on/off state of the effect components.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Quick TranceGate
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Quick TranceGate"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_quick_trancegate.xml` (100,727 bytes).
