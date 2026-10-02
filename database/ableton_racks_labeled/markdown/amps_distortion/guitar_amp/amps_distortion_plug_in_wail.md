---
title: Plug In & Wail
category: amps_distortion
subcategory: guitar_amp
id: amps_distortion_plug_in_wail
pages: 1
words: 237
source: ableton_dataset.jsonl
---
# Plug In & Wail

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack named 'Plug In & Wail' created by Huston Singletary. It is a heavy saturation and character-shaping chain designed for high-gain processing, likely for electric instruments or aggressive drum/bass textures.

> **Emotional Vibe:** A thick, gritty, and highly controlled saturation chain that provides massive harmonic weight while maintaining surgical control over frequency-specific distortion and transient punch.

## Technical Architecture & Signal Chain
The preset is an Audio Effect Rack (ADG) containing a serial signal chain of five devices: Amp, Drum Buss, EQ Three, Pedal, and Limiter. It utilizes 8 visible macro controls for streamlined parameter mapping.

## Chain of Thought Sound Design Breakdown
The signal flows through an Amp (using a Rhodes 2-way preset) for initial warmth/drive, followed by Drum Buss for heavy compression and 'boom' enhancement. EQ Three then carves the tone, Pedal adds specific grit/distortion modes, and Limiter ensures the final output doesn't clip while maintaining high perceived loudness. The macro controls are mapped to Drive, Pressure, and Hi Freq, allowing for rapid tonal shifts from clean-ish to heavily distorted/compressed.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Plug In & Wail
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Plug In & Wail"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/amps_distortion_plug_in_wail.xml` (53,182 bytes).
