---
title: Dual Parallel Phaser-Flanger Rack
category: modulation
subcategory: chorus_flanger_phaser
id: modulation_dual_parallel_phaser_flanger_rack
pages: 1
words: 292
source: ableton_dataset.jsonl
---
# Dual Parallel Phaser-Flanger Rack

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Group containing two parallel branches of the 'Phaser-Flanger' device. The primary difference between the two branches is that Branch 1 has 'Invert Wet' enabled, while Branch 0 does not. This setup is designed for phase manipulation or texture switching using Ableton's Effect Rack branching.

> **Emotional Vibe:** A dual-branch Phaser-Flanger rack. Branch A: Standard Flanger (Invert Wet OFF). Branch B: Inverted Flanger (Invert Wet ON). Both branches are set to 100% Wet with a center frequency of ~1kHz and a synced rate of 4/4.

## Technical Architecture & Signal Chain
Audio Effect Group with two parallel branches (Branch 0 and Branch 1). Both branches utilize the Phaser-Flanger device in Flanger mode, but they are configured to create phase cancellation/inversion effects when switched via the branch selector. Macro 2 is mapped to 'Flange Time'.

## Chain of Thought Sound Design Breakdown
The XML describes an AudioEffectGroupDevice containing two 'AudioEffectBranchPreset' objects. Each branch contains a 'PhaserNew' device (Ableton's Phaser-Flanger) and an 'AudioBranchMixerDevice'. The key distinction is the 'InvertWet' parameter in Branch 1, which is set to 'true', whereas it is 'false' in Branch 0. This indicates a phase-inversion effect designed for use with the Rack's branch selector or automation. One macro ('Flange Time') is mapped to a parameter within the device chain (though the specific target mapping isn't explicitly visible in this snippet, it is assigned to Macro 1).

## Live Actions Blueprint
```python
# Live Actions device chain reference for Dual Parallel Phaser-Flanger Rack
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Dual Parallel Phaser-Flanger Rack"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/modulation_dual_parallel_phaser_flanger_rack.xml` (52,657 bytes).
