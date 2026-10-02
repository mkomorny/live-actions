---
title: Sweep Overdrive
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_sweep_overdrive
pages: 1
words: 171
source: ableton_dataset.jsonl
---
# Sweep Overdrive

## Sound Character & Overview
> **Layman Description:** Sweep Overdrive

> **Emotional Vibe:** A gritty, evolving, and expansive texture that moves from tight, distorted aggression to wide, washed-out ambient sweeps.

## Technical Architecture & Signal Chain
Effect Rack with Amp for a raw edge, Auto Filter provides sweep, complemented by Chorus, Ping Pong Delay and Reverb.

## Chain of Thought Sound Design Breakdown
The preset is an Audio Effect Rack containing two distinct branches: 'Sweep OD' (the main effect chain) and 'Dry' (a pass-through). The 'Sweep OD' chain uses a serial processing order of Amp -> Auto Filter -> Chorus -> Ping Pong Delay -> Reverb -> Limiter. It features 8 macro controls for high-level performance and 4 snapshots for rapid tonal shifts.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Sweep Overdrive
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Sweep Overdrive"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_sweep_overdrive.xml` (92,860 bytes).
