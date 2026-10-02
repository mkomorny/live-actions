---
title: Ducker
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_ducker
pages: 1
words: 200
source: ableton_dataset.jsonl
---
# Ducker

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Ducker' designed for rhythmic volume modulation (ducking). It uses a Shaper device to create a rhythmic pulse, followed by a Utility device to ensure signal integrity.

> **Emotional Vibe:** A precise, rhythmic tool that breathes life into your tracks by creating controlled, pulsing movement through synchronized volume ducking.

## Technical Architecture & Signal Chain
An Audio Effect Rack containing a single chain. The rack utilizes macro mapping to control the intensity and timing of a Shaper-based ducking effect. It includes snapshots for varying rhythmic subdivisions (from 1/2 to 1/64).

## Chain of Thought Sound Design Breakdown
The XML represents an Audio Effect Rack ('Ducker'). I will first identify the macro controls, then traverse the device chain within the branch to extract specific parameters for each device (Shaper and Utility), and finally list the macro snapshots provided in the preset.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Ducker
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Ducker"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_ducker.xml` (54,626 bytes).
