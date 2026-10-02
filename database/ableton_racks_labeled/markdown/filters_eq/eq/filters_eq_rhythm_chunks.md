---
title: Rhythm Chunks
category: filters_eq
subcategory: eq
id: filters_eq_rhythm_chunks
pages: 1
words: 233
source: ableton_dataset.jsonl
---
# Rhythm Chunks

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Rhythm Chunks' created by Huston Singletary. It is designed as an Amp Simulation chain, likely for heavily processed rhythmic guitar or percussion, featuring a serial signal chain of Gate -> Amp -> Drum Buss -> EQ Three -> Pedal -> Limiter.

> **Emotional Vibe:** Analyze the signal flow of the 'Rhythm Chunks' Ableton Rack. Identify the specific settings for the Gate, Amp (Rhodes 2 way), Drum Buss, EQ Three, Pedal, and Limiter devices to reconstruct this exact tone.

## Technical Architecture & Signal Chain
Analyze the following Ableton Live 11.3 Audio Effect Rack: 'Rhythm Chunks'. The rack utilizes a single branch containing a complex serial processing chain including dynamic control, amp simulation, drum enhancement, tonal shaping, and final limiting.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack ('Rhythm Chunks') with a single branch containing six devices in series. The macro controls are mapped to specific parameters across these devices, allowing for high-level control over timbre (Treble, Presence), saturation (Drive), and dynamics (Pressure, Gate Intensity).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Rhythm Chunks
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Rhythm Chunks"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/filters_eq_rhythm_chunks.xml` (63,603 bytes).
