---
id: 02_instrument_eq_carving_curves_doc_003_drums_percussion_parametric_eq_profiles
title: Drum & Percussion Parametric EQ Profiles
category: 02_instrument_eq_carving_curves
pages: 1
words: 358
source: 02_instrument_eq_carving_curves/doc_003_drums_percussion_parametric_eq_profiles.md
---
# Drum & Percussion Parametric EQ Profiles

## Precision Parametric Filter Recipes from MixologyDB

Each filter configuration below is derived directly from empirical session annotations in MixologyDB. These settings translate 1:1 into Ableton Live's native **EQ Eight** device.

---

### 1. Kick Drum EQ Architecture (`Kick In` / `Kick Out`)
In the dataset, kick processing bifurcates cleanly between sub-harmonic control and boxiness attenuation:

* **Band 1 (Highpass Sub Rumble Cut):**
  * `Type`: Highpass 12dB or 24dB
  * `Frequency`: **49.6 Hz** (or 35.0 Hz on sub-heavy genres)
  * `Q`: **0.71**
  * `Purpose`: Cuts subsonic energy below the fundamental to free amplifier headroom.
* **Band 2 (Sub Weight & Punch Boost):**
  * `Type`: Low Shelf / Peaking
  * `Frequency`: **106 Hz**
  * `Q`: **1.0**
  * `Gain`: **+2.5 dB to +4.0 dB**
  * `Purpose`: Enhances low-end thud and chest punch.
* **Band 3 (Cardboard Mud Notch Cut):**
  * `Type`: Peaking / Notch
  * `Frequency`: **446 Hz**
  * `Q`: **1.1**
  * `Gain`: **-6.5 dB**
  * `Purpose`: Eliminates "cardboard box" resonance between 350 Hz and 500 Hz.
* **Band 4 (Beater Click Sizzle):**
  * `Type`: Peaking
  * `Frequency`: **2,360 Hz – 3,200 Hz**
  * `Q`: **2.1**
  * `Gain`: **+3.0 dB to +5.0 dB**
  * `Purpose`: Accentuates the beater impact so the kick cuts through laptop speakers.

---

### 2. Snare Drum EQ Architecture (`Snare Top` / `Snare Bottom`)

* **Band 1 (Highpass Fundamental Guard):**
  * `Type`: Highpass 12dB
  * `Frequency`: **114 Hz – 138 Hz**
  * `Q`: **0.71**
  * `Purpose`: Cleans out kick drum bleed and subsonic stage rumble.
* **Band 2 (Body & Meat Boost):**
  * `Type`: Peaking
  * `Frequency`: **180 Hz – 220 Hz**
  * `Q`: **1.17**
  * `Gain`: **+3.1 dB**
  * `Purpose`: Thickens snare body for punchy backbeats.
* **Band 3 (Hollow Resonance Cut):**
  * `Type`: Surgical Notch
  * `Frequency`: **732 Hz – 850 Hz**
  * `Q`: **5.87** (Very narrow)
  * `Gain`: **-7.9 dB**
  * `Purpose`: Removes metallic ringing overtones and nasal hollow frequencies.
* **Band 4 (Wire Snap & Air Boost):**
  * `Type`: High Shelf / Peaking
  * `Frequency`: **7,010 Hz**
  * `Q`: **0.89**
  * `Gain`: **+4.5 dB to +8.3 dB**
  * `Purpose`: Brightens snare wire sizzle and presence.
