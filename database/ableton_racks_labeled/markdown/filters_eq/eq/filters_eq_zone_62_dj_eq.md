---
title: Zone 62 DJ EQ
category: filters_eq
subcategory: eq
id: filters_eq_zone_62_dj_eq
pages: 1
words: 506
source: ableton_dataset.jsonl
---
# Zone 62 DJ EQ

## Sound Character & Overview
> **Layman Description:** This is a professional DJ-style EQ Audio Effect Rack named 'Zone 62 DJ EQ'. It uses an Audio Effect Rack to group an Eq8 and a Limiter, allowing for macro-controlled frequency shaping (Low, Low Mid, Hi Mid, High) and a final safety limiter.

> **Emotional Vibe:** A precise and powerful DJ tool designed for seamless transitions and high-impact frequency control. This rack gives you instant access to the most critical tonal zones, ensuring your mix stays clean, punchy, and perfectly balanced even at high volumes.

## Technical Architecture & Signal Chain
An Ableton Live Audio Effect Rack (ADG) containing a single branch named 'EQ'. The rack features 8 active Macro Controls mapped to EQ parameters. The signal chain within the 'EQ' branch consists of an Eq8 followed by a Limiter. The Eq8 is configured with multiple active bands for surgical and musical frequency shaping, and the Limiter provides peak control with a -0.3dB ceiling.

## Chain of Thought Sound Design Breakdown
1. **Identify Root Device**: The preset is a `GroupDevicePreset` (Audio Effect Rack) named 'Zone 62 DJ EQ'.
2. **Analyze Macro Controls**: There are 16 macros. Macros 0-7 are mapped to specific names and values. Macros 8-15 are unassigned.
   - Macro 0: 'Low' (Value: 63.5)
   - Macro 1: 'Low Mid' (Value: 63.5)
   - Macro 2: 'Hi Mid' (Value: 63.5)
   - Macro 3: 'Hi' (Value: 63.5)
   - Macro 4: 'Lo Freq 51' (Value: 51)
   - Macro 5: 'LM Freq 41.5' (Value: 41.5)
   - Macro 6: 'HM Freq 67.5' (Value: 67.5)
   - Macro 7: 'Hii Freq 94' (Value: 94)
3. **Analyze Branches**: There is one branch named 'EQ'.
4. **Analyze Branch Devices (Chain)**:
   - **Device 1: Eq8**
     - Band 0, Param A: Mode 2 (Low Shelf), Freq: 424.38 Hz, Gain: 0 dB, Q: 2.82
     - Band 0, Param B: Mode 3 (Bell), Freq: 100.00 Hz, Gain: 0 dB, Q: 0.71
     - Band 1, Param A: Mode 3 (Bell), Freq: 259.07 Hz, Gain: 0 dB, Q: 1.52
     - Band 1, Param B: Mode 3 (Bell), Freq: 500.00 Hz, Gain: 0 dB, Q: 0.71
     - Band 2, Param A: Mode 3 (Bell), Freq: 1000.04 Hz, Gain: 0 dB, Q: 1.05
     - Band 2, Param B: Mode 3 (Bell), Freq: 2000.00 Hz, Gain: 0 dB, Q: 0.71
     - Band 3, Param A: Mode 5 (High Shelf), Freq: 3961.83 Hz, Gain: 0 dB, Q: 1.34
     - Band 3, Param B: Mode 3 (Bell), Freq: 10000.01 Hz, Gain: 0 dB, Q: 0.71
     - Spectrum Analyzer: On.
   - **Device 2: Limiter**
     - Gain: 0 dB
     - Ceiling: -0.3 dB
     - Release: 58 ms
     - Auto Release: Off
     - Link Channels: On
5. **Synthesize Final Report**: Organize by Rack -> Macros -> Branch -> Devices/Parameters.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Zone 62 DJ EQ
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Zone 62 DJ EQ"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_zone_62_dj_eq.xml` (102,337 bytes).
