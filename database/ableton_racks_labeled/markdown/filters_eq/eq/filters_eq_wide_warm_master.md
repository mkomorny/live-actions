---
title: Wide & Warm Master
category: filters_eq
subcategory: eq
id: filters_eq_wide_warm_master
pages: 1
words: 319
source: ableton_dataset.jsonl
---
# Wide & Warm Master

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Wide & Warm Master'. It uses parallel processing (Branches) to create a 'Wet' signal path, which contains an EQ Eight, a Compressor, and a Limiter. The rack is highly optimized for mastering with 8 custom Macro controls that allow for quick adjustments to Bass/Mid/High gains, Compression threshold/gain, and Limiter gain.

> **Emotional Vibe:** A professional-grade mastering tool designed to add 'width' and 'warmth' to a mix. It provides surgical EQ control, smooth classical-style compression, and a transparent limiter, all controllable via a single macro interface for seamless performance.

## Technical Architecture & Signal Chain
Audio Effect Rack (ADG) utilizing parallel branching. Signal path: [Input] -> [Wet Branch] -> [EQ Eight] -> [Compressor] -> [Limiter] -> [Output]. The rack features 8 mapped Macro controls and 5 custom Snapshots for tonal shaping and dynamic control.

## Chain of Thought Sound Design Breakdown
1. Identify Root: GroupDevicePreset (Audio Effect Rack). 2. Analyze Structure: The device uses 'Branches'. Specifically, there is one branch named 'Wet'. 3. Deconstruct 'Wet' Branch: It contains three devices in series: EQ Eight -> Compressor -> Limiter. 4. Extract EQ Eight Params: Multiband setup with specific active bands (Low Pass at ~70Hz, Low Pass at ~1500Hz/2500Hz, and High Pass/Boosts). 5. Extract Compressor Params: Uses 'Classical Compression' preset; Ratio 1.5:1, Attack 10ms, Release 100ms, Knee 6. 6. Extract Limiter Params: Ceiling -0.3dB, Lookahead 2ms. 7. Analyze Macros: Map the MacroDisplayNames to their values (Bass Gain, Mid Gain, etc.). 8. Analyze Snapshots: Identify tonal variations (Wide Low Mids, High Boost, Light/Heavy Comp).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Wide & Warm Master
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Wide & Warm Master"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_wide_warm_master.xml` (84,117 bytes).
