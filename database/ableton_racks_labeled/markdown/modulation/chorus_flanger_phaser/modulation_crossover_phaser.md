---
title: Crossover Phaser
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_crossover_phaser
pages: 1
words: 239
source: ableton_dataset.jsonl
---
# Crossover Phaser

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack named 'Crossover Phaser'. It uses a crossover technique to split audio into different frequency bands, applying heavy modulation (Phaser) only to the mid/high frequencies while keeping the bass clean. This prevents the low-end from becoming muddy or losing its punch.

> **Emotional Vibe:** A professional, surgical tool designed to add movement and character to your tracks without destroying your low-end stability. Perfect for basslines or rhythmic elements that need 'swirl' without losing their weight.

## Technical Architecture & Signal Chain
An Audio Effect Rack utilizing three parallel branches for frequency-dependent processing. Branch 0 acts as a Low-Pass filter (Bass), Branch 1 acts as a Band-Pass/High-Pass filter with a Phaser (Mids/Highs), and Branch 2 is a Dry bypass. The crossover point is controlled via the Chain Selector.

## Chain of Thought Sound Design Breakdown
The XML describes an Audio Effect Rack (ADG). I will break it down by its three main branches: Low Bass, Phaser, and Dry. For each branch, I will identify the devices used and their specific parameter settings as extracted from the XML values.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Crossover Phaser
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Crossover Phaser"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_crossover_phaser.xml` (54,219 bytes).
