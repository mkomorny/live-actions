---
title: Drum Cassette
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_drum_cassette
pages: 1
words: 323
source: ableton_dataset.jsonl
---
# Drum Cassette

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack designed for lo-fi drum processing, likely intended to emulate the character of an old cassette tape (as indicated by the name 'Drum Cassette'). It uses a combination of rhythmic shaping, bit-crushing, tonal sculpting, and movement via phasing/flanging.

> **Emotional Vibe:** The sound is gritty, unstable, and vintage. It provides a sense of 'broken' hardware, rhythmic jitter, and tape-like pitch warble, perfect for adding character and 'dust' to clean drum samples.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack containing a single serial chain of five devices. The signal path consists of a custom Max for Live Shaper, followed by Redux (bit-reduction), Channel EQ (tonal shaping), Erosion (noise/grit), and finally a Phaser-Flanger (modulation). It features 6 macro controls mapped to various parameters across the chain.

## Chain of Thought Sound Design Breakdown
1. Identify the Rack: Name is 'Drum Cassette', created by Huston Singletary. 2. Analyze Device 1 (Shaper): It's a Max for Live device ('Cutoff Filter Shaper 2'). Parameters are set to high depth, specific sync rates, and jitter. 3. Analyze Device 2 (Redux): Bit depth is reduced to 6-bit, sample rate is lowered significantly (~7.7kHz), creating digital grit. 4. Analyze Device 3 (Channel EQ): Used for additive/subtractive EQ with a mid-boost around 2.4kHz and slight gain increase. 5. Analyze Device 4 (Erosion): Set to high frequency (14.5kHz) and amplitude, adding high-end 'hiss' or 'sand'. 6. Analyze Device 5 (Phaser/Flanger): High feedback (~70%) and modulation amount (~98%), creating a heavy 'wow and flutter' effect. 7. Map Macros: Identified the macro names and their default values.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Drum Cassette
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Drum Cassette"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_drum_cassette.xml` (81,075 bytes).
