---
title: Filtered Tempo-Synced Delay Rack
category: time_based_spatial
subcategory: delay
id: time_based_spatial_filtered_tempo_synced_delay_rack
pages: 1
words: 325
source: ableton_dataset.jsonl
---
# Filtered Tempo-Synced Delay Rack

## Sound Character & Overview
> **Layman Description:** This is an Audio Effect Rack containing a single device: the Ableton Delay. The delay is set to be tempo-synced with a filter engaged, but currently, the Dry/Wet knob is at 0%, meaning no effect is audible.

> **Emotional Vibe:** A clean, rhythmic delay setup that's ready to add space and movement, but currently waiting for you to dial in the mix.

## Technical Architecture & Signal Chain
Audio Effect Rack (Single Chain) containing one instance of 'Ableton Delay'. Device is active (On). The delay line is synced to tempo (Sync L/R: On), with a feedback level of 50%. A filter is engaged (Filter On) with a cutoff frequency of approximately 1kHz and a bandwidth of 8. Note that the Dry/Wet mix is currently set to 0% (fully dry).

## Chain of Thought Sound Design Breakdown
1. Identify Root: The XML starts with a 'GroupDevicePreset', which is an Audio Effect Rack.
2. Navigate Hierarchy: Inside 'BranchPresets' -> 'AudioEffectBranchPreset' -> 'DevicePresets', I find one device of type 'Delay'.
3. Analyze Delay Parameters:
   - On/Off: Manual = true (On).
   - Sync: DelayLine_SyncL and R are both 'true' (Tempo synced).
   - Time: DelayLine_TimeL/R is ~0.375s. Note that SyncedSixteenth L=2, R=3 (Asymmetric rhythmic offset).
   - Feedback: 0.5 (50%).
   - Filter: Filter_On = true; Frequency ≈ 1000Hz; Bandwidth = 8.
   - Dry/Wet: Manual = 0 (This is the most important part for a sound designer—the effect is currently bypassed via the mix knob).
4. Analyze Mixer Parameters:
   - Volume: 1 (Unity gain).
   - Pan: 0 (Center).
5. Summary Construction: Group by device, list parameters with their specific values and states.

## Live Actions Blueprint
```python
# Live Actions device chain reference for Filtered Tempo-Synced Delay Rack
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "Filtered Tempo-Synced Delay Rack"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/time_based_spatial_filtered_tempo_synced_delay_rack.xml` (31,799 bytes).
