---
title: Xfer Serum Wavetable & Detuned Reese Bass
category: bass_sound_design
subcategory: serum
id: doc_024_bass_design_serum
words: 347
source: ableton_god_producer_15k.jsonl
---
# Xfer Serum Wavetable & Detuned Reese Bass

Master synthesis reference and Ableton Live 12 workflow for Serum (Wavetable).

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
<think>
God-Level Bass Design Reasoning:
For Trap, we need:
- Strong sub energy (30-60Hz)
- Mid presence for character (150-400Hz)
- Controlled harmonics to avoid mud

Serum Setup:
- Osc 1: Sine wave (sub) + slight detune
- Osc 2: Saw or Wavetable (character) - detune +3-7 cents
- Filter: Low-pass 24dB, cutoff 180-280Hz, resonance 12-18%
- Envelope: Amp Attack 0ms, Decay 180-350ms, Sustain 0%, Release 80ms
- Add subtle pitch envelope on filter for movement

Routing in Ableton:
- Main track: Serum → EQ Eight (high-pass 28Hz, -12dB/oct)
- Send to "Bass Bus" with Multiband Dynamics (low band compression)
- Sidechain to kick with 1/4 note pump (using Glue Compressor or stock Compressor)
</think>

**Exact Ableton Steps:**
1. Create MIDI track → Load Serum
2. Load preset "Init" or "Basic Sine"
3. Set parameters exactly as above
4. Draw 1/8 or 1/4 note bassline in C1-C2 range
5. Group with drums → Sidechain compression (threshold -24dB, ratio 6:1, attack 5ms)

This bass will punch through any mix while leaving space for kicks.
