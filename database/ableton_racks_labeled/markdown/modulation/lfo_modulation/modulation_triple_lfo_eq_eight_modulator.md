---
title: Triple LFO EQ Eight Modulator
category: modulation
subcategory: lfo_modulation
id: modulation_triple_lfo_eq_eight_modulator
pages: 1
words: 185
source: ableton_dataset.jsonl
---
# Triple LFO EQ Eight Modulator

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Group preset containing a single signal chain (Branch 0) consisting of three LFO devices in series, followed by an EQ Eight.

> **Emotional Vibe:** A complex modulation chain using three LFOs to create rhythmic movement, followed by a heavy multi-band EQ boost/cut structure.

## Technical Architecture & Signal Chain
Audio Effect Group | Branch 0: [LFO] -> [LFO] -> [LFO] -> [EQ Eight]

## Chain of Thought Sound Design Breakdown
The XML defines an AudioEffectGroupDevice. Inside 'BranchPresets', there is one branch (Id=0) containing four devices in a serial chain: three instances of the LFO device and one instance of EQ Eight. I will extract parameters for each device individually based on their specific 'AbletonDevicePreset' IDs within that branch.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Triple LFO EQ Eight Modulator
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Triple LFO EQ Eight Modulator"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_triple_lfo_eq_eight_modulator.xml` (122,144 bytes).
