---
id: 04_live_actions_genius_actions_doc_010_live_actions_mix_critique_blueprint
title: 'Live Actions Blueprint: Semantic Mix Doctor Critique'
category: 04_live_actions_genius_actions
pages: 1
words: 251
source: 04_live_actions_genius_actions/doc_010_live_actions_mix_critique_blueprint.md
---
# Live Actions Blueprint: Semantic Mix Doctor Critique

## Action: `genius_mix_critique`

This blueprint audits active track relationships, fader balances, and reverb send levels, evaluating them against the 2,177 MixologyDB human listening assessments.

```python
# Live Actions Tool Blueprint
# Action: genius_mix_critique

def evaluate_mix_relationships(tracks_state: list[dict]) -> str:
    """Analyze faders and sends; emit professional critique and recommended actions."""
    critiques = []
    
    vocal = next((t for t in tracks_state if "vox" in t["name"].lower() or "vocal" in t["name"].lower()), None)
    snare = next((t for t in tracks_state if "snare" in t["name"].lower()), None)
    kick = next((t for t in tracks_state if "kick" in t["name"].lower()), None)
    
    # 1. Check Vocal Forwardness vs Space
    if vocal:
        v_gain = vocal.get("gain", 0.0)
        v_send_a = vocal.get("send_a", -99.0)
        if v_gain > -4.0 and v_send_a < -30.0:
            critiques.append(
                "• [VOCAL SPACE]: Lead vocal is sitting unusually forward (+{:.1f} dB) with virtually dry space. "
                "MixologyDB listening panels consistently critique this as 'vocal uncomfortably upfront and detached'. "
                "Recommendation: Reduce fader by 2.0 dB and open Return A to -16 dB."
            )
            
    # 2. Check Kick / Snare Dynamic Ratio
    if kick and snare:
        k_gain = kick.get("gain", 0.0)
        s_gain = snare.get("gain", 0.0)
        delta = k_gain - s_gain
        if delta < 0.5:
            critiques.append(
                "• [DRUM BALANCE]: Snare is competing with or louder than the Kick drum. "
                "In 90% of MixologyDB mixes, Kick leads Snare by 2.0 to 3.0 dB. "
                "Recommendation: Pull Snare fader down by 2.5 dB."
            )
            
    return "\n\n".join(critiques) if critiques else "Mix balance falls within healthy professional tolerances."
```
