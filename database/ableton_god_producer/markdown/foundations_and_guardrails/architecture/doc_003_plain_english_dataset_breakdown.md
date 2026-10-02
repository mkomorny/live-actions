---
title: Plain English Dataset Architecture & Honest Breakdown
category: foundations_and_guardrails
subcategory: architecture
id: doc_003_plain_english_dataset_breakdown
words: 291
source: PLAIN_ENGLISH_EXPLAINED.txt
---
# Plain English Dataset Architecture & Honest Breakdown

## Dataset Breakdown by the Numbers

Across the 9,956 raw records:
- **Drum Programming**: 8,334 examples (~83.7%)
- **Bass Sound Design**: 1,609 examples (~16.2%)
- **Mixing & Mastering**: 13 examples (~0.1%)

## The 13 Production Styles
Each genre represents approximately 750 examples:
1. **Lo-Fi Hip Hop** (794) - Dusty boom-bap, swing, relaxed pocket.
2. **Techno** (791) - Driving four-on-the-floor, industrial rumble, 130-140 BPM.
3. **UK Garage** (779) - Skippy 2-step syncopation, ghost hits, swing 58%.
4. **Drill** (776) - Sliding 808s, triplet hi-hat rolls, off-beat snares.
5. **Drum & Bass** (775) - High-tempo 170-174 BPM two-step and amen patterns.
6. **Ambient Electronic** (769) - Expansive textures, sparse percussion, long decays.
7. **Trap** (761) - Heavy 808 subs, tight 1/32 and 1/64 hi-hat rolls, clap on beat 3.
8. **Jungle** (760) - Fast syncopated breaks, timestretched snares, deep sub bass.
9. **IDM** (759) - Glitch percussion, irregular micro-timings, complex modulation.
10. **Future Bass** (749) - Sidechained supersaws, wide syncopated kicks, bright snares.
11. **House** (748) - Classic four-on-the-floor, 909 open hats on the offbeat, 124-128 BPM.
12. **Hyperpop** (748) - Distorted transients, aggressive clipping, extreme pitch shifts.
13. **Phonk** (747) - Cowbell melodies, chopped Memphis vocal loops, saturated 808s.

## The Core Finding: Three Archetypal Recipes
The entire corpus relies on 3 master production recipes:
- **Recipe 1 (Drums)**: 16th grid pocket, 58% swing, ghost notes on boxes 7 & 15, Glue Compressor on kick.
- **Recipe 2 (Bass)**: Sub sine wave + detuned saw, 24dB low-pass (180-280Hz), quick decay (180-350ms), kick sidechain ducking (-24dB, 6:1).
- **Recipe 3 (Mix/Master)**: Group mix bus (EQ Eight high-pass 25Hz, mud notch 250Hz, Glue Compressor 2.5:1) + Master limiter (-0.3dB True Peak, -8 to -9 LUFS target).
