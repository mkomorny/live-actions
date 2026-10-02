---
id: 04_live_actions_genius_actions_doc_008_live_actions_auto_balance_blueprint
title: 'Live Actions Blueprint: Multi-Track Auto Balance'
category: 04_live_actions_genius_actions
pages: 1
words: 185
source: 04_live_actions_genius_actions/doc_008_live_actions_auto_balance_blueprint.md
---
# Live Actions Blueprint: Multi-Track Auto Balance

## Action: `genius_auto_gain_stage`

This blueprint automatically queries active tracks in an Ableton Live Set, matches track names to standard instrument classifications, and applies empirical MixologyDB gain staging and stereo panning.

```python
# Live Actions Tool Blueprint
# Action: genius_auto_gain_stage

def apply_mixology_balance(live_set_data: dict, genre: str = "ROCK") -> list[dict]:
    """Calculate and emit fader and pan updates for active tracks."""
    actions = []
    
    # MixologyDB Target Profiles (Mean dB)
    target_faders = {
        "kick": -5.0,
        "snare": -7.5,
        "hihat": -14.0,
        "overheads": -8.0,
        "bass": -6.0,
        "vocal": -6.5,
        "guitar": -8.5,
        "keys": -5.5
    }
    
    for track in live_set_data.get("tracks", []):
        t_idx = track["index"]
        t_name = track["name"].lower()
        
        # Determine classification
        for key, target_gain in target_faders.items():
            if key in t_name:
                actions.append({
                    "tool": "live_update_track",
                    "args": {"track_index": t_idx, "gain_db": target_gain}
                })
                break
                
        # Stereo panning rules
        if "overhead" in t_name or "oh" in t_name:
            actions.append({"tool": "live_update_track", "args": {"track_index": t_idx, "pan": -0.75 if "l" in t_name else 0.75}})
        elif "rhythm" in t_name and "gtr" in t_name:
            actions.append({"tool": "live_update_track", "args": {"track_index": t_idx, "pan": -0.6 if "1" in t_name else 0.6}})
            
    return actions
```
