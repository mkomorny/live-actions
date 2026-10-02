---
title: Creative Synth Buss
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_creative_synth_buss
pages: 1
words: 169
source: ableton_dataset.jsonl
---
# Creative Synth Buss

## Sound Character & Overview
> **Layman Description:** Creative Synth Buss

> **Emotional Vibe:** Modulation & Rhythmic / Creative Synth Buss

## Technical Architecture & Signal Chain
Audio Effect Rack (ADG)

## Chain of Thought Sound Design Breakdown
The user provided an Ableton XML preset. I need to parse the <BranchPresets> section to find the actual device chain and then extract the parameter values for each device within that chain. The rack is named 'Creative Synth Buss' and contains 8 macro controls mapped to specific functions like Filter Cutoff, Tube Warmth, and Comp. The signal flow follows a serial path through several Ableton devices: Auto Filter -> Chorus-Ensemble -> Dynamic Tube -> Glue Compressor -> Auto Pan -> Limiter.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Creative Synth Buss
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Creative Synth Buss"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_creative_synth_buss.xml` (79,561 bytes).
