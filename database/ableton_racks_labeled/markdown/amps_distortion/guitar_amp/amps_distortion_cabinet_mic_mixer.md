---
title: Cabinet Mic Mixer
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_cabinet_mic_mixer
pages: 1
words: 357
source: ableton_dataset.jsonl
---
# Cabinet Mic Mixer

## Sound Character & Overview
> **Layman Description:** This is a complex Audio Effect Rack designed for guitar cabinet emulation and ambient room simulation. It uses an Audio Effect Rack to switch between different microphone positions (On-Axis, Off-Axis, Far) on a Cabinet device, then passes the signal through a Hybrid Reverb to simulate a room environment.

> **Emotional Vibe:** This preset provides a professional, studio-quality cabinet mic blending tool. It allows you to move from a tight, direct 'on-axis' sound to a distant, ambient 'far' sound with just a few turns of a knob, making it perfect for creating realistic guitar textures and spaces.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack ('Cabinet Mic Mixer') containing two main device chains. The first chain is a parallel/branching structure using three Audio Effect Branches (On-Axis, Off-Axis, Far) to select different microphone positions on a Cabinet device. The second chain is a Hybrid Reverb acting as a room simulator. Macro controls are mapped to blend the volumes of these mic positions and the reverb level.

## Chain of Thought Sound Design Breakdown
1. Identify the Root: An Audio Effect Rack (ADG) named 'Cabinet Mic Mixer'.
2. Analyze Macros: 6 active macros are mapped to On-Axis Vol, Off-Axis Vol, Far Vol, Macro 4, Room, and Master Vol.
3. Analyze Branching Structure: 
   - Branch 0 ('On-Axis'): Cabinet (Type 3, Mic Pos 0) -> Mixer (Vol ~0.56).
   - Branch 1 ('Off-Axis'): Cabinet (Type 3, Mic Pos 1) -> Mixer (Vol ~0.32).
   - Branch 2 ('Far'): Cabinet (Type 3, Mic Pos 2) -> Mixer (Vol ~0.50).
4. Analyze Secondary Device: A 'Hybrid Reverb' named 'Room' follows the rack.
5. Extract Hybrid Reverb Parameters: IR is 'Hybrid_Early_Reflections_Ableton Studio Mid.aif', Decay 3.5s, Size 0.5, EQ active with specific peak/low/high settings, and a very low Dry/Wet (~6.7%).
6. Synthesize into structured output.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Cabinet Mic Mixer
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Cabinet Mic Mixer"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_cabinet_mic_mixer.xml` (98,704 bytes).
