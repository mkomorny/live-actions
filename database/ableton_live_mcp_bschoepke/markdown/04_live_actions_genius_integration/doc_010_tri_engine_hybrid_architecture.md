---
id: 04_live_actions_genius_integration_doc_010_tri_engine_hybrid_architecture
title: The Unified Tri-Engine Hybrid Architecture for Live Actions Genius
category: 04_live_actions_genius_integration
pages: 1
words: 860
source: 04_live_actions_genius_integration/doc_010_tri_engine_hybrid_architecture.md
---
# The Unified Tri-Engine Hybrid Architecture for Live Actions Genius

## 1. Overview of the Tri-Engine System

To achieve unmatched power, rock-solid reliability, and zero third-party device modifications, **Live Actions Helper / Live Actions Genius** adopts a **Tri-Engine Hybrid Architecture**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Live Actions Genius (LLM Chat)                      │
│                    C:\Users\<you>\My Apps\Live Actions Helper            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  ENGINE 1 (OSC)  │         │  ENGINE 2 (TCP)  │         │ ENGINE 3 (LOCAL) │
│ Live Actions M4L │         │  AbletonMCP 9877 │         │ Python & SQLite  │
├──────────────────┤         ├──────────────────┤         ├──────────────────┤
│ • Real-time UDP  │         │ • Capture MIDI   │         │ • 562MB Similar  │
│ • Volume, pan    │         │ • Locators / cue │         │   Sounds DB      │
│ • EQ Eight carve │         │ • Drum pad mutes │         │ • DawDreamer WAV │
│ • Native devices │         │ • Browser load   │         │ • live_exec hook │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

---

## 2. Division of Labor Across Engines

### Engine 1: Max for Live OSC Bridge (`Live Actions Bridge.amxd` on UDP 11924)
- Handles core, high-speed DAW transport, fader mixing, device parameter adjustments, and ticked-track scope.
- Zero external Python dependencies; 100% stable inside Live 12 Standard.

### Engine 2: AbletonMCP Python Remote Script (`localhost:9877`)
- Handles complex LOM operations unexposed to Max for Live:
  - Retrospective Capture MIDI.
  - Linear Arrangement cue markers/locators.
  - Drum Rack 128-pad inspection & pad-level muting.
  - Programmatic browser item loading (`browser.load_item`).

### Engine 3: Local Host Desktop Engine (`app/helper.py`)
- Executes offline, heavy-compute operations:
  - Sound Similarity vector searches across `Live-files-12300.db`.
  - Offline Vital WAV baking via DawDreamer faster-than-realtime.
  - Arbitrary Python `live_exec` evaluation hooks.

---

## 3. Implementation in `genius_client.py`

When the agent receives a request:
1. It selects the appropriate engine automatically based on the action type.
2. The user experiences an effortless, unified natural language co-producer that can do anything possible in Ableton Live!
