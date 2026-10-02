---
id: 01_mix_engineering_foundations_doc_001_mixologydb_architecture_and_dataset_spec
title: MixologyDB Architecture & Dataset Specification
category: 01_mix_engineering_foundations
pages: 1
words: 312
source: 01_mix_engineering_foundations/doc_001_mixologydb_architecture_and_dataset_spec.md
---
# MixologyDB Architecture & Dataset Specification

## Overview & Background
**MixologyDB** is an empirical audio engineering database curated by researchers at the University of Utah (funded under NSF Award #1650114). Developed as an extension of Brecht De Man's *The Mix Evaluation Dataset* and utilizing multitrack source projects from Mike Senior's *The Mixing Secrets* (Sound on Sound), MixologyDB provides an empirical record of real-world mixing decisions made by professional mixing engineers across digital audio workstations (Logic Pro, Pro Tools, and Reaper).

The dataset bridges the gap between acoustic engineering parameters and human perceptual evaluation by pairing multitrack channel settings with blind listening evaluations.

---

## Dataset Scale & Metrics

* **Total Complete Mix Projects:** 90 multitrack DAW projects
* **Total Track Annotations:** 2,411 individual instrument & vocal channels
* **Total Human Listening Evaluations:** 2,177 qualitative and quantitative evaluations
* **Primary Musical Genres:**
  * Pop Rock (21 mixes)
  * Country (21 mixes)
  * Rock & Hard Rock (16 mixes)
  * Funk & Soul (19 mixes)
  * Pop & Indie Rock (13 mixes)

---

## Channel Attribute Schema

For each of the 2,411 tracks, MixologyDB records:
1. **`track-name`**: Standardized instrument identifier (e.g. `Kick In`, `Snare Top`, `BassDI`, `RGtr Cleaner`, `mV1_LeadVox`, `wrlz_Keys`).
2. **`track-type`**: Channel routing classification (`AUDIO`, `AUX`, `BUS`, `MASTER`).
3. **`gain`**: Exact fader gain level specified in decibels (`dB`), referenced to DAW nominal fader scale.
4. **`pan`**: Stereo field panning position ($-100$ left to $+100$ right, centered at $0$).
5. **`eq`**: Array of discrete parametric filter bands:
   * Filter types: `HP` (Highpass), `LP` (Lowpass), `LS` (Low Shelf), `HS` (High Shelf), `NOTCH` / `PEAK` (Parametric Peaking).
   * Exact band properties: `freq` (Hz), `q` (bandwidth factor), and `gain` (dB boost/cut).
6. **`reverb` & `delay`**: Send assignments, target room acoustic models (`LexRoom`, `Plate`, `Hall`, `Room`), and exact send gains (`dB`).
7. **`mix-evaluation`**: Real human listening evaluations scoring overall mix balance, spatial cohesion, frequency masking, and vocal prominence.
