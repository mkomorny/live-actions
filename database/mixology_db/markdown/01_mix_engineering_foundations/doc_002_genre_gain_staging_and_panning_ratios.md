---
id: 01_mix_engineering_foundations_doc_002_genre_gain_staging_and_panning_ratios
title: Genre Gain Staging & Stereo Panning Reference Tables
category: 01_mix_engineering_foundations
pages: 1
words: 415
source: 01_mix_engineering_foundations/doc_002_genre_gain_staging_and_panning_ratios.md
---
# Genre Gain Staging & Stereo Panning Reference Tables

## Empirical Multi-Track Fader Hierarchy

Across the 2,411 annotated tracks in MixologyDB, professional mix engineers maintain a remarkably consistent relative fader gain hierarchy. Regardless of master bus headroom conventions, the relative decibel ratios between foundational elements remain stable.

### Master Fader Gain Benchmarks (Empirical Dataset Averages)

| Instrument Group | Mean Fader Gain | Median Fader Gain | Standard Dev | Fader Role in Balance |
| :--- | :--- | :--- | :--- | :--- |
| **Kick Drum (`KICK`)** | **-5.06 dB** | **-4.40 dB** | 6.41 dB | Low-end rhythmic anchor; highest drum transient |
| **Keys & Electric Piano (`KEYS`)** | **-5.61 dB** | **-4.35 dB** | 6.81 dB | Midrange harmonic foundation |
| **Bass Guitar / Synth (`BASS`)** | **-6.04 dB** | **-5.95 dB** | 5.42 dB | Lowest dynamic standard deviation; glued 1dB below kick |
| **Lead Vocal (`LEAD_VOCAL`)** | **-6.43 dB** | **-6.40 dB** | 5.17 dB | Front-and-center narrative focus |
| **Snare Drum (`SNARE`)** | **-7.40 dB** | **-7.40 dB** | 7.11 dB | Consistent 2.5–3.0 dB below kick drum peak |
| **Overheads (`OVERHEADS`)** | **-7.90 dB** | **-8.00 dB** | 7.86 dB | Acoustic kit space; sits below direct close mics |
| **Rhythm Guitars (`GUITAR_RHYTHM`)** | **-8.83 dB** | **-7.15 dB** | 6.67 dB | Flanks the vocal; stereo panned |
| **Hi-Hats (`HIHAT`)** | **-13.56 dB** | **-14.60 dB** | 10.89 dB | Deliberately tucked low to prevent ear fatigue |

---

## Stereo Panning Distribution Rules

MixologyDB records reveal a strict adherence to modern stereo architecture:

1. **The Solid Mono Center Axis ($0$ Pan):**
   * Kick Drum (`Kick In`, `Kick Out`) $	o$ Always Center ($0$)
   * Snare Top $	o$ Center ($0$) or micro-offset ($< 5\%$ L/R to match overhead image)
   * Bass DI / Bass Amp $	o$ Always Center ($0$)
   * Lead Vocal $	o$ Always Center ($0$)
2. **The Intermediate Mid-Sides ($\pm 15\%$ to $\pm 45\%$ Pan):**
   * Toms (T1: $25	ext{L}$, T2: $10	ext{R}$, Floor: $35	ext{R}$)
   * Hi-Hat ($15	ext{L}$ to $25	ext{L}$ to match drummer perspective)
   * Wurlitzer / Rhodes / Pianos (panned slightly off-center to clear vocal pocket)
3. **The Wide Stereophonic Flanks ($\pm 50\%$ to $\pm 100\%$ Pan):**
   * Overheads (Coles / Ribbon pairs panned hard $\pm 80\%$ to $\pm 100\%$)
   * Doubled Rhythm Guitars (Hard L/R $\pm 75\%$ to $\pm 100\%$ to leave center free for Lead Vocal and Bass)
