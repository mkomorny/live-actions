---
title: Filter Pumper
category: modulation
subcategory: lfo_modulation
id: modulation_filter_pumper
pages: 1
words: 424
source: ableton_dataset.jsonl
---
# Filter Pumper

## Sound Character & Overview
> **Layman Description:** This XML represents an Ableton Live Audio Effect Rack named 'Filter Pumper'. It is a parallel processing rack designed to create rhythmic, pumping filter effects by splitting the signal into a 'Wet' branch (heavily processed) and a 'Dry' branch (unprocessed).

> **Emotional Vibe:** A high-energy EDM/Techno effect rack designed for rhythmic 'pumping' and 'wobble' textures. It uses heavy compression and LFO-driven filtering to create a sidechain-like ducking sensation even without an external trigger.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing two main branches. The 'Wet' branch contains a serial chain of Compressor, Auto Filter, Utility, and Limiter. The 'Dry' branch is empty, acting as a parallel dry path. Macro controls are mapped to key parameters including Filter Frequency, Resonance, Drive, LFO Rate, and a 'Pump' control (likely mapping to compressor/filter interaction).

## Chain of Thought Sound Design Breakdown
1. Identify the root: Audio Effect Rack ('Filter Pumper').
2. Analyze Branches: Found two branches: 'Wet' (ID 0) and 'Dry' (ID 1).
3. Analyze 'Wet' Branch Devices:
   - Device 0: Compressor (Compressor2). Parameters: Threshold (~0.03dB), Ratio (~7.47:1), Attack (2ms), Release (50ms), Gain (-10.39dB), Dry/Wet (100%).
   - Device 1: Auto Filter. Parameters: Cutoff (87.76Hz), Resonance (0.6), Drive (18.9dB), LFO On (True), LFO Rate (Sync, 9th note/division), Attack (8.88ms), Release (111.18ms).
   - Device 2: Utility (StereoGain). Parameters: Mid-Side Balance (On), Gain (approx -4.08dB via legacy gain).
   - Device 3: Limiter. Parameters: Ceiling (-0.3dB), Release (300ms), Auto Release (On).
4. Analyze 'Dry' Branch Devices: Empty.
5. Identify Macro Controls:
   - Macro 0: Filter Freq
   - Macro 1: Filter Reso
   - Macro 2: Filter Env
   - Macro 3: Filter Drive
   - Macro 4: LFO Amount
   - Macro 5: LFO Rate
   - Macro 6: Pump
   - Macro 7: Rack Dry/Wet
6. Synthesize the signal flow and purpose.

### Mapped Macro Controls
- **Macro 1:** `Filter Freq`
- **Macro 2:** `Filter Reso`
- **Macro 3:** `Filter Env`
- **Macro 4:** `Filter Drive`
- **Macro 5:** `LFO Amount`
- **Macro 6:** `LFO Rate`
- **Macro 7:** `Pump`
- **Macro 8:** `Rack Dry/Wet`

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filter Pumper
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filter Pumper"},
    {"name": "Macro 1 (Filter Freq)", "value": 64},
    {"name": "Macro 2 (Filter Reso)", "value": 64},
    {"name": "Macro 3 (Filter Env)", "value": 64},
    {"name": "Macro 4 (Filter Drive)", "value": 64},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_filter_pumper.xml` (63,959 bytes).
