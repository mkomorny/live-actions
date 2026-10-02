---
title: Slap Bass Amp
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_slap_bass_amp
pages: 1
words: 207
source: ableton_dataset.jsonl
---
# Slap Bass Amp

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Slap Bass Amp'. It is designed for bass guitar processing, utilizing a serial chain of compression, amp simulation, and cabinet emulation.

> **Emotional Vibe:** This preset provides a punchy, controlled, and bright slap bass tone, combining heavy compression for sustain with a high-treble amp character.

## Technical Architecture & Signal Chain
The preset is an Ableton Audio Effect Rack containing a single device chain. The signal flow follows a standard bass processing topology: Compressor2 -> Amp (Bass Roundup) -> Cabinet (4x10 Bass Cab).

## Chain of Thought Sound Design Breakdown
The XML structure reveals an Audio Effect Rack ('Slap Bass Amp'). Inside the first branch (Chain 1), there are three distinct devices: a Compressor2, an Amp, and a Cabinet. I will extract the specific 'Manual' parameter values for each device and then list the Macro control settings defined at the rack level.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Slap Bass Amp
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Slap Bass Amp"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_slap_bass_amp.xml` (48,547 bytes).
