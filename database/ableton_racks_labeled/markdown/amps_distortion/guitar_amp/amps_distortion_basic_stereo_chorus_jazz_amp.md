---
title: Basic Stereo Chorus Jazz Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_basic_stereo_chorus_jazz_amp
pages: 1
words: 287
source: ableton_dataset.jsonl
---
# Basic Stereo Chorus Jazz Amp

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Basic Stereo Chorus Jazz Amp'. It is designed as a complex guitar/instrument signal chain, specifically utilizing a 'Wet' branch that contains a series of amp simulation, modulation, and spatial effects.

> **Emotional Vibe:** This preset provides a lush, polished, and highly controlled jazz-style tone. It combines the grit of an amp with deep, shimmering chorus and high-end hall reverb, all held in check by precise dynamics processing for a professional studio sound.

## Technical Architecture & Signal Chain
The preset is an Ableton Live 11 Audio Effect Rack. The primary signal path is contained within a single branch named 'Wet'. It follows a serial processing chain: Gate -> Compressor -> Pedal -> Amp -> Chorus-Ensemble -> Hybrid Reverb -> Cabinet -> Limiter.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack ('Basic Stereo Chorus Jazz Amp').
2. Identify Branching: Only one branch 'Wet' is populated with devices.
3. Trace Device Chain (Serial): Gate -> Compressor2 -> Pedal -> Amp -> Chorus2 -> Hybrid -> Cabinet -> Limiter.
4. Extract Parameters per device: Iterate through each <AbletonDevicePreset> and its child <Device> tags.
5. Map Macros: Extract MacroDisplayNames and their corresponding Manual values from the Default snapshot.
6. Identify Snapshots: Note the existence of 'Clean Jazz', 'Dirty Rhythm', 'Deep Chorus', and 'Discipline' snapshots for tonal variety.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Basic Stereo Chorus Jazz Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Basic Stereo Chorus Jazz Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_basic_stereo_chorus_jazz_amp.xml` (108,658 bytes).
