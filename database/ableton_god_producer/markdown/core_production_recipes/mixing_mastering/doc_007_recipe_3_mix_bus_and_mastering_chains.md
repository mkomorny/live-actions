---
title: 'Master Recipe 3: Mix Bus & Mastering Chains'
category: core_production_recipes
subcategory: mixing_mastering
id: doc_007_recipe_3_mix_bus_and_mastering_chains
words: 273
source: PLAIN_ENGLISH_EXPLAINED.txt
---
# Master Recipe 3: Mix Bus & Mastering Chains

The definitive mixing and mastering chains provided across the God Producer engineering benchmarks.

## Mix Bus Architecture (Track Group)
Placed across the composite mix bus prior to the master track:

1. **EQ Eight (Surgical Cleaning)**:
   - High-pass: 25 Hz (48 dB/oct steep slope).
   - Low-mid dip: -2.5 dB to -3.0 dB at 250 Hz (Q: 2.5 - 3.0) to eliminate boxiness.
   - High shelf: +1.5 dB to +2.5 dB at 12 kHz for high-end polish.
2. **Glue Compressor (Mix Bus Bonding)**:
   - Threshold: -18 dB to -16 dB (targeting 2 dB to 3 dB of gain reduction).
   - Ratio: 2:1 or 4:1.
   - Attack: 10 ms to 30 ms (preserving drum transient punch).
   - Release: Auto or 100 ms.
3. **Multiband Dynamics**:
   - Gentle low-mid control (200 Hz - 800 Hz) with soft knee.

## Master Output Chain
1. **Utility**:
   - Bass Mono activated at 120 Hz (ensuring mono compatibility on club sound systems).
   - Width set to 100% to 110%.
2. **EQ Eight (Linear Phase Mastering Mode)**:
   - +1.5 dB gentle low shelf at 60 Hz.
   - +1.8 dB high shelf at 14 kHz.
3. **Limiter (Ableton Stock or Pro-L 2)**:
   - Ceiling: -0.3 dB True Peak (or -1.0 dBTP for lossy streaming encodes).
   - Lookahead: 5 ms.
   - Target Loudness: -8 to -9 LUFS for club masters; -14 LUFS for streaming releases.

```python
# Live Actions Python Blueprint: Master Channel Setup
live_create_device(track_index=-1, device_name="Utility", params=[
    {"name": "Bass Mono", "value": "1"},
    {"name": "Bass Mono Freq", "value": "120 Hz"}
])
live_create_device(track_index=-1, device_name="Limiter", params=[
    {"name": "Ceiling", "value": "-0.3 dB"},
    {"name": "Lookahead", "value": "5 ms"}
])
```
