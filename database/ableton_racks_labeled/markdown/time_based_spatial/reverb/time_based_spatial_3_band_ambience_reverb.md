---
title: 3 Band Ambience Reverb
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_3_band_ambience_reverb
pages: 1
words: 344
source: ableton_dataset.jsonl
---
# 3 Band Ambience Reverb

## Sound Character & Overview
> **Layman Description:** This is a sophisticated 3-band parallel reverb rack. It splits the audio into Low, Mid, and High frequency bands using EQ Three devices, processes each band with its own Reverb settings, and then recombines them. This allows for independent control over the decay and wet/dry mix of different frequency ranges (e.g., a long tail on the lows but a short, tight reverb on the highs).

> **Emotional Vibe:** A massive, cinematic space maker that allows you to sculpt the 'weight' of your reverb. You can create deep, sub-heavy ambient washes or bright, shimmering tails without muddying up your mix.

## Technical Architecture & Signal Chain
An Audio Effect Group utilizing an Audio Effect Rack with three parallel branches (Lo, Mid, High) for frequency-dependent spatial processing. Each branch contains an EQ Three for band isolation and a Reverb device for independent time/texture control, followed by a Branch Mixer.

## Chain of Thought Sound Design Breakdown
1. Identify Group: It is an Audio Effect Group named '3 Band Ambience Reverb'. 2. Identify Macro Structure: There are 8 macros controlling Decay (Lo/Mid/Hi), Width, Dry/Wet (Lo/Mid/Hi), and Rack Volume. 3. Identify Routing: The preset uses 'AudioEffectBranchPreset', meaning it is a parallel rack with three branches: Lo, Mid, and High. 4. Analyze Branch 'Lo': Uses EQ Three as a Low-Pass filter (FreqLo: 100Hz, FreqHi: 2500Hz, LowOn: true) followed by Reverb (Decay: ~4.1s). 5. Analyze Branch 'Mid': Uses EQ Three as a Band-Pass filter (FreqLo: 84Hz, FreqHi: 2500Hz, MidOn: true) followed by Reverb (Decay: ~1.7s). 6. Analyze Branch 'High': Uses EQ Three as a Band-Pass filter (FreqLo: 250Hz, FreqHi: 18kHz, MidOn: true) followed by Reverb (Decay: ~1.6s). 7. Note Snapshots: Includes 'High Shimmer', 'Low & Subtle', and 'Small Dull Room'.

## Live Actions Blueprint
```python
# Live Actions device chain reference for 3 Band Ambience Reverb
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "3 Band Ambience Reverb"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_3_band_ambience_reverb.xml` (137,402 bytes).
