---
title: MultiComp & EQ Three
category: filters_eq
subcategory: filter
id: filters_eq_multicomp_eq_three
pages: 1
words: 260
source: ableton_dataset.jsonl
---
# MultiComp & EQ Three

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack designed for parallel multiband compression and tonal shaping. It uses four parallel chains (three 'Wet' branches and one 'Dry' branch) to allow frequency-specific processing, specifically targeting Bass, Mid, and High frequencies independently.

> **Emotional Vibe:** This is a powerful mixing tool for adding 'glue' and character to a drum bus or mix buss. It allows you to surgically add 'Boom', 'Snap', or 'Sizzle' without destroying the transients of the original signal by using parallel saturation and compression.

## Technical Architecture & Signal Chain
The preset is a Group Device containing an Audio Effect Rack with three active parallel branches ('Wet 1', 'Wet 2', 'Wet 3') and one bypass/dry branch ('Dry'). Each wet branch follows a serial signal path of FilterEQ3 $\rightarrow$ Compressor2 $\rightarrow$ StereoGain, followed by a branch mixer. This architecture facilitates frequency-dependent dynamic control (multiband compression) via parallel processing.

## Chain of Thought Sound Design Breakdown
The XML structure reveals an Audio Effect Rack with 4 branches. Branch 0 (Wet 1) targets Lows; Branch 1 (Wet 2) targets Mids/Highs; Branch 2 (Wet 3) targets Highs. The macro controls suggest a highly tactile way to blend these frequency-specific compression/EQ settings into the main signal.

## Live Actions Blueprint
```python
# Live Actions device chain reference for MultiComp & EQ Three
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "MultiComp & EQ Three"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_multicomp_eq_three.xml` (115,020 bytes).
