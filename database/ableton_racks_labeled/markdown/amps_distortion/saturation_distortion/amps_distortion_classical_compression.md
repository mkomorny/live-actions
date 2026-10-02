---
title: Classical Compression
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_classical_compression
pages: 1
words: 280
source: ableton_dataset.jsonl
---
# Classical Compression

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Bright & Edgy Master'. It is a complex processing chain designed for mastering or heavy bus processing, featuring multiple snapshots that change the character from 'Light & Clean' to 'Over Driven'.

> **Emotional Vibe:** This preset is a powerful tool for transforming a sound from polished and clean to aggressive and saturated with just a single knob turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) utilizing a single branch named 'Wet'. The signal chain within this branch consists of EQ Eight $\rightarrow$ Compressor 2 $\rightarrow$ Overdrive $\rightarrow$ Limiter. It utilizes 8 macro controls and 5 macro snapshots for high-level parameter automation.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack ('Bright & Edgy Master').
2. Analyze Macros: 8 macros mapped to specific functions (Gain, Drive, Tone, Comp, Limiter).
3. Analyze Snapshots: 5 distinct states (Bright & Edgy, Light & Clean, Loud & Bright, Tamed Highs, Over Driven).
4. Deconstruct Branch 'Wet':
   - EQ Eight: Complex multi-band filtering (High Pass at 100Hz/500Hz and high-end shaping at 8kHz/10kHz).
   - Compressor 2: 'Classical Compression' preset, Ratio 1.5:1, Attack 10ms, Release 100ms.
   - Overdrive: Drive ~30dB, Tone 60, Mid Freq ~557Hz.
   - Limiter: Ceiling -0.3dB, Lookahead 2ms.
5. Identify Mixer: Branch mixer is set to unity gain and center pan.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Classical Compression
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Classical Compression"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_classical_compression.xml` (89,238 bytes).
