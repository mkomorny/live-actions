---
title: 'Master Recipe 1: Drum Rack Programming, Pocket & Groove'
category: core_production_recipes
subcategory: drums
id: doc_005_recipe_1_drum_rack_pocket_and_groove
words: 343
source: PLAIN_ENGLISH_EXPLAINED.txt
---
# Master Recipe 1: Drum Rack Programming, Pocket & Groove

The foundational drum architecture utilized across 8,334 examples in the God Producer corpus.

## Core Step Architecture (16th Note Grid)

```text
Step Box:      1   2   3   4 | 5   6   7   8 | 9  10  11  12 | 13  14  15  16
Beat Division: 1.1     .2    | 1.2     .4    | 1.3     .2    | 1.4     .4
Kick:          [X] .   .   . | [X] .   .   . | [X] .   .   . | [X] .   .   .
Snare / Clap:  .   .   .   . | [X] .   .   . | .   .   .   . | [X] .   .   .
Closed Hat:    [X] [X] [X] [X]| [X] [X] [X] [X]| [X] [X] [X] [X]| [X] [X] [X] [X]
Open Hat:      .   .   .   . | .   .   .  [X]| .   .   .   . | .   .   .  [X]
Ghost Snare:   .   .   .   . | .   .  (x)  . | .   .   .   . | .   .  (x)  .
Perc / Rim:    .   .  [x]  . | .   .   .   . | .   .  [x]  . | .   .   .   .
```

## Velocity Humanization Guidelines
- **Kicks**: High velocity stability (105-115) to maintain steady low-end punch.
- **Main Snares**: Assertive strike (100-112).
- **Ghost Snares**: Subtle placement (40-52) on boxes 7 and 15.
- **Hi-Hats**: Dynamic micro-velocity curve (65 to 95) with subtle random jitter (+-4).
- **Swing**: 56% to 58% MPC groove offset.

## Processing Chain Blueprint (Live Actions)
1. **Drum Rack Group Bus**: Insert Saturator with Soft Sine, Drive at 1.5 dB (8-10% depth).
2. **Kick Channel**: Dedicated Glue Compressor (Threshold: -18 dB, Ratio: 4:1, Attack: 30 ms, Release: 100 ms).
3. **Hi-Hat Channel**: Auto Filter high-pass at 350 Hz to clear low-mid headroom.

```python
# Live Actions Python Blueprint: Create Drum Rack & Processing Chain
live_create_device(track_index=0, device_name="DrumGroupDevice")
live_create_device(track_index=0, device_name="Saturator", params=[
    {"name": "Drive", "value": "1.8 dB"},
    {"name": "Curve Type", "value": "Soft Sine"}
])
live_create_device(track_index=0, device_name="Glue Compressor", params=[
    {"name": "Threshold", "value": "-18.0 dB"},
    {"name": "Ratio", "value": "4"},
    {"name": "Attack", "value": "30 ms"}
])
```
