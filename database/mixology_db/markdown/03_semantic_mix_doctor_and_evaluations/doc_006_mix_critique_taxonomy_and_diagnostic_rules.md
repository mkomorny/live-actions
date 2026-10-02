---
id: 03_semantic_mix_doctor_and_evaluations_doc_006_mix_critique_taxonomy_and_diagnostic_rules
title: Mix Critique Taxonomy & Diagnostic Rules
category: 03_semantic_mix_doctor_and_evaluations
pages: 1
words: 386
source: 03_semantic_mix_doctor_and_evaluations/doc_006_mix_critique_taxonomy_and_diagnostic_rules.md
---
# Mix Critique Taxonomy & Diagnostic Rules

## The 4 Universal Flaw Patterns in Multitrack Mixes

Analyzing the 2,177 human listening evaluations in MixologyDB reveals four recurring acoustic defects that blind listening panels consistently criticize:

---

### Pattern 1: Vocal Detachment & Excessive Dryness
* **Evaluation Quotes:**
  * *"Vocals very close, super dry. Need a bit of a sense of space around them. They are also too loud. Stick out."*
  * *"Stereo width is wide. Vocal is detached from the rest of the mix."*
  * *"Male vox way up front (uncomfortably)."*
* **Acoustic Signature:**
  * Lead Vocal fader $> -3.0 	ext{ dB}$ relative to drums.
  * Reverb / Delay sends $\le -35 	ext{ dB}$ (virtually bone dry).
* **Diagnostic Rule for Genius:**
  If Lead Vocal volume exceeds drum bus peak and send to Return A is disabled, flag: *"Vocal is upfront and detached from the ensemble."*

---

### Pattern 2: Low-End Masking & Kick/Bass Collision
* **Evaluation Quotes:**
  * *"Meager amount of bass frequency; kick drum dominates."*
  * *"Boomy bottom end, cannot distinguish bass notes from kick thud."*
* **Acoustic Signature:**
  * Kick Drum and Bass Guitar both boosting between 80 Hz and 110 Hz.
  * Lack of highpass filtering on guitars and keyboards below 100 Hz.
* **Diagnostic Rule for Genius:**
  If Kick and Bass lack reciprocal notch carving (e.g. Kick at 60Hz, Bass at 100Hz), flag: *"Low-end masking detected between Kick and Bass."*

---

### Pattern 3: Awkward Stereo Panning & Disjointed Transients
* **Evaluation Quotes:**
  * *"Snaps panning a little weird. Dominates vox."*
  * *"Too dry; clicks panned too far left, not enough ambience."*
  * *"Bold panning but failure to compensate with appropriate levels."*
* **Acoustic Signature:**
  * Transient-heavy percussive elements panned hard ($> 60\%$) with high fader levels.
* **Diagnostic Rule for Genius:**
  If high-frequency percussive elements are panned wide without auxiliary reverb balance, flag: *"Wide transient imbalance pulling listener focus away from center."*

---

### Pattern 4: Nasal Midrange & Boxiness
* **Evaluation Quotes:**
  * *"Vocal is bizarrely filtered sounding - no highs, too much mids."*
  * *"Cardboard drum sound, lacks air and depth."*
* **Acoustic Signature:**
  * Build-up of un-notched acoustic energy in the 400 Hz – 900 Hz zone.
* **Diagnostic Rule for Genius:**
  Recommend a -4dB to -8dB surgical cut at 450Hz on drums or 850Hz on vocals.
