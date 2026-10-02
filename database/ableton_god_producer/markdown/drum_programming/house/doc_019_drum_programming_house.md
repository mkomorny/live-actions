---
title: House 126 BPM Four-on-Floor & Offbeat Open Hats
category: drum_programming
subcategory: house
id: doc_019_drum_programming_house
words: 482
source: ableton_god_producer_15k.jsonl
---
# House 126 BPM Four-on-Floor & Offbeat Open Hats

Comprehensive production guide and Ableton Live 12 workflow for House drum programming.

## Overview & Style Attributes
- **Primary Style**: House
- **Recommended Drum Kits**: TR-909, TR-707
- **Groove Pool Template**: MPC60 16-Swing 58% / SP-1200 Swing 56%
- **Corpus Examples**: 623 variations indexed

## Step Sequencer Piano Roll Matrix (1 Bar Pattern)
1. **Kick**: Primary hits on Beat 1 and syncopated offbeats.
2. **Snare / Clap**: Crisp transient hit on Beats 2 and 4 (or Beat 3 for halftime).
3. **Hi-Hats**: Dynamic 1/16 grid with randomized velocity between 65 and 95.
4. **Ghost Notes**: Soft taps (velocity 40-50) providing rhythmic bounce.

## Live Actions Parameter Blueprint
```python
# Create Drum Rack on MIDI Track 0
live_create_device(track_index=0, device_name="DrumGroupDevice")

# Write 1-bar drum loop in House style
live_write_notes(track_index=0, clip_index=0, notes=[
    {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 110}, # Kick 1
    {"pitch": 36, "start_time": 2.0, "duration": 0.25, "velocity": 105}, # Kick 2
    {"pitch": 38, "start_time": 1.0, "duration": 0.25, "velocity": 108}, # Snare 1
    {"pitch": 38, "start_time": 3.0, "duration": 0.25, "velocity": 112}, # Snare 2
    {"pitch": 42, "start_time": 0.0, "duration": 0.25, "velocity": 85},  # Hat
    {"pitch": 42, "start_time": 0.25, "duration": 0.25, "velocity": 70}, # Hat
    {"pitch": 42, "start_time": 0.5, "duration": 0.25, "velocity": 90},  # Hat
    {"pitch": 42, "start_time": 0.75, "duration": 0.25, "velocity": 72}, # Hat
])
```

## Professional Production Workflow Example
<think>
Step 1: Drum Rack Setup
- Create new MIDI track → Load Drum Rack
- Load Acoustic Kit preset (or individual samples: Kick from 808, Snare from TR-909, Closed Hats from SP-1200)
- Set Drum Rack output to "Track" for individual processing later

Step 2: Core Groove (Piano Roll - 1/16 grid)
- Kick: Hits on 1, 5, 9, 13 (strong on 1 and 9 for House bounce)
- Snare: Hits on 5 and 13 (classic backbeat), velocity 90-110
- Closed Hats: 16th notes with velocity variation (65-95) + slight swing 55-58%
- Open Hat: Hit on 8 and 16 for lift
- Percussion: Add rim or clap on 3 and 11 for syncopation

Step 3: God-Level Refinements
- Apply "Swing" 58% on MIDI clip (makes it breathe)
- Velocity humanization: ±8 on hats
- Add subtle ghost notes on snare (velocity 40-55) on 7 and 15
- Route kick to separate track with Glue Compressor (threshold -18dB, ratio 4:1)

Reasoning: In House, the kick and snare relationship creates the pocket. The slight swing + velocity variation prevents robotic feel while keeping it tight. Low-end energy is reserved for later bass layering.
</think>

**Final Ableton Actions:**
1. Load Drum Rack on Track 1
2. Drag Acoustic Kit samples into pads
3. Draw MIDI as described above
4. Add "Groove Pool" → "MPC60" or "SP-1200" feel
5. Group drums → Add "Saturator" (Soft Sine, Drive 8%) for warmth

This foundation gives massive headroom for bass and melody while staying dancefloor-ready.
