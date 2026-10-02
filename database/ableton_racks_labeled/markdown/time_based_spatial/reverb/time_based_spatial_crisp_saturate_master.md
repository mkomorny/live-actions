---
title: Crisp Saturate Master
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_crisp_saturate_master
pages: 1
words: 460
source: ableton_dataset.jsonl
---
# Crisp Saturate Master

## Sound Character & Overview
> **Layman Description:** This is a Mastering Effect Group preset named 'Crisp Saturate Master' created by Michele Darling. It uses an effect chain (branch) called 'Wet' that contains a series of processing devices: Drum Buss, EQ Eight, Glue Compressor, Reverb, Utility, and Limiter.

> **Emotional Vibe:** This is a high-end mastering chain designed to add 'crispness' and saturation. It uses Drum Buss for low-end weight, EQ Eight for tonal shaping (with specific boosts in the low-mids and highs), Glue Compressor for density, Reverb for depth, and a Limiter for loudness. The macros allow you to control the intensity of these processes.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Group (ADG) utilizing a single branch named 'Wet'. The signal chain follows a classic mastering topology: transient/low-end enhancement $\rightarrow$ surgical EQ $\rightarrow$ glue compression $\rightarrow$ spatial enrichment $\rightarrow$ stereo imaging $\rightarrow$ peak limiting. It features 8 mapped macro controls for real-time automation of drive, transients, compression, space, and limiting.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Group ('Crisp Saturate Master').
2. Identify Branching: One branch exists named 'Wet'.
3. Traverse 'Wet' Chain:
    - Device 1: Drum Buss (Preset: Soft Boom in D). Parameters: Compression On, Drive 0, Crunch 0, Damping 18.8kHz, Transient Shaping 0.26, Boom Freq 54.7Hz, Input Trim 0.016.
    - Device 2: EQ Eight (Preset: Electric Git EQ 1). Parameters: Band 3A boost at 75.8Hz (+2.1dB), Band 4A cut at 639Hz (-0.87dB), Band 5A boost at 8kHz (+1dB).
    - Device 3: Glue Compressor. Parameters: Threshold -5.67dB, Range 15dB, Makeup 9.06dB, Attack 6ms, Dry/Wet 64.5%.
    - Device 4: Reverb. Parameters: Pre-delay 2.5ms, Decay 743ms, Room Size 31.7%, Stereo Separation 100%, Chorus On.
    - Device 5: Utility (Stereo Gain). Parameters: Gain +1.58dB, Stereo Width 1 (Normal).
    - Device 6: Limiter. Parameters: Gain +6dB, Ceiling -0.3dB, Release 300ms, Lookahead 2ms.
4. Identify Macros:
    - Macro 0: Drive
    - Macro 3: Trnsnt (Value: 80)
    - Macro 4: Comp Thresh (Value: 109)
    - Macro 5: Comp Gain (Value: 115)
    - Macro 6: Space (Value: 28)
    - Macro 7: Limiter Gain (Value: 127 - Maxed)

### Mapped Macro Controls
- **Macro 1:** `Drive`
- **Macro 2:** `Trnsnt`
- **Macro 3:** `Comp Thresh`
- **Macro 4:** `Comp Gain`
- **Macro 5:** `Space`
- **Macro 6:** `Limiter Gain`

## Live Actions Blueprint
```python
# Live Actions device chain reference for Crisp Saturate Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Crisp Saturate Master"},
    {"name": "Macro 1 (Drive)", "value": 64},
    {"name": "Macro 2 (Trnsnt)", "value": 64},
    {"name": "Macro 3 (Comp Thresh)", "value": 64},
    {"name": "Macro 4 (Comp Gain)", "value": 64},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_crisp_saturate_master.xml` (110,658 bytes).
