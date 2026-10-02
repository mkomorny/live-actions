---
title: Stereo Widener Mod
category: time_based_spatial
subcategory: delay
id: time_based_spatial_stereo_widener_mod
pages: 1
words: 415
source: ableton_dataset.jsonl
---
# Stereo Widener Mod

## Sound Character & Overview
> **Layman Description:** Analyze the provided Ableton XML preset code. Identify all the effects, devices, and specific parameter values used within the structure.

> **Emotional Vibe:** You are an expert sound designer. Dissect this complex stereo widener preset. Tell me exactly how it is built, what devices are used in its parallel branches, and the specific settings that make this 'Stereo Widener Mod' work.

## Technical Architecture & Signal Chain
Perform a deep-structure analysis of the Ableton Live XML Audio Effect Group. Extract the signal chain architecture (including parallel branches), identify every device type, and map out the precise parameter values for each device's internal settings.

## Chain of Thought Sound Design Breakdown
1. **Identify Root Structure**: The file is an `AudioEffectGroupDevice` (an Audio Effect Rack/Group) named 'Stereo Widener Mod'. It uses parallel processing via `BranchPresets`. 

2. **Analyze Branch 0 ('Mid')**:
   - **Signal Path**: A single device.
   - **Device**: `StereoGain` (Ableton's **Utility** effect).
   - **Parameters**:
     - `ChannelMode`: 1 (Mid/Side mode)
     - `StereoWidth`: 1
     - `MidSideBalance`: 0
     - `MidSideBalanceOn`: true
     - `Mono`: false
     - `BassMono`: false
     - `BassMonoFrequency`: 120 Hz
     - `Gain`: 1 (Unity)

3. **Analyze Branch 1 ('Side')**:
   - **Signal Path**: A serial chain of two devices: `Echo` -> `StereoGain` (Utility).
   - **Device 1: Echo**:
     - `Delay_SyncL/R`: false (Free-running)
     - `Delay_TimeL`: ~0.0094s (approx. 9.5ms)
     - `Delay_TimeR`: ~0.0204s (approx. 20.4ms)
     - `Delay_Repitch`: true
     - `Feedback`: 0
     - `StereoWidth`: 2 (Maximum width)
     - `DryWet`: ~0.677 (67.7% wet)
     - `Filter_HighPassFrequency`: 21.07 Hz
     - `Modulation_Frequency`: 0.08 Hz
     - `Modulation_PhaseOffset`: 180°
   - **Device 2: Utility (StereoGain)**:
     - `ChannelMode`: 1 (Mid/Side mode)
     - `StereoWidth`: 1
     - `MidSideBalance`: 1 (All Side content)
     - `MidSideBalanceOn`: true
     - `Mono`: false
     - `Gain`: 1 (Unity)

4. **Synthesize Sound Design Intent**:
   The preset uses a Mid/Side splitting technique. Branch 'Mid' preserves the center signal using a Utility set to M/S mode. Branch 'Side' isolates the side information, applies a micro-delay (Haas effect) via Echo with different delay times for Left and Right to create massive stereo width, and then ensures only the Side content is passed through via a second Utility device. This is a sophisticated way to widen a signal without destroying mono compatibility or phase coherence in the center.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Stereo Widener Mod
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Stereo Widener Mod"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_stereo_widener_mod.xml` (68,886 bytes).
