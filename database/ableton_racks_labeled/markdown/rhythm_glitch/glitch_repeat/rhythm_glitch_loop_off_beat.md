---
title: Loop Off Beat
category: rhythm_glitch
subcategory: glitch_repeat
id: rhythm_glitch_loop_off_beat
pages: 1
words: 197
source: ableton_dataset.jsonl
---
# Loop Off Beat

## Sound Character & Overview
> **Layman Description:** This is an Ableton Audio Effect Rack (ADG) named 'Loop Off Beat'. It uses a parallel processing structure with two branches: a 'Wet' branch containing a heavy rhythmic/textural chain, and a 'Dry' branch for clean signal bypass.

> **Emotional Vibe:** This rack is designed to 'rewrite drum grooves' by applying heavy physical modeling (Corpus), aggressive compression, and rhythmic slicing (Beat Repeat). It features several snapshots specifically tuned for drum fills and melodic 'siren' effects.

## Technical Architecture & Signal Chain
The preset utilizes an Audio Effect Rack with Macro mapping and Snapshot variations. The primary signal path is a serial chain of Corpus $\rightarrow$ Compressor $\rightarrow$ Beat Repeat.

## Chain of Thought Sound Design Breakdown
1. Identify Rack Structure $\rightarrow$ 2. Analyze Wet Branch Devices $\rightarrow$ 3. Extract Parameter Values $\rightarrow$ 4. Map Macro Controls $\rightarrow$ 5. Analyze Snapshots

## Live Actions Blueprint
```python
# Live Actions device chain reference for Loop Off Beat
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Loop Off Beat"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/rhythm_glitch_loop_off_beat.xml` (74,650 bytes).
