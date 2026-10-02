---
id: 04_live_actions_genius_actions_doc_009_live_actions_eq_carve_blueprint
title: 'Live Actions Blueprint: Parametric EQ Eight Carving'
category: 04_live_actions_genius_actions
pages: 1
words: 292
source: 04_live_actions_genius_actions/doc_009_live_actions_eq_carve_blueprint.md
---
# Live Actions Blueprint: Parametric EQ Eight Carving

## Action: `genius_eq_carve`

This blueprint injects instrument-calibrated 4-band or 8-band parametric EQ curves directly into Ableton Live's native **EQ Eight** on any specified track.

```python
# Live Actions Tool Blueprint
# Action: genius_eq_carve

def emit_eq_eight_carve(track_index: int, instrument: str) -> str:
    """Generate Live Actions tool call to instantiate calibrated EQ Eight."""
    
    eq_profiles = {
        "snare": [
            {"name": "1 Filter On A", "value": "1"},
            {"name": "1 Filter Type A", "value": "Highpass 48 dB"},
            {"name": "1 Frequency A", "value": "114 Hz"},
            {"name": "2 Filter On A", "value": "1"},
            {"name": "2 Frequency A", "value": "200 Hz"},
            {"name": "2 Gain A", "value": "3.1 dB"},
            {"name": "2 Q A", "value": "1.17"},
            {"name": "3 Filter On A", "value": "1"},
            {"name": "3 Frequency A", "value": "732 Hz"},
            {"name": "3 Gain A", "value": "-7.9 dB"},
            {"name": "3 Q A", "value": "5.87"},
            {"name": "4 Filter On A", "value": "1"},
            {"name": "4 Filter Type A", "value": "High Shelf"},
            {"name": "4 Frequency A", "value": "7010 Hz"},
            {"name": "4 Gain A", "value": "5.5 dB"}
        ],
        "vocal": [
            {"name": "1 Filter On A", "value": "1"},
            {"name": "1 Filter Type A", "value": "Highpass 24 dB"},
            {"name": "1 Frequency A", "value": "114 Hz"},
            {"name": "2 Filter On A", "value": "1"},
            {"name": "2 Frequency A", "value": "980 Hz"},
            {"name": "2 Gain A", "value": "-4.0 dB"},
            {"name": "2 Q A", "value": "1.4"},
            {"name": "3 Filter On A", "value": "1"},
            {"name": "3 Frequency A", "value": "2800 Hz"},
            {"name": "3 Gain A", "value": "-3.5 dB"},
            {"name": "3 Q A", "value": "2.2"},
            {"name": "4 Filter On A", "value": "1"},
            {"name": "4 Filter Type A", "value": "High Shelf"},
            {"name": "4 Frequency A", "value": "12000 Hz"},
            {"name": "4 Gain A", "value": "4.0 dB"}
        ]
    }
    
    params = eq_profiles.get(instrument.lower(), eq_profiles["vocal"])
    return f'live_create_device(track_index={track_index}, device_name="EQ Eight", params={params})'
```
