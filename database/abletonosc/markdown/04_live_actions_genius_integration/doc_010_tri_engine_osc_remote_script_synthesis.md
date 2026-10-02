# Grounded Tri-Engine Architectural Synthesis

> **Architecture:** Multi-Tiered DAW Control & Knowledge Layer  
> **Engines:** Engine 1 (M4L OSC), Engine 2 (Remote Script OSC/TCP), Engine 3 (Host Python)  

---

## 1. Unified Control Plane

By incorporating `ideoforms/AbletonOSC`, Live Actions Helper achieves complete protocol resilience:

```
+----------------------------------------------------------------------------------------------------+
|                                    LIVE ACTIONS GENIUS                                            |
|                                                                                                    |
|   +--------------------------+  +-------------------------------+  +----------------------------+   |
|   |   Engine 1: M4L OSC      |  |  Engine 2: Remote Scripts     |  |   Engine 3: Host Engine    |   |
|   |   (UDP 11924 / 11925)    |  |  (OSC 11000 + TCP 9877)       |  |   (Pure Python / SQLite)   |   |
|   +--------------------------+  +-------------------------------+  +----------------------------+   |
|                 |                               |                                |                 |
|   - Ticked track faders/pans     - 1-Shot Session JSON Dump      - 562MB Sound Similarity DB       |
|   - Parametric EQ Eight carving  - Bulk Multi-Track Queries      - Vital Preset & Baker            |
|   - Native device instantiation  - Hardware MIDI CC Mapping      - ASCII Grid Tab Compiler         |
|   - Sweet-spot randomizer        - Track I/O Bus Routing         - LERP Parameter Morpher          |
|   - Micro-timing humanizer       - Retrospective MIDI Capture    - Offline DawDreamer Bounces      |
|   - 0ms GUI reflection           - Timeline Locators & Cues      - Live Exec Escape Hatch          |
+-----------------|-------------------------------|--------------------------------|-----------------+
                  |                               |                                |
                  v                               v                                v
+----------------------------------------------------------------------------------------------------+
|                                      ABLETON LIVE 12 HOST                                          |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Operational Matrix & Redundancy

| Task | Primary Engine | Fallback Engine | Rationale |
| :--- | :--- | :--- | :--- |
| **Inspect Session** | Engine 2 (`/live/song/export/structure`) | Engine 1 (`live_read_set`) | JSON export takes 5ms for 50 tracks vs 50 sequential queries. |
| **Ticked Track Volume/Pan**| Engine 1 (M4L UDP 11924) | Engine 2 (AbletonOSC 11000) | M4L handles instantaneous UI updates with zero latency. |
| **Hardware MIDI CC Mapping**| Engine 2 (`/live/midimap/map_cc`) | Engine 1 (M4L parameters) | AbletonOSC directly triggers `request_rebuild_midi_map()`. |
| **Sound Similarity Search** | Engine 3 (Local SQLite Cosine) | Live 12 Browser GUI | 50ms sub-millisecond local vector matching. |
| **Submix Bus Routing** | Engine 2 (AbletonOSC Routing) | Manual User Action | AbletonOSC exposes `output_routing_type` directly. |
| **Note Generation** | Engine 3 (ASCII Grid / Euclidean) | Engine 1 / 2 Clip Notes | ASCII grid uses 80% fewer LLM tokens. |
