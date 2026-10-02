---
title: Spotify Pedalboard VST3 Pipeline for Vital
category: third_party_plugins
subcategory: plugins
id: third_party_plugins_doc_006_spotify_pedalboard_vst3_pipeline
pages: 1
words: 288
source: 02_headless_rendering_and_hosting/doc_006_spotify_pedalboard_vst3_pipeline.md
---
# Spotify Pedalboard VST3 Pipeline for Vital

## Overview

**Spotify Pedalboard** (`github.com/spotify/pedalboard`) is a high-performance Python audio library created by Spotify. It provides a native interface for loading VST3® and Audio Unit plugins, automating parameters, and applying studio-grade DSP chains directly in Python code.

### Installation
```bash
pip install pedalboard
```

---

## Loading Vital VST3 & Automating DSP Chains

Pedalboard allows you to treat `Vital.vst3` as a Python audio processor node, chain it into hardware-modeled guitar pedals or mastering processors, and write high-fidelity WAV files.

```python
import numpy as np
from pedalboard import Pedalboard, Chorus, Reverb, Delay, HighpassFilter, Compressor, Limiter
from pedalboard.io import AudioFile
import pedalboard

def process_synth_through_studio_chain(input_wav: str, output_wav: str, sample_rate: int = 44100):
    """Pass rendered Vital synth stems through a professional mastering & analog coloration chain."""
    
    # Construct an analog post-processing chain
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=30.0),  # Sub rumble cleanup
        Chorus(rate_hz=1.2, depth=0.25, centre_delay_ms=7.0, feedback=0.2, mix=0.3),
        Delay(delay_seconds=0.375, feedback=0.35, mix=0.15),  # Dotted 8th delay
        Compressor(threshold_db=-18.0, ratio=3.0, attack_ms=15.0, release_ms=120.0),
        Reverb(room_size=0.45, damping=0.5, wet_level=0.2, dry_level=0.8),
        Limiter(threshold_db=-0.5)
    ])
    
    # Read raw audio
    with AudioFile(input_wav) as f:
        audio = f.read(f.frames)
        sr = f.samplerate
        
    # Process through Pedalboard DSP
    effected_audio = board(audio, sr)
    
    # Write final polished master
    with AudioFile(output_wav, 'w', sr, effected_audio.shape[0]) as f:
        f.write(effected_audio)
```

---

## VST3 Parameter Inspection & State Management

Pedalboard provides a direct mechanism to load and inspect VST3 plugins:

```python
from pedalboard import load_plugin

def inspect_vital_vst3(vst_path: str = r"C:\Program Files\Common Files\VST3\Vital.vst3"):
    """List available parameter identifiers on Vital VST3."""
    vital = load_plugin(vst_path)
    print(f"Plugin Name: {vital.name}")
    print(f"Category: {vital.category}")
    print(f"Parameters Count: {len(vital.parameters)}")
    
    # Query parameters
    for name, param in list(vital.parameters.items())[:15]:
        print(f"  {name}: min={param.min_value}, max={param.max_value}, default={param.default_value}")
```

This permits Live Actions Helper to dynamically verify plugin parameter names and ranges on the user's specific installation before triggering automated parameter tweaks.
