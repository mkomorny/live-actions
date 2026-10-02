---
title: Drum Noise Glitcher
category: vocal_processing
subcategory: vocoder
id: vocal_processing_drum_noise_glitcher
pages: 1
words: 237
source: ableton_dataset.jsonl
---
# Drum Noise Glitcher

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack named 'Drum Noise Glitcher' designed for drum processing. It uses a parallel structure with a clean 'Dry' path and a heavily processed 'Wet' path containing filtering, bit-crushing, spatialization, vocoding, and amp simulation.

> **Emotional Vibe:** A gritty, mechanical, and highly textured drum processor that can transform clean percussion into glitchy, lo-fi, and aggressive rhythmic textures with a single knob turn.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (AER) utilizing a dual-branch architecture. The Wet branch contains a serial chain of seven devices: Auto Filter, Auto Pan, Redux, Hybrid Reverb, Vocoder, Amp, and Limiter. It features 8 user-mapped Macro Controls and 5 custom Snapshots for rapid timbre modulation.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Group Device (Rack) with two branches: 'Dry' (empty/mixer only) and 'Wet'. The Wet branch contains a serial chain of 7 devices. I will now extract the specific parameters for each device in that chain, as well as the macro mapping and snapshots provided in the code.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Drum Noise Glitcher
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Drum Noise Glitcher"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/vocal_processing_drum_noise_glitcher.xml` (114,194 bytes).
