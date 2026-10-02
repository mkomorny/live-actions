---
title: Live Actions & Live 12 Production Glossary
category: foundations_and_guardrails
subcategory: glossary
id: doc_004_live_actions_integration_glossary
words: 203
source: PLAIN_ENGLISH_EXPLAINED.txt
---
# Live Actions & Live 12 Production Glossary

Essential technical terminology mapped to Ableton Live 12 and Live Actions OSC parameters:

- **Drum Rack**: Ableton's modular 128-pad instrument. Each pad hosts a Simpler or external instrument. Mapped via `live_create_device(device_name="DrumGroupDevice")`.
- **1/16 Grid**: Standard 16-step sequencer division per 4/4 measure (steps 0.0, 0.25, 0.5, 0.75 in beats).
- **Velocity**: MIDI note strike force (1-127). Live Actions sets this per note via the `velocity` property.
- **Swing / Groove Pool**: Micro-timing offsets shifting even 16th notes backward. 58% is standard MPC swing.
- **Ghost Notes**: Soft velocity hits (vel 35-55) on offbeats (boxes 7, 15) creating rhythmic momentum.
- **Sidechain Compression**: Audio routing where an external trigger (kick) modulates compressor gain reduction on a target track (bass, pads).
- **LUFS (Loudness Units Full Scale)**: Integrated psychoacoustic loudness standard. -14 LUFS for streaming; -8 to -10 LUFS for club systems.
- **True Peak**: Inter-sample peak level detection preventing D/A conversion clipping (target: -0.3 to -1.0 dBTP).
- **Glue Compressor**: Analog-modeled SSL bus compressor featuring transparent VCA peak leveling.
- **Saturator**: Non-linear waveshaping distortion adding even/odd harmonics (Soft Sine, Analog Clip).
- **Utility Device**: Gain, phase inversion, stereo width, and low-frequency mono summing (Bass Mono below 120Hz).
