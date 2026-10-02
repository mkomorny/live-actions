---
title: Knob 1 Fade to Grey
category: time_based_spatial
subcategory: delay
id: time_based_spatial_knob_1_fade_to_grey
pages: 1
words: 275
source: ableton_dataset.jsonl
---
# Knob 1 Fade to Grey

## Sound Character & Overview
> **Layman Description:** This is a single-macro Audio Effect Rack designed for performance, specifically to transition from a dry signal into a filtered, ping-pong delay effect.

> **Emotional Vibe:** A smooth, cinematic transition tool that allows you to wash out a sound into a dark, rhythmic space with a single movement.

## Technical Architecture & Signal Chain
An Ableton Live Audio Effect Rack containing a serial chain of an EQ Three and a Ping Pong Delay. The rack features a single visible macro named 'Fade' intended to automate the engagement and wetness of the delay chain.

## Chain of Thought Sound Design Breakdown
The XML defines an Audio Effect Rack ('Knob 1 Fade to Grey'). The device chain consists of two devices: EQ Three and Ping Pong Delay. The 'On' state for the Delay is currently false, and its Dry/Wet is at 0, meaning the effect is currently bypassed/dry. The annotation reveals that Macro 1 ('Fade') controls the transition from dry to an EQ'd delay tail. This implies the macro maps to the 'Device On' parameter of the delay and/or its 'Dry/Wet' parameter, while potentially modulating the EQ Three parameters to create a 'fading to grey' (darkening) effect as the delay engages.

### Mapped Macro Controls
- **Macro 1:** `'Fade'`

## Live Actions Blueprint
```python
# Live Actions device chain reference for Knob 1 Fade to Grey
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Knob 1 Fade to Grey"},
    {"name": "Macro 1 ('Fade')", "value": 64},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_knob_1_fade_to_grey.xml` (38,722 bytes).
