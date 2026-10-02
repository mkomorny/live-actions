---
title: Major Wah
category: modulation
subcategory: lfo_modulation
id: modulation_major_wah
pages: 1
words: 272
source: ableton_dataset.jsonl
---
# Major Wah

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Major Wah', designed specifically for heavy wah-wah processing on bass instruments. It uses a parallel processing structure (Wet/Dry branches) to allow for heavy tonal shaping while maintaining signal integrity.

> **Emotional Vibe:** A massive, growling bass wah effect that can shift from subtle rhythmic movement to aggressive, filtered sweeps with heavy body and resonance.

## Technical Architecture & Signal Chain
The preset is an Ableton Audio Effect Rack (ADG) utilizing two parallel branches: a 'Wet' branch containing a complex serial chain of dynamics, filtering, and equalization, and a 'Dry' branch which serves as a direct signal path. The rack features 8 user-defined Macro controls and 4 custom Snapshots for rapid tonal morphing.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It's a GroupDevicePreset (Audio Effect Rack). 2. Check branches: Found 'Wet' branch (Id=0) and 'Dry' branch (Id=1). 3. Analyze Wet Branch: Contains Compressor2, AutoFilter, and Eq8 in series. 4. Analyze Dry Branch: Empty device list (direct signal). 5. Extract parameters for each device: Compressor (Threshold, Ratio, etc.), AutoFilter (Cutoff, Resonance, LFO), Eq8 (Band frequencies/gains). 6. Identify Macros: Mapping the MacroDisplayNames to their Manual values. 7. Identify Snapshots: Extracting names and macro values for 'Wah Wah', 'Add Body', and 'Subtle Drift'. 8. Compile into a structured report.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Major Wah
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Major Wah"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_major_wah.xml` (94,683 bytes).
