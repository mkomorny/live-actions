---
title: Wah Pedal
category: modulation
subcategory: lfo_modulation
id: modulation_wah_pedal
pages: 1
words: 525
source: ableton_dataset.jsonl
---
# Wah Pedal

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Wah Pedal' created by Philipp Lange. It uses a parallel processing structure with two branches: a 'Wet' branch containing an Auto Filter and a Pedal, and a 'Dry' branch which acts as a low-volume parallel path.

> **Emotional Vibe:** This 'Wah Pedal' preset offers everything from clean, slow sweeps to aggressive, dirty, and fast rhythmic textures. It’s designed for expressive performance, allowing you to morph between subtle filtering and heavy, driven pedal effects with ease.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) utilizing a dual-branch architecture. The Wet branch contains a serial chain of an Auto Filter and a Pedal device, followed by a branch mixer with a gain boost (~1.26). The Dry branch contains only a branch mixer with attenuated volume (~0.20). Macro controls are mapped to key parameters across both branches.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (ADG) named 'Wah Pedal'. 

1. **Macro Controls Mapping**: The rack exposes 6 primary macros:
   - Macro 0: Heel to Toe
   - Macro 1: Auto Speed
   - Macro 2: Auto Amount
   - Macro 3: Env Amount
   - Macro 4: Drive
   - Macro 5: Dry Signal

2. **Signal Flow (Branches)**:
   - **Wet Branch**: Contains a serial chain of [Auto Filter] -> [Pedal]. 
     - The Wet branch mixer has a volume of ~1.26.
   - **Dry Branch**: Contains no devices, only a branch mixer with a volume of ~0.20 (acting as a parallel dry path).

3. **Device Analysis - Auto Filter (Wet Branch)**:
   - Filter Type: Value 2 (likely Low Pass/Band Pass based on typical mapping)
   - Circuit LPF/HPF: Value 2
   - Cutoff: 62.37
   - Resonance: 0.49
   - Drive: 7
   - ModHub: 127 (Maxed)
   - Attack: 10.30
   - Release: 114.36
   - LFO Frequency: 1.13 Hz
   - LFO Rate Type: Sync/Tempo (Value 1)
   - LFO Beat Rate: 13

4. **Device Analysis - Pedal (Wet Branch)**:
   - Gain: 0.05
   - Output: 0
   - Bass/Mid/Treble: All at 0 (Flat EQ)
   - MidFreq: 1
   - Dry/Wet: 0.05 (Very low wetness, suggesting the 'Wah' effect is heavily blended via the rack structure or intended to be driven by the filter).

5. **Snapshots (Macro Variations)**:
   - Clean Slow: Low heel-to-toe, slow speed.
   - Dirty Fast: High drive, high speed, high amount.
   - Fixed: Static settings for a non-moving wah effect.
   - Auto Only: Focuses on LFO modulation.
   - Env Only: Focuses on Envelope Follower modulation.

### Mapped Macro Controls
- **Macro 1:** `Heel to Toe`
- **Macro 2:** `Auto Speed`
- **Macro 3:** `Auto Amount`
- **Macro 4:** `Env Amount`
- **Macro 5:** `Drive`
- **Macro 6:** `Dry Signal`

## Live Actions Blueprint
```python
# Live Actions device chain reference for Wah Pedal
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Wah Pedal"},
    {"name": "Macro 1 (Heel to Toe)", "value": 64},
    {"name": "Macro 2 (Auto Speed)", "value": 64},
    {"name": "Macro 3 (Auto Amount)", "value": 64},
    {"name": "Macro 4 (Env Amount)", "value": 64},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_wah_pedal.xml` (51,508 bytes).
