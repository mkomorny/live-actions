---
id: 03_semantic_mix_doctor_and_evaluations_doc_007_automated_mix_audit_and_remedies
title: Automated Mix Doctor Audit & Remedy Algorithms
category: 03_semantic_mix_doctor_and_evaluations
pages: 1
words: 266
source: 03_semantic_mix_doctor_and_evaluations/doc_007_automated_mix_audit_and_remedies.md
---
# Automated Mix Doctor Audit & Remedy Algorithms

## Genius Diagnostic Logic Flow

When Live Actions Genius runs a mix diagnostic, it follows a deterministic evaluation tree derived from MixologyDB:

```text
Active Live Set
      |
      v
[Read Tracks & Faders (live_read_set)]
      |
      +---> Check 1: Headroom & Master Peak
      |       └── If master sum > -1.0 dB: Scale all track faders down by -4.0 dB
      |
      +---> Check 2: Vocal-to-Rhythm Balance
      |       └── If Vocal - DrumSum > 2.0 dB: Lower Vocal by -2.5 dB
      |
      +---> Check 3: Reverb Return Staging
      |       └── If Vocal Send A < -30 dB: Set Send A to -16.0 dB (Plate)
      |
      +---> Check 4: Low-End Frequency Carve
      |       └── Check Kick EQ Eight vs Bass EQ Eight: Inject reciprocal notch at 60Hz / 100Hz
      |
      v
[Emit Corrective Actions over OSC]
```

---

## Remedy Presets (Corrective Actions Matrix)

| Detected Acoustic Issue | Threshold Condition | Corrective Live Actions Tool Call |
| :--- | :--- | :--- |
| **Detached / Dry Vocal** | Vocal fader $> -3\text{ dB}$, Send A off | `live_update_track(track_index=vocal_idx, gain_db=-6.5, send="A", send_gain_db=-16.0)` |
| **Boxy Snare** | No notch between 600–900 Hz | `live_create_device(track_index=snare_idx, device_name="EQ Eight", params=[{"name": "3 Frequency A", "value": "732 Hz"}, {"name": "3 Gain A", "value": "-7.5 dB"}, {"name": "3 Q A", "value": "5.5"}])` |
| **Muddy Rhythm Guitars** | No highpass below 100 Hz | `live_create_device(track_index=gtr_idx, device_name="EQ Eight", params=[{"name": "1 Frequency A", "value": "95 Hz"}, {"name": "1 Filter Type A", "value": "Highpass 24 dB"}])` |
| **Masked Kick/Bass** | Both peaking at 80 Hz | `live_update_device(track_index=bass_idx, device_index=0, params=[{"name": "2 Frequency A", "value": "92 Hz"}])`, `live_update_device(track_index=kick_idx, device_index=0, params=[{"name": "2 Frequency A", "value": "55 Hz"}])` |
