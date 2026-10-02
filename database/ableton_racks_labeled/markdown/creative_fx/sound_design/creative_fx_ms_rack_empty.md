---
title: MS Rack Empty
category: creative_fx
subcategory: sound_design
id: creative_fx_ms_rack_empty
pages: 1
words: 230
source: ableton_dataset.jsonl
---
# MS Rack Empty

## Sound Character & Overview
> **Layman Description:** This is a Mid-Side (M/S) processing Audio Effect Rack. It splits an incoming stereo signal into two parallel paths: one for the 'Mid' (center) information and one for the 'Sides' (stereo width) information, using Ableton's Utility device.

> **Emotional Vibe:** A surgical mixing tool that allows you to independently control the center and the stereo width of your audio, giving you total command over the spatial image.

## Technical Architecture & Signal Chain
An Audio Effect Rack containing two discrete branches designed for Mid-Side manipulation. Each branch utilizes a Utility device set to M/S mode with specific balance offsets to isolate signal components.

## Chain of Thought Sound Design Breakdown
1. Identify Root: Audio Effect Rack (GroupDevicePreset) named 'MS Rack Empty'.
2. Analyze Branch 1 ('Mid'): Contains a Utility device (StereoGain). MidSideBalance is set to 0 (isolating Mid). Volume is at unity.
3. Analyze Branch 2 ('Sides'): Contains a Utility device (StereoGain). MidSideBalance is set to 2 (isolating Sides). Volume is at unity.
4. Conclusion: This is a standard M/S splitter rack.

## Live Actions Blueprint
```python
# Live Actions device chain reference for MS Rack Empty
live_create_device(track_index=0, device_name="AudioEffectGroupDevice", params=[
    {"name": "Preset Name", "value": "MS Rack Empty"},
])
```

## XML Source Note
The full XML preset is cataloged in the dataset database and archived under `xml_presets/creative_fx_ms_rack_empty.xml` (38,429 bytes).
