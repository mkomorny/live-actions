---
title: 3-Way Split Vocoder Rack
category: vocal_processing
subcategory: vocoder
id: vocal_processing_3_way_split_vocoder_rack
pages: 1
words: 309
source: ableton_dataset.jsonl
---
# 3-Way Split Vocoder Rack

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack designed for a '3-Way Split' vocoder effect. It uses parallel processing to split the signal into three distinct frequency bands (Low, Mid, and High), applying a Vocoder to each band separately before summing them back together. There is also a fourth chain containing an EQ Eight for tonal shaping.

> **Emotional Vibe:** An advanced spectral vocoder rack that splits audio into three frequency-specific paths (Low, Mid, High) and processes each via a Vocoder with varying filter bank settings. Includes a fourth parallel EQ Eight chain for final frequency sculpting.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing four parallel chains. Chains 0-2 implement a frequency-split vocoding architecture where the signal is divided into Low (100Hz-500Hz), Mid (500Hz-2kHz), and High (2kHz-18kHz) bands using the Vocoder's internal filter bank. Chain 3 provides an EQ Eight for additive/subtractive tonal control.

## Chain of Thought Sound Design Breakdown
The XML reveals an Audio Effect Rack containing 4 branches (parallel chains). Chain 0, 1, and 2 are 'Utility -> Vocoder' setups. By analyzing the LowFrequency and HighFrequency parameters of the Vocoders, we see a clear frequency split: Chain 2 is low-end (~100Hz-500Hz), Chain 1 is mid-range (~500Hz-2kHz), and Chain 0 is high-end (~2kHz-18kHz). This confirms it is a multi-band vocoder. Chain 3 contains an EQ Eight with several bands active for frequency shaping. Each chain ends with an Audio Branch Mixer to control the level of that specific band in the mix.

## Live Actions Blueprint
```python
# Live Actions device chain reference for 3-Way Split Vocoder Rack
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "3-Way Split Vocoder Rack"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/vocal_processing_3_way_split_vocoder_rack.xml` (138,145 bytes).
