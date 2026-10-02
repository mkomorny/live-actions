---
id: 03_algorithmic_music_helpers_doc_008_algorithmic_drum_and_bassline_generation
title: 'Algorithmic Music Generation: 8 Drum Styles, 6 Bassline Styles & Humanizers'
category: 03_algorithmic_music_helpers
pages: 1
words: 880
source: 03_algorithmic_music_helpers/doc_008_algorithmic_drum_and_bassline_generation.md
---
# Algorithmic Music Generation: 8 Drum Styles, 6 Bassline Styles & Humanizers

## 1. Algorithmic Drum Pattern Generation (`generate_drum_pattern`)

`AbletonMCP` embeds pure algorithmic MIDI pattern builders inside Python, writing notes directly into clip slots.

### Supported Drum Styles (General MIDI Pad Map)
- **`house`**: Four-on-the-floor kick (C1 on 1, 2, 3, 4), off-beat open hi-hat (A#1 on 1.5, 2.5, 3.5, 4.5), clap/snare (D1 on 2 and 4).
- **`techno`**: Driving 4/4 kick, closed hats on 16th notes with velocity accenting, syncopated ride cymbal.
- **`hip_hop`**: Boom-bap syncopated kick pattern, snare on 2 and 4, swinging 8th-note hats.
- **`trap`**: Heavy 808 kick drops, snare/clap on 3rd beat, rapid 1/16 and 1/32 hi-hat rolls.
- **`dnb`**: Fast 174 BPM two-step breakbeat (kick on 1, snare on 1.75 and 3.5).
- **`funk`**: Ghosted syncopated snares, intricate kick modulation, dynamic hi-hat pedal control.
- **`jazz`**: Swing ride cymbal pattern (`ding-ding-a-ding`), feathered bass drum, 2 and 4 hi-hat chicks.
- **`basic`**: Standard rock 8-beat starter groove.

```python
# Generate a 4-bar trap drum pattern on Track 0, Slot 0
client.send({
    "type": "generate_drum_pattern",
    "params": {"track_index": 0, "slot_index": 0, "style": "trap", "length_bars": 4}
})
```

---

## 2. Algorithmic Bassline Generation (`generate_bassline`)

Generates scale-constrained bass riffs based on root note and scale mode:

### Bassline Styles
- **`basic`**: Root note anchors on strong beats with octave jumps.
- **`walking`**: Jazz walking bass using scale stepwise motion and chromatic passing tones.
- **`synth`**: 16th-note driving bass with octave bounces and syncopation.
- **`funk`**: Syncopated slap/pop riffs with rests and 16th-note ghost notes.
- **`octave`**: Classic disco/italo octave alternating pattern.
- **`arpeggiated`**: Moving chord triad/seventh arpeggios.

---

## 3. Scale Reference Engine (`get_scale_notes`)

Translates root notes (`C`, `D#`, `F`) into exact MIDI note numbers across 13 scales:
- `major`, `minor`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `locrian`
- `pentatonic_major`, `pentatonic_minor`, `blues`
- `harmonic_minor`, `melodic_minor`, `whole_tone`

---

## 4. Humanization & Timing Quantization

### Micro-Timing Humanizer (`humanize_clip_timing`)
Applies a Gaussian-distributed timing jitter (±5 to ±25 milliseconds) to note start times, eliminating robotic rigidity.

### Velocity Dynamics Humanizer (`humanize_clip_velocity`)
Applies subtle velocity deviations (±3 to ±15 velocity units) while preserving groove accents on strong beats.

### Note Quantizer (`quantize_clip_notes`)
Snaps notes to strict musical grids (`1/4`, `1/8`, `1/16`, `1/32`, `1/8T`, `1/16T`) with adjustable strength percentage (0.0 to 1.0).
