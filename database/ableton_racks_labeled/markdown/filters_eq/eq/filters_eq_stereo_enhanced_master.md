---
title: Stereo Enhanced Master
category: filters_eq
subcategory: eq
id: filters_eq_stereo_enhanced_master
pages: 1
words: 313
source: ableton_dataset.jsonl
---
# Stereo Enhanced Master

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack preset named 'Stereo Enhanced Master'. It uses a parallel processing structure (a branch named 'Wet') containing a chain of EQ, Compression, Utility, and Limiting. The rack is designed for mastering, featuring macro controls for tonal balance (Bass/Mid/High gain) and dynamic control.

> **Emotional Vibe:** A polished, professional mastering chain that provides surgical control over the stereo image and frequency spectrum, ensuring a tight, controlled, and loud final output.

## Technical Architecture & Signal Chain
Audio Effect Rack (ADG) utilizing parallel branching. Contains one active branch ('Wet') with a serial chain of EQ Eight, Glue Compressor, Utility (Stereo Gain), and Limiter. Macro controls are mapped to tonal balance and dynamic parameters.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (Stereo Enhanced Master).
2. Analyze Structure: It contains an 'AudioEffectBranchPreset' named 'Wet'. This indicates parallel processing.
3. Deconstruct 'Wet' Branch Chain:
    a. EQ Eight: Multiple bands active, specifically focusing on high-pass/crossover behavior in the low-mids and highs (Bands 3, 4, 5).
    b. Glue Compressor: Set with -12dB threshold, 4dB makeup, and 5ms attack.
    c. Utility (Stereo Gain): Configured for Mid/Side processing (Mid/Side Balance ON) and Stereo Width.
    d. Limiter: Final stage with a ceiling of -0.3dB and 300ms release.
4. Identify Macro Controls: The rack has 8 user-facing macros mapped to Bass Gain, Mid Gain, High Gain, Stereo Enhance, Comp Thresh, Comp Gain, Comp Dry/Wet, and Limiter Gain.
5. Extract Parameter Values: Pull specific numerical values for threshold, gain, frequency, and Q from the XML nodes.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Stereo Enhanced Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Stereo Enhanced Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_stereo_enhanced_master.xml` (81,855 bytes).
