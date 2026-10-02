---
title: Dirty Drum Synthesizer
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_dirty_drum_synthesizer
pages: 1
words: 380
source: ableton_dataset.jsonl
---
# Dirty Drum Synthesizer

## Sound Character & Overview
> **Layman Description:** This is an Ableton Live Audio Effect Rack named 'Dirty Drum Synthesizer'. It uses a complex nested structure to combine Corpus, Flanger, Shifter, and Limiter to create a synthesized drum sound. The rack features 8 main macro controls for easy manipulation of tone, distortion, and movement.

> **Emotional Vibe:** A gritty, metallic, and highly rhythmic drum processor that transforms acoustic drums into aggressive, synth-like percussion with deep resonance and shifting frequencies.

## Technical Architecture & Signal Chain
An Audio Effect Rack containing a nested Audio Effect Rack. The primary structure uses parallel branching (Wet/Dry). The 'Wet' branch contains a secondary rack with three sub-chains: a Corpus-based 'Dry' chain, a Flanger/Utility-based 'Wet' chain, and a Shifter-based 'Freq Shift' chain. A Limiter is placed on the main 'Dry' branch for peak control.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack ('Dirty Drum Synthesizer').
2. Analyze Main Macros: 8 macros mapped to Tune, Distort, Tone, Chorus, Motion Rate, Decay, Rack Dry/Wet, and Rack Volume.
3. Trace Branching (Main): 
   - Branch 'Wet' (Id=0) contains a nested Audio Effect Rack.
   - Branch 'Dry' (Id=1) contains a Limiter.
4. Trace Nested Rack (Inside 'Wet'):
   - Sub-branch 'Dry' (Id=0): Contains Corpus ('Drum to Bass Synth' preset).
   - Sub-branch 'Wet' (Id=1): Contains Flanger and StereoGain (Utility).
   - Sub-branch 'Freq Shift' (Id=2): Contains Shifter.
5. Extract Parameters for each device: 
   - Corpus: Resonance Type 2, Frequency ~0.248, Decay ~0.802, Freq Damping -0.6, Radius ~0.975, Tube Opening 1.0, Ratio ~0.68, Excitation X ~0.69, LFO On (Sine/Sync), Filter Mid Freq ~173Hz, Drive ~0.71.
   - Flanger: Dry/Wet 1.0, Delay Time 7, Feedback 0, LFO On (Type 2, Freq ~0.92Hz, Phase 180°), Hipass 20Hz.
   - StereoGain: Mid/Side Mode On, M/S Balance ~1.24, Gain ~0.69, Phase Invert L/R On.
   - Shifter: Frequency Shift mode, LFO Spin On (Phase 180°), Ring Mod Drive On (Amount 17), Global Tone 22kHz, Wide On.
   - Limiter: Ceiling -0.5dB, Release 300ms, Auto Release On, Lookahead 1ms.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dirty Drum Synthesizer
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dirty Drum Synthesizer"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_dirty_drum_synthesizer.xml` (130,208 bytes).
