---
title: Basic Heavy Guitar Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_heavy_guitar_amp
pages: 1
words: 264
source: ableton_dataset.jsonl
---
# Basic Heavy Guitar Amp

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack designed for heavy guitar tones, titled 'Basic Heavy Guitar Amp'. It uses a parallel processing structure with two main chains: a 'Wet' chain containing a Gate and an Amp, and a 'Cabinets' chain that allows for blending different cabinet/mic positions (Far vs. Near).

> **Emotional Vibe:** An expert-level heavy guitar rig featuring a gated amp signal and a parallel cabinet blend. Includes specific snapshots for 'Thrash', 'Old School', 'Midriff Punch', and 'Practice Room' styles.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) utilizing parallel branching. The signal path consists of a primary 'Wet' branch containing a Gate followed by an Amp, and a secondary 'Cabinets' rack branch that uses sub-branches to switch between different Cabinet settings via a Chain Selector.

## Chain of Thought Sound Design Breakdown
The XML structure reveals an Audio Effect Rack with two main branches (Wet and Cabinets). The Wet branch contains a Gate and an Amp. The Cabinets branch is itself a rack containing a Cabinet device with sub-branches for Far and Near mic positions. Macro controls are mapped to the primary amp and gate parameters, and there are several snapshots defined for different playing styles.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Heavy Guitar Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Heavy Guitar Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_heavy_guitar_amp.xml` (80,045 bytes).
