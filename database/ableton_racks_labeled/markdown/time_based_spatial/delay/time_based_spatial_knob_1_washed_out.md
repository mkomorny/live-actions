---
title: Knob 1 Washed Out
category: time_based_spatial
subcategory: delay
id: time_based_spatial_knob_1_washed_out
pages: 1
words: 258
source: ableton_dataset.jsonl
---
# Knob 1 Washed Out

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Knob 1 Washed Out'. It uses a parallel processing structure with two main branches: an 'EFX' branch containing a heavy modulation and delay chain, and a 'Dry' branch for the unprocessed signal. The rack is designed for performance/DJ use, featuring 8 mapped macro controls to manipulate the 'washed out' texture.

> **Emotional Vibe:** A lush, psychedelic, and highly textured effect rack. It combines swirling phaser movements with rhythmic delays and multi-band filter sweeps, all glued together by a compressor. Perfect for transforming clean sounds into 'washed out', dreamy, and cinematic soundscapes.

## Technical Architecture & Signal Chain
Audio Effect Rack (ADG) with two branches: [EFX] and [Dry]. The EFX branch utilizes a serial chain of Phaser, Delay, FilterDelay, and Compressor2. Macro mapping is heavily utilized for real-time timbre and spatial manipulation.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack. I will break this down by its two branches: EFX (the effect chain) and Dry (the bypass/clean chain). Within the EFX branch, there is a serial signal path of four devices. For each device, I will extract the specific parameter settings found in the <Manual> tags.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Knob 1 Washed Out
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Knob 1 Washed Out"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_knob_1_washed_out.xml` (76,129 bytes).
