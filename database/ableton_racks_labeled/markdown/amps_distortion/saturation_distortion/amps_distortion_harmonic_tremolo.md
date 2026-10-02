---
title: Harmonic Tremolo
category: amps_distortion
subcategory: saturation_distortion
id: amps_distortion_harmonic_tremolo
pages: 1
words: 330
source: ableton_dataset.jsonl
---
# Harmonic Tremolo

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Harmonic Tremolo'. It uses a frequency-splitting technique (crossover) to apply different modulation characteristics to the low and high frequencies of a signal, creating a complex, 'harmonic' movement. It also includes a distortion/pedal branch.

> **Emotional Vibe:** A lush, swirling, and complex movement effect that feels alive and organic, moving between deep rhythmic pulses and shimmering high-end textures.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack utilizing multiple branches for parallel processing. It implements a frequency-dependent modulation scheme by splitting the signal into 'Lo' and 'Hi' bands using EQ Three devices, applying phase-offset or inverted Auto Pan to each band, and providing a separate saturation path via a Pedal device.

## Chain of Thought Sound Design Breakdown
1. Identify the root: It's an Audio Effect Rack (GroupDevicePreset) named 'Harmonic Tremolo'.
2. Analyze Branch 1 ('Lo'): Contains EQ Three followed by Auto Pan. The EQ Three acts as a low-pass filter (Low On, Mid/Hi Off) with a crossover point around 456Hz and 2500Hz.
3. Analyze Branch 2 ('Hi'): Contains EQ Three followed by Auto Pan. This acts as a high-pass/band-pass (Mid/Hi On, Low Off).
4. Compare modulation: The 'Lo' branch has Auto Pan with 'LfoInvert' set to True, while the 'Hi' branch has it set to False. This creates the 'harmonic' phase-shifting effect.
5. Analyze Branch 3 (Unnamed): Contains a Pedal device. It is currently set to a Dry/Wet of 0, meaning it is effectively bypassed but available for drive.
6. Map Macros: Macro 3 is explicitly named 'Drive Amt'. Other macros are unassigned in the XML but control various parameters across the chains.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Harmonic Tremolo
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Harmonic Tremolo"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_harmonic_tremolo.xml` (95,702 bytes).
