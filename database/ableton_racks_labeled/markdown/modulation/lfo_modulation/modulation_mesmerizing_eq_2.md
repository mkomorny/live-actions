---
title: Mesmerizing EQ 2
category: modulation
subcategory: lfo_modulation
id: modulation_mesmerizing_eq_2
pages: 1
words: 217
source: ableton_dataset.jsonl
---
# Mesmerizing EQ 2

## Sound Character & Overview
> **Layman Description:** This is an Ableton Audio Effect Rack named 'Mesmerizing EQ 2'. It consists of a single chain containing three LFO devices followed by an EQ Eight device.

> **Emotional Vibe:** This rack uses three layers of LFO modulation to create complex movement, likely modulating the EQ parameters or other external targets, followed by a highly surgical EQ Eight with multiple active bands for frequency shaping.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) containing one branch. The signal chain follows a serial routing: LFO -> LFO -> LFO -> EQ Eight.

## Chain of Thought Sound Design Breakdown
1. Identify Rack Type: Audio Effect Rack (AudioEffectGroupDevice).
2. Identify Branching: One branch present (Branch 0).
3. Trace Device Chain: 
   - Device 0: LFO (Built-in)
   - Device 1: LFO (Built-in)
   - Device 2: LFO (Built-in)
   - Device 3: EQ Eight (Built-in)
4. Extract Parameters for each device.
5. Note specific manual values vs default values.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Mesmerizing EQ 2
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Mesmerizing EQ 2"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_mesmerizing_eq_2.xml` (113,830 bytes).
