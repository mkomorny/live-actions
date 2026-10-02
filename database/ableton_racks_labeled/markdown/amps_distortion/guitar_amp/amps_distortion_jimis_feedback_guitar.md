---
title: Jimi's Feedback Guitar
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_jimis_feedback_guitar
pages: 1
words: 256
source: ableton_dataset.jsonl
---
# Jimi's Feedback Guitar

## Sound Character & Overview
> **Layman Description:** This preset is a complex guitar effect chain designed to simulate 'Jimi-style' feedback. It uses a combination of heavy amplification, cabinet simulation, and—most importantly—a Resonator device configured with multiple pitch-shifted oscillators to create the singing, harmonic ringing characteristic of controlled guitar feedback.

> **Emotional Vibe:** A wild, psychedelic, and singing guitar tone. It captures the controlled chaos of a vintage tube amp feedbacking in a room, ranging from smooth melodic ringing to aggressive, screaming high-gain textures.

## Technical Architecture & Signal Chain
An Audio Effect Group preset titled 'Jimi's Feedback Guitar'. The signal chain utilizes a branch structure containing an Amp -> Resonator -> Amp -> Cabinet sequence. The core character is driven by a Resonator with three active resonance modes (one at E2, one pitch-shifted -5 semitones, and one +12 semitones) to create harmonic feedback loops, followed by dual-stage amplification and cabinet emulation.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Group. I will break this down by identifying the macro controls first (which define user interaction), then the device chain within the branch, and finally the specific parameter settings for each device found in the 'DevicePresets' section of the XML code.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Jimi's Feedback Guitar
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Jimi's Feedback Guitar"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_jimis_feedback_guitar.xml` (61,799 bytes).
