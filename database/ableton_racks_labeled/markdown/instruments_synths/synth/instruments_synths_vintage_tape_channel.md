---
title: Vintage Tape Channel
category: instruments_synths
subcategory: synth
id: instruments_synths_vintage_tape_channel
pages: 1
words: 133
source: ableton_dataset.jsonl
---
# Vintage Tape Channel

## Sound Character & Overview
> **Layman Description:** Analyze Ableton XML

> **Emotional Vibe:** Professional and Detailed

## Technical Architecture & Signal Chain
Expert Sound Designer/Audio Engineer Analysis

## Chain of Thought Sound Design Breakdown
1. Identify the root device (Audio Effect Rack). 2. Extract Macro Control mappings to understand user intent. 3. Iterate through each Device in the chain within the BranchPresets. 4. Extract specific parameter values for every effect. 5. Synthesize a professional summary of the signal flow and sonic character.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Vintage Tape Channel
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Vintage Tape Channel"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/instruments_synths_vintage_tape_channel.xml` (126,400 bytes).
