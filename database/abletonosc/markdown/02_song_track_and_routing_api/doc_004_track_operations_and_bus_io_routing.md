# Track Operations, Mixer Control & Bus I/O Routing

> **Module:** `abletonosc.track`  
> **Upstream Handlers:** `TrackHandler`  
> **Key Capabilities:** Mixer faders, sends, submix bus routing, sidechain source assignment  

---

## 1. Mixer Properties & Track State

All track operations take `track_index` (0-indexed) as their first parameter:

| Property | Getter | Setter | Value Range / Description |
| :--- | :--- | :--- | :--- |
| **Volume** | `/live/track/get/volume <i>` | `/live/track/set/volume <i> <v>` | `0.0` to `1.0` (0.85 ~ 0 dB) |
| **Panning** | `/live/track/get/panning <i>` | `/live/track/set/panning <i> <v>` | `-1.0` (Hard Left) to `1.0` (Hard Right) |
| **Mute** | `/live/track/get/mute <i>` | `/live/track/set/mute <i> <v>` | `1` (Muted), `0` (Unmuted) |
| **Solo** | `/live/track/get/solo <i>` | `/live/track/set/solo <i> <v>` | `1` (Soloed), `0` (Unsoloed) |
| **Arm** | `/live/track/get/arm <i>` | `/live/track/set/arm <i> <v>` | `1` (Armed), `0` (Disarmed) |
| **Color** | `/live/track/get/color <i>` | `/live/track/set/color <i> <v>` | 24-bit RGB integer |
| **Name** | `/live/track/get/name <i>` | `/live/track/set/name <i> <v>` | String track label |

### Send Levels
- Query Send: `/live/track/get/send <track_index> <send_index>`
- Set Send: `/live/track/set/send <track_index> <send_index> <gain: float>`

---

## 2. Programmatic Input & Output Routing (Busses & Sidechain)

One of AbletonOSC's most powerful capabilities is full introspection and manipulation of track audio/MIDI signal routing:

### Input Routing Endpoints
- `/live/track/get/available_input_routing_types <track_index>`
- `/live/track/get/input_routing_type <track_index>`
- `/live/track/set/input_routing_type <track_index> <type_str>`
- `/live/track/get/available_input_routing_channels <track_index>`
- `/live/track/get/input_routing_channel <track_index>`
- `/live/track/set/input_routing_channel <track_index> <channel_str>`

### Output Routing Endpoints
- `/live/track/get/available_output_routing_types <track_index>`
- `/live/track/get/output_routing_type <track_index>`
- `/live/track/set/output_routing_type <track_index> <type_str>`
- `/live/track/get/available_output_routing_channels <track_index>`
- `/live/track/get/output_routing_channel <track_index>`
- `/live/track/set/output_routing_channel <track_index> <channel_str>`

### Automated Bus Routing Example:
To route Track 1 ("Kick") and Track 2 ("Snare") into Track 3 ("Drum Bus"):
```python
# 1. Query available outputs for Track 1
types = client.query("/live/track/get/available_output_routing_types", (1,))
# Match target track name "Drum Bus" in types:
client.send("/live/track/set/output_routing_type", 1, "Drum Bus")
client.send("/live/track/set/output_routing_type", 2, "Drum Bus")
```

---

## 3. Arrangement Timeline Clip Inspection

AbletonOSC allows querying clips placed on the arrangement timeline:

- `/live/track/get/arrangement_clips/name <track_index>`
- `/live/track/get/arrangement_clips/length <track_index>`
- `/live/track/get/arrangement_clips/start_time <track_index>`

This enables Genius to reconstruct the entire song arrangement structure directly from Live.
