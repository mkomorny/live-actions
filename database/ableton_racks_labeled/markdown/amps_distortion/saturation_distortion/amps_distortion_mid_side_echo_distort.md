---
title: Mid_Side Echo Distort
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_mid_side_echo_distort
pages: 1
words: 265
source: ableton_dataset.jsonl
---
# Mid_Side Echo Distort

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Mid_Side Echo Distort', created by Timo Preece. It uses a complex signal chain consisting of five different effects to create a textured, modulated, and distorted spatial effect.

> **Emotional Vibe:** A dark, rhythmic, and evolving spatial texture. It combines the lush, tape-like movement of a modulated delay with gritty distortion and controlled filtering, resulting in a sound that feels both cavernous and claustrophobic.

## Technical Architecture & Signal Chain
An Audio Effect Rack (ADG) containing a single processing chain. The rack features 8 macro controls mapped to specific parameters across the device chain: Filter Frequency, Filter Resonance, Distortion, Delay Amount, Delay L Rate, Delay R Rate, Delay Feedback, and an additional Macro 8. The signal path follows: Echo -> Pedal -> Auto Filter -> Glue Compressor -> Limiter.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (ADG). I will first identify the macro controls which define the user interface. Then, I will traverse the device chain within the branch to extract every individual effect and its specific parameter settings, including the 'Echo' preset used, the 'Pedal' mode, the 'Auto Filter' circuit type, and the compression/limiting stages at the end of the chain.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Mid_Side Echo Distort
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Mid_Side Echo Distort"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_mid_side_echo_distort.xml` (78,764 bytes).
