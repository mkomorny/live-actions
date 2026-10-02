---
title: 4 VOCODER
category: vocal_processing
subcategory: vocoder
id: vocal_processing_4_vocoder
pages: 1
words: 255
source: ableton_dataset.jsonl
---
# 4 VOCODER

## Sound Character & Overview
> **Layman Description:** This is a multi-band parallel vocoder rack designed to split the frequency spectrum into four distinct zones, each with its own vocoder resolution and frequency range.

> **Emotional Vibe:** A massive, wide, and complex vocal texture that shifts from deep, subby growls in the lows to shimmering, airy robotic textures in the highs.

## Technical Architecture & Signal Chain
Audio Effect Rack: '4 VOCODER' containing 4 parallel branches of the Ableton Vocoder device. The rack utilizes a multi-band approach by assigning different frequency ranges and band counts to each branch, effectively creating a frequency-split vocoder effect.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack with 4 branches. Each branch contains a Vocoder device and its own mixer settings. The core design strategy is frequency splitting: Branch 0 handles low frequencies (30-500Hz), Branch 1 mid-low (500-1kHz), Branch 2 mid-high (1k-2kHz), and Branch 3 high/air (2k-18kHz). Crucially, the 'BandCount' varies per branch (1, 2, 3, and 9 bands respectively), meaning the low end is a single-band sub-vocoder while the high end has much higher spectral resolution. This is a sophisticated way to build a thick, multi-octave vocoded sound without phase issues or muddying the mid-range.

## Live Actions Blueprint
```python
# Live Actions device chain reference for 4 VOCODER
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "4 VOCODER"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/vocal_processing_4_vocoder.xml` (94,800 bytes).
