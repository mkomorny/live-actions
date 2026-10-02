---
id: 02_instrument_eq_carving_curves_doc_004_bass_guitars_keys_eq_profiles
title: Bass, Guitars & Keyboard Parametric EQ Profiles
category: 02_instrument_eq_carving_curves
pages: 1
words: 305
source: 02_instrument_eq_carving_curves/doc_004_bass_guitars_keys_eq_profiles.md
---
# Bass, Guitars & Keyboard Parametric EQ Profiles

## 1. Bass Guitar & Synth Bass EQ Profiles

In MixologyDB, bass tracks are engineered to intertwine with the kick drum rather than compete for identical frequency nodes:

* **Band 1 (Sub Alignment Notch / Shelf):**
  * `Frequency`: **92 Hz**
  * `Type`: Low Shelf
  * `Gain`: **-0.5 dB to -2.0 dB**
  * `Purpose`: Leaves room for the 100 Hz kick punch.
* **Band 2 (Fundamental Growl Peak):**
  * `Frequency`: **400 Hz**
  * `Type`: Peaking
  * `Q`: **1.9**
  * `Gain`: **+3.0 dB to +7.5 dB**
  * `Purpose`: The core melodic pitch definition of electric and synth bass.
* **Band 3 (Finger Noise / Fret Clack Attenuation):**
  * `Frequency`: **1,880 Hz**
  * `Type`: Notch
  * `Q`: **3.1**
  * `Gain`: **-12.0 dB to -15.0 dB**
  * `Purpose`: Eliminates clicky string noise and high-frequency fret buzz.

---

## 2. Electric & Acoustic Guitars EQ Profiles

Rhythm guitars frequently occupy the critical 200 Hz to 3 kHz vocal corridor. Dataset annotations enforce surgical cleanup:

* **Highpass Filter:** Cut at **80 Hz – 110 Hz** (Q=0.71) to prevent mud accumulation with bass.
* **Low-Mid Mud Dip:** Cut at **350 Hz – 500 Hz** (-3.5 dB, Q=1.4) to de-clutter chordal rhythm parts.
* **Presence Air Peak:** Gentle lift at **4,500 Hz – 6,000 Hz** (+2.0 dB, Q=1.0) for pick definition.

---

## 3. Keyboards, Rhodes & Wurlitzer EQ Profiles

Keyboard instruments feature broad harmonic spectra that mask lead vocals if left flat:

* **Highpass Filter:** Set at **120 Hz** to isolate left-hand bass notes from the bass player.
* **Vocal Window Dip:** A wide parametric cut at **1,200 Hz – 2,500 Hz** (-2.5 dB, Q=0.8) carves a pocket for the lead vocal.
* **Top-End Roll-off:** Lowpass or high-shelf at **10,000 Hz** (-3.0 dB) to keep Rhodes warm and retro rather than modern and brittle.
