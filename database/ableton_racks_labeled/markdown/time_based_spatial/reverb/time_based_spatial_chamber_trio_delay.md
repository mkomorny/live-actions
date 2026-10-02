---
title: Chamber Trio Delay
category: time_based_spatial
subcategory: reverb
id: time_based_spatial_chamber_trio_delay
pages: 1
words: 234
source: ableton_dataset.jsonl
---
# Chamber Trio Delay

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack named 'Chamber Trio Delay'. It uses Ableton's 'Chain Selector' to switch between four distinct signal paths (Branches): two pitch-shifting/resonating delay paths, one heavy reverb path, and one completely dry path. The preset is designed for 'quirky auto-harmonization' using Grain Delay and Resonators.

> **Emotional Vibe:** A haunting, shimmering, and unpredictable soundscape that can transform a simple input into a lush, harmonized cathedral of echoes or a chaotic, metallic glitch texture.

## Technical Architecture & Signal Chain
An Audio Effect Rack containing four branches with complex modulation via macro controls. It utilizes Grain Delay and Resonator devices in parallel within the first two branches to create pitch-shifted textures, followed by a high-density Reverb branch. The rack is designed for rapid timbre/pitch shifting via the Chain Selector.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will break this down by its four branches (0-3), identifying the devices in each and their specific parameter settings, then list the Macro mapping which is critical for usability.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Chamber Trio Delay
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Chamber Trio Delay"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_chamber_trio_delay.xml` (100,713 bytes).
