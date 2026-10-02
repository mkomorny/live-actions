---
id: 01_preset_architecture_doc_002_oscillators_filters_and_modulators
title: Vital Oscillators, Filters, and Modulation Architecture
category: 01_preset_architecture
pages: 1
words: 608
source: 01_preset_architecture/doc_002_oscillators_filters_and_modulators.md
---
# Vital Oscillators, Filters, and Modulation Architecture

## Oscillator Engine (Osc 1, Osc 2, Osc 3)

Vital features 3 stereo wavetable oscillators with independent warp modes, unison generators, and spectral processing engines.

### 1. Oscillator Core Parameters
For oscillator $N \in \{1, 2, 3\}$, the parameter prefix in `settings` is `osc_{N}_`:

```json
{
  "osc_1_on": 1.0,
  "osc_1_level": 0.8,
  "osc_1_pan": 0.0,
  "osc_1_transpose": 0.0,
  "osc_1_tune": 0.0,
  "osc_1_wave_frame": 0.0,
  "osc_1_spectral_morph_type": 1.0,
  "osc_1_spectral_morph_amount": 0.5,
  "osc_1_distortion_type": 2.0,
  "osc_1_distortion_amount": 0.35,
  "osc_1_unison_voices": 8.0,
  "osc_1_detune_power": 1.5,
  "osc_1_detune_range": 2.0,
  "osc_1_stereo_spread": 1.0,
  "osc_1_phase": 0.5,
  "osc_1_phase_random": 1.0,
  "osc_1_destination": 1.0
}
```

* **`wave_frame`**: Current position in the 256-frame wavetable, mapped from `0.0` to `255.0` (or normalized `0.0` - `1.0`).
* **`destination`**: Routing destination: `0.0` = Direct to Master, `1.0` = Filter 1, `2.0` = Filter 2.
* **`distortion_type` (Warp Engine)**:
  * `0.0`: None
  * `1.0`: Sync (Oscillator hard sync simulation)
  * `2.0`: Formant (Pulse-width formant shifting)
  * `3.0`: Quantize (Bitcrush/sample-rate reduction)
  * `4.0`: Bend (Waveform warp bend)
  * `5.0`: Squeeze (Center compression)
  * `6.0`: Pulse (Duty cycle modulation)
  * `7.0`: FM from Osc 2 (Frequency Modulation)
  * `8.0`: RM from Osc 2 (Ring Modulation)
* **`spectral_morph_type`**:
  * `0.0`: None
  * `1.0`: Vocode (Frequency bin filtering)
  * `2.0`: Formant Scale (Vocal tract resonance expansion)
  * `3.0`: Harmonic Stretch
  * `4.0`: Inharmonic Stretch (Bell/metallic timbre generation)
  * `5.0`: Smear (Phase randomization)
  * `6.0`: Random Amplitudes

---

## Dual Multimode Filters (Filter 1 & Filter 2)

Each filter can model both vintage analog circuits and digital acoustic resonators.

```json
{
  "filter_1_on": 1.0,
  "filter_1_model": 0.0,
  "filter_1_style": 1.0,
  "filter_1_cutoff": 48.0,
  "filter_1_resonance": 0.35,
  "filter_1_drive": 0.2,
  "filter_1_keytrack": 0.5,
  "filter_1_blend": 0.0,
  "filter_1_formant_x": 0.0,
  "filter_1_formant_y": 0.0
}
```

* **`filter_1_model`**:
  * `0.0`: Analog (12dB / 24dB OTA ladder with warm saturation)
  * `1.0`: Dirty (Aggressive non-linear feedback drive)
  * `2.0`: Ladder (Moog-style transistor ladder with low-end drop compensation)
  * `3.0`: Digital (Clean zero-delay feedback filter)
  * `4.0`: Diode (Roland TB-303 style diode ladder)
  * `5.0`: Formant (Dual vowel resonator)
  * `6.0`: Comb (Delay-line physical modeling resonator)
* **`filter_1_cutoff`**: Pitch-calibrated cutoff value in MIDI semitones (`0.0` = 8.17 Hz / C-2, `60.0` = 261.6 Hz / C3, `128.0` = 12,543 Hz / G9).

---

## Envelopes (Env 1 through Env 6)

Env 1 is hardwired as the Master Amplitude Envelope. Envelopes 2–6 are freely assignable modulation sources.

```json
{
  "env_1_attack": 0.005,
  "env_1_decay": 0.8,
  "env_1_sustain": 0.0,
  "env_1_release": 0.15,
  "env_1_delay": 0.0,
  "env_1_hold": 0.0,
  "env_1_attack_power": 0.0,
  "env_1_decay_power": -1.5,
  "env_1_release_power": -2.0
}
```

* **Timing Units**: `attack`, `decay`, `release` are specified in logarithmic seconds ($2^{\text{val}}$).
* **Power Curves**: `-1.0` to `-3.0` produces sharp exponential snap (ideal for plucks and kicks); `0.0` is linear; `1.0` to `3.0` is logarithmic swell.

---

## LFO Generators (LFO 1 through LFO 8)

Vital LFOs are customizable bezier curve sequencers.

```json
{
  "lfo_1_frequency": 2.0,
  "lfo_1_sync_type": 1.0,
  "lfo_1_tempo": 6.0,
  "lfo_1_smooth": 0.0,
  "lfo_1_fade_time": 0.0,
  "lfo_1_keytrack": 0.0
}
```

* **`sync_type`**: `0.0` = Seconds / Free Hz, `1.0` = Tempo Sync, `2.0` = Triplet, `3.0` = Dotted, `4.0` = Keytrack, `5.0` = Envelope (Single-shot trigger).
* **`tempo`**: Musical divisions (`4.0` = 1 bar, `5.0` = 1/2 note, `6.0` = 1/4 note, `7.0` = 1/8 note, `8.0` = 1/16 note).

---

## Modulation Matrix Routing Architecture

Vital provides up to 64 modulation matrix routing connections. Each connection is indexed by integer $M \in [1, 64]$:

```json
{
  "modulation_1_source": "lfo_1",
  "modulation_1_destination": "filter_1_cutoff",
  "modulation_1_amount": 24.0,
  "modulation_1_bipolar": 1.0,
  "modulation_1_stereo": 0.0,
  "modulation_1_power": 0.0
}
```

* **`source`**: Identifier string (e.g. `"lfo_1"`, `"env_2"`, `"random_1"`, `"mod_wheel"`, `"note"`, `"velocity"`, `"aftertouch"`).
* **`destination`**: Exact parameter name string (e.g. `"filter_1_cutoff"`, `"osc_1_wave_frame"`, `"osc_1_distortion_amount"`).
* **`amount`**: Modulation depth scaled to destination units (e.g. semitones for cutoff/pitch, 0.0–1.0 for gain/warp).
* **`bipolar`**: `1.0` for two-sided sweep ($\pm \Delta$); `0.0` for unipolar sweep ($0 \to +\Delta$).
