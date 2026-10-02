---
title: 'Master Recipe 2: Sub & Synth Bass Sound Design'
category: core_production_recipes
subcategory: bass
id: doc_006_recipe_2_sub_and_synth_bass_design
words: 264
source: PLAIN_ENGLISH_EXPLAINED.txt
---
# Master Recipe 2: Sub & Synth Bass Sound Design

The universal bass design formula utilized across 1,609 examples in the God Producer corpus.

## Acoustic & Synthesis Architecture

- **Oscillator 1 (Fundamental Sub)**: Pure Sine wave in the sub-octave range (C1-C2, 32 Hz to 65 Hz). Zero detune.
- **Oscillator 2 (Harmonic Definition)**: Sawtooth, Square, or Wavetable voice tuned to the same octave or +1 octave, detuned +3 to +7 cents for stereo spread.
- **Filter Section**: 24 dB/oct Low-Pass filter. Cutoff tuned to 180 Hz - 280 Hz with 12% - 18% resonance.
- **Amplitude Envelope**:
  - Attack: 0.0 ms (instant punch).
  - Decay: 180 ms - 350 ms (tight decay clearing space for kick hits).
  - Sustain: 0.0% to 15%.
  - Release: 60 ms - 90 ms.
- **Pitch Modulation**: Subtle 2-4 semitone instant pitch envelope drop (5-10 ms) on the transient onset.

## Ableton Live 12 Channel Processing Chain
1. **EQ Eight**: 48 dB/oct High-pass at 28 Hz (eliminating sub-audible speaker excursion).
2. **Multiband Dynamics**: Upward compression on the low band (Below 120 Hz) to lock consistent low-end energy.
3. **Glue Compressor (Sidechain Mode)**: Sidechained to Kick track. Threshold: -24 dB, Ratio: 6:1, Attack: 2 ms, Release: 80 ms.

```python
# Live Actions Python Blueprint: Instantiate Drift for Sub Bass
live_create_device(track_index=1, device_name="Drift", params=[
    {"name": "Osc 1 Wave", "value": "Sine"},
    {"name": "Osc 2 Wave", "value": "Saw"},
    {"name": "Osc 2 Detune", "value": "0.05"},
    {"name": "Filt 1 Type", "value": "24 Low"},
    {"name": "Filt 1 Freq", "value": "220 Hz"},
    {"name": "Env 1 Decay", "value": "280 ms"},
    {"name": "Env 1 Sustain", "value": "0.0"}
])
```
