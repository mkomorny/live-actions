---
id: 01_preset_architecture_doc_003_algorithmic_patch_generation_recipes
title: Algorithmic Patch Generation Recipes for Vital
category: 01_preset_architecture
pages: 1
words: 671
source: 01_preset_architecture/doc_003_algorithmic_patch_generation_recipes.md
---
# Algorithmic Patch Generation Recipes for Vital

## 1. Procedural Sound Design Archetypes

Using Python to generate `.vital` presets allows immediate sound design automation without opening a GUI. Below are tested programmatic parameter recipes for foundational production archetypes.

### Archetype A: Cyberpunk Reese Bass (Heavy Detune + Lowpass Saturation)

```python
def make_reese_bass() -> dict:
    return {
        "author": "Live Actions Genius",
        "preset_name": "Genius Reese Bass",
        "preset_style": "Bass",
        "settings": {
            "polyphony": 1.0,  # Monophonic
            "legato": 1.0,
            "portamento_time": -3.5,  # ~88ms glide
            
            # Osc 1: Sawtooth, 8 Unison voices
            "osc_1_on": 1.0,
            "osc_1_transpose": -12.0,
            "osc_1_unison_voices": 8.0,
            "osc_1_detune_power": 1.8,
            "osc_1_detune_range": 1.2,
            "osc_1_stereo_spread": 0.8,
            "osc_1_level": 0.7,
            "osc_1_destination": 1.0,
            
            # Osc 2: Square / Sub reinforcement
            "osc_2_on": 1.0,
            "osc_2_transpose": -24.0,
            "osc_2_unison_voices": 1.0,
            "osc_2_level": 0.65,
            "osc_2_destination": 1.0,
            
            # Filter 1: 24dB Analog Lowpass with Drive
            "filter_1_on": 1.0,
            "filter_1_model": 0.0,
            "filter_1_style": 1.0,
            "filter_1_cutoff": 42.0,  # ~110 Hz
            "filter_1_resonance": 0.28,
            "filter_1_drive": 0.35,
            
            # Env 1: Sustained amp
            "env_1_attack": 0.01,
            "env_1_decay": 0.5,
            "env_1_sustain": 1.0,
            "env_1_release": 0.2,
            
            # Distortion FX: Soft clip drive
            "distortion_on": 1.0,
            "distortion_type": 0.0,  # Soft clip
            "distortion_drive": 0.45,
            "distortion_mix": 0.8
        }
    }
```

### Archetype B: Neo-Soul Polyphonic Pluck (Exponential Filter Snap)

```python
def make_poly_pluck() -> dict:
    return {
        "author": "Live Actions Genius",
        "preset_name": "Neo-Soul Glass Pluck",
        "preset_style": "Keys",
        "settings": {
            "polyphony": 8.0,
            
            # Osc 1: Triangle / Sine hybrid with Formant warp
            "osc_1_on": 1.0,
            "osc_1_distortion_type": 2.0,  # Formant warp
            "osc_1_distortion_amount": 0.25,
            "osc_1_unison_voices": 4.0,
            "osc_1_detune_range": 0.35,
            "osc_1_level": 0.75,
            "osc_1_destination": 1.0,
            
            # Filter 1: 12dB Ladder with quick decay envelope
            "filter_1_on": 1.0,
            "filter_1_model": 2.0,  # Ladder
            "filter_1_cutoff": 36.0,
            "filter_1_resonance": 0.2,
            "filter_1_keytrack": 0.7,
            
            # Env 1: Pluck amplitude envelope
            "env_1_attack": 0.002,
            "env_1_decay": 0.85,
            "env_1_sustain": 0.15,
            "env_1_release": 0.25,
            "env_1_decay_power": -2.2,
            
            # Env 2: Filter envelope modulation
            "env_2_attack": 0.001,
            "env_2_decay": 0.32,
            "env_2_sustain": 0.0,
            "env_2_release": 0.15,
            "env_2_decay_power": -3.0,
            
            # Modulation: Env 2 -> Filter 1 Cutoff (+48 semitones)
            "modulation_1_source": "env_2",
            "modulation_1_destination": "filter_1_cutoff",
            "modulation_1_amount": 48.0,
            "modulation_1_bipolar": 0.0,
            
            # Reverb FX
            "reverb_on": 1.0,
            "reverb_decay_time": 2.2,
            "reverb_size": 0.6,
            "reverb_mix": 0.25
        }
    }
```

---

## 2. Musical Sweet-Spot Parameter Randomizer

Pure mathematical randomization often creates unusable audio (screaming resonant spikes or inaudible subsonic rumbles). The algorithm below constrains randomized values to verified musical ranges:

```python
import random

def mutate_vital_preset(base_preset: dict, mutation_rate: float = 0.2) -> dict:
    """Safely mutate a Vital preset dictionary while respecting acoustic sweet spots."""
    mutated = dict(base_preset)
    settings = dict(mutated.get("settings", {}))
    
    # 1. Subtle Cutoff shift (+- 12 semitones)
    if "filter_1_cutoff" in settings and random.random() < mutation_rate:
        current = settings["filter_1_cutoff"]
        settings["filter_1_cutoff"] = max(24.0, min(108.0, current + random.uniform(-12.0, 12.0)))
        
    # 2. Resonance clamp (never exceed 0.7 to prevent harsh screeching)
    if "filter_1_resonance" in settings and random.random() < mutation_rate:
        settings["filter_1_resonance"] = max(0.05, min(0.65, random.uniform(0.1, 0.55)))
        
    # 3. Wavetable frame shift
    if "osc_1_wave_frame" in settings and random.random() < mutation_rate:
        settings["osc_1_wave_frame"] = max(0.0, min(255.0, settings["osc_1_wave_frame"] + random.uniform(-30.0, 30.0)))
        
    # 4. Unison voice count (keep between 1 and 8)
    if "osc_1_unison_voices" in settings and random.random() < mutation_rate:
        settings["osc_1_unison_voices"] = float(random.choice([1, 2, 4, 6, 8]))
        
    # 5. Decay time variation
    if "env_1_decay" in settings and random.random() < mutation_rate:
        settings["env_1_decay"] = max(0.05, min(3.0, settings["env_1_decay"] * random.uniform(0.75, 1.35)))
        
    mutated["settings"] = settings
    mutated["preset_name"] = mutated.get("preset_name", "Patch") + " (Mutated)"
    return mutated
```

---

## 3. Patch Morphing / Linear Interpolation (LERP)

Given two `.vital` presets, you can blend timbres smoothly by interpolating their normalized parameter values:

$$\text{param}_{\text{morphed}} = (1 - \alpha)\cdot \text{param}_A + \alpha \cdot \text{param}_B \quad (\alpha \in [0.0, 1.0])$$

```python
def morph_vital_presets(preset_a: dict, preset_b: dict, alpha: float = 0.5) -> dict:
    """Linearly interpolate continuous parameters between two Vital presets."""
    set_a = preset_a.get("settings", {})
    set_b = preset_b.get("settings", {})
    all_keys = set(set_a.keys()).union(set_b.keys())
    
    morphed_settings = {}
    for key in all_keys:
        val_a = set_a.get(key)
        val_b = set_b.get(key)
        
        # If both are floats, interpolate
        if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
            # Preserve discrete toggles or step parameters
            if key in {"osc_1_unison_voices", "filter_1_model", "polyphony"}:
                morphed_settings[key] = val_a if alpha < 0.5 else val_b
            else:
                morphed_settings[key] = (1.0 - alpha) * float(val_a) + alpha * float(val_b)
        else:
            morphed_settings[key] = val_a if alpha < 0.5 else val_b
            
    return {
        "author": "Live Actions Genius",
        "preset_name": f"Morph ({int((1-alpha)*100)}% A / {int(alpha*100)}% B)",
        "preset_style": preset_a.get("preset_style", "Init"),
        "settings": morphed_settings
    }
```
