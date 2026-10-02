---
id: 02_instrument_eq_carving_curves_doc_005_vocal_processing_and_space_curves
title: Vocal Processing & Acoustic Space Profiles
category: 02_instrument_eq_carving_curves
pages: 1
words: 311
source: 02_instrument_eq_carving_curves/doc_005_vocal_processing_and_space_curves.md
---
# Vocal Processing & Acoustic Space Profiles

## 1. Lead Vocal Parametric EQ Profiles

Lead vocal channels in MixologyDB exhibit a consistent 4-stage equalisation structure:

* **Stage 1 (Chest Rumble Highpass):**
  * `Frequency`: **114 Hz**
  * `Slope`: 12dB or 24dB / octave
  * `Q`: **0.71**
  * `Purpose`: Eliminates mic stand thump, AC rumble, and plosive air bursts.
* **Stage 2 (Nasal / Cardboard Cut):**
  * `Frequency`: **980 Hz – 1,150 Hz**
  * `Type`: Peaking
  * `Q`: **1.4**
  * `Gain`: **-3.5 dB to -8.0 dB**
  * `Purpose`: Removes honky, cupped-hand resonances in vocal recordings.
* **Stage 3 (Harsh Sibilance Dip):**
  * `Frequency`: **2,700 Hz – 3,400 Hz**
  * `Type`: Peaking
  * `Q`: **2.2**
  * `Gain`: **-3.0 dB to -5.0 dB**
  * `Purpose`: Tames abrasive ear fatigue and aggressive sibilance before compression.
* **Stage 4 (Silky Air Boost):**
  * `Frequency`: **11,000 Hz – 14,000 Hz**
  * `Type`: High Shelf
  * `Q`: **0.71**
  * `Gain`: **+3.0 dB to +5.5 dB**
  * `Purpose`: Adds commercial broadcast sheen and breathing space.

---

## 2. Reverb Models & Space Send Guidelines

MixologyDB multitracks record exact auxiliary send configurations:

| Reverb Category | Target Instruments | Average Send Gain | Reverb Tail Time (RT60) |
| :--- | :--- | :--- | :--- |
| **`Room / LexRoom`** | Drums (Snare, Toms), Rhythm Guitars | **-11.1 dB to -15.0 dB** | Short (0.8s – 1.2s) |
| **`Plate`** | Lead Vocals, Snare Top | **-14.0 dB to -18.5 dB** | Medium (1.5s – 2.2s) |
| **`Hall / Space`** | Background Vocals, Ambient Synths | **-18.0 dB to -22.0 dB** | Long (2.5s – 4.0s) |

### Key Takeaway
Notice that reverb sends in professional mixes are never pushed higher than $-10 	ext{ dB}$. This empirical rule directly informs Live Actions Genius when setting up Return tracks: auxiliary space should be felt, not heard as an obvious wash.
