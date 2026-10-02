---
title: 808 Tuning, Saturation & Phase Alignment
category: bass_sound_design
subcategory: 808_and_sub_bass_management
id: doc_027_bass_design_808_sub_management
words: 183
source: ableton_god_producer_15k.jsonl
---
# 808 Tuning, Saturation & Phase Alignment

Master synthesis reference and Ableton Live 12 workflow for 808 and Sub Bass Management (Sub Bass Management).

## Core Synthesis Architecture
- **Target Frequency Spectrum**: 30 Hz fundamental to 300 Hz harmonic body.
- **Oscillator Configuration**: Pure Sine wave sub fundamental paired with lightly detuned (+4 to +8 cents) harmonic voice.
- **Filter Topology**: 24 dB/oct Low-Pass filter set to 180 Hz - 260 Hz with controlled resonance (12-16%).
- **Envelope Profile**: Zero attack, 250 ms decay, zero sustain, 75 ms release.
- **Sidechain Routing**: Mandatory ducking beneath Kick transient (-20 dB, 4:1 ratio, 5 ms attack).

## Live Actions Parameter Blueprint
```python
# Live Actions Python Blueprint: Create Native Drift Synth for Bass
live_create_device(track_index=1, device_name="Drift", params=[
    {"name": "Osc 1 Wave", "value": "Sine"},
    {"name": "Osc 2 Wave", "value": "Saw"},
    {"name": "Osc 2 Detune", "value": "0.06"},
    {"name": "Filt 1 Type", "value": "24 Low"},
    {"name": "Filt 1 Freq", "value": "220 Hz"},
    {"name": "Filt 1 Reso", "value": "14%"},
    {"name": "Env 1 Decay", "value": "280 ms"}
])
```

## Professional Production Workflow Example
Standard bass design instructions.
