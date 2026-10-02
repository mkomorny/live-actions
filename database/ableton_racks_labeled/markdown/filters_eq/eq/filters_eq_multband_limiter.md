---
title: Multband & Limiter
category: filters_eq
subcategory: eq
id: filters_eq_multband_limiter
pages: 1
words: 310
source: ableton_dataset.jsonl
---
# Multband & Limiter

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Multband & Limiter'. It uses a parallel processing structure with two branches: a 'Dry' branch (which contains the actual processing) and a 'Wet' branch (which is currently empty of effects).

> **Emotional Vibe:** The rack is configured for multiband dynamics control and peak limiting. The macro controls are mapped to specific frequency bands and limiter parameters, allowing for streamlined mastering or bus compression.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing a split-branch architecture. The primary signal path ('Dry' branch) implements multiband compression followed by a limiter, while the 'Wet' branch acts as a parallel/dry path (though it currently contains no processing devices).

## Chain of Thought Sound Design Breakdown
1. Identify the root: Audio Effect Rack ('Multband & Limiter').
2. Analyze Macro Controls: 8 macros are active (Bass, Mid, High Freq, High, Limiter Ceiling, Limiter Gain, Rack Dry/Wet, Rack Volume).
3. Analyze Branching: Two branches exist: 'Dry' and 'Wet'.
4. Deep dive into 'Dry' branch:
   - Device 1: Multiband Dynamics ('A Standard Multiband Comp').
     - Crossover frequencies: ~200Hz (SplitLowMid) and ~9.6kHz (SplitMidHigh).
     - Settings: SoftKnee ON, EnvelopeIsPeak OFF (RMS mode), OutputGain -5.12dB.
     - Band-specific settings for Low, Mid, and High bands (Thresholds, Ratios, Attack/Release).
   - Device 2: Limiter.
     - Gain: +4.72dB, Ceiling: 0dB, Release: 300ms, AutoRelease ON, Lookahead: 1ms.
   - Mixer: Volume set to ~0.67.
5. Deep dive into 'Wet' branch:
   - No devices present in the chain.
   - Mixer: Volume set to ~0.67.
6. Summarize all findings.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Multband & Limiter
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Multband & Limiter"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_multband_limiter.xml` (56,493 bytes).
