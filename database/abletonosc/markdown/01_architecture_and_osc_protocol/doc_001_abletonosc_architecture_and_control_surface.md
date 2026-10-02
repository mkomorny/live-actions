# AbletonOSC Architecture & Control Surface Foundation

> **Module:** `abletonosc` (Remote Script / Control Surface)  
> **Upstream Repository:** `ideoforms/AbletonOSC`  
> **Target Environment:** Ableton Live 10, 11, 12 (Windows / macOS)  
> **Network Protocol:** Open Sound Control (OSC 1.0) over UDP  

---

## 1. Executive Summary & Philosophy

AbletonOSC is an open-source MIDI Remote Script (Control Surface) for Ableton Live that embeds an asynchronous Open Sound Control (OSC) server directly inside Ableton Live's internal Python interpreter.

Unlike Max for Live bridges (which must be instantiated as an audio effect device on a track and operate within Max's thread boundaries), AbletonOSC operates at the root application level. It provides zero-latency, bi-directional control over the entire Live Object Model (LOM) without requiring Max for Live installed on any track.

```
+-------------------------------------------------------------------------+
|                           Ableton Live Host                             |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |           Native Python Interpreter (Control Surface Engine)       |  |
|  |                                                                   |  |
|  |  +-------------------------------------------------------------+  |  |
|  |  |                   AbletonOSC Remote Script                  |  |  |
|  |  |                                                             |  |  |
|  |  |   [OSC Server UDP 11000]          [OSC Client UDP 11001]   |  |  |
|  |  |          ^                                  |               |  |  |
|  |  +----------|----------------------------------|---------------+  |  |
|  |             |                                  |                  |  |
|  |             v                                  v                  |  |
|  |     Live Object Model (Song, Tracks, Clips, Devices, View)        |  |
|  +-------------------------------------------------------------------+  |
+----------------|----------------------------------^---------------------+
                 |                                  |
     Incoming OSC Commands                 Outgoing OSC Replies & Events
                 |                                  |
+----------------|----------------------------------|---------------------+
|  Live Actions Genius / Live Actions Helper (Host Engine / Client)      |
|  PythonOSC Client (Port 11000)        PythonOSC Server (Port 11001)     |
+-------------------------------------------------------------------------+
```

---

## 2. Network Specifications & Port Allocation

AbletonOSC adheres to strict, predictable network port assignments:

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Incoming Port** | `11000` | UDP port on which AbletonOSC listens for commands. |
| **Reply Port** | `11001` | UDP port to which AbletonOSC sends replies and property streams. |
| **Bind Interface** | `0.0.0.0` | Listens on all local network interfaces (accessible via `127.0.0.1`). |
| **Response Destination** | Client IP | Automatically transmits replies to the IP address of the incoming packet. |

---

## 3. Installation & Lifecycle Management

### Installation Paths
To install AbletonOSC as a Control Surface:
- **Windows**: `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\AbletonOSC`
- **macOS**: `~/Music/Ableton/User Library/Remote Scripts/AbletonOSC`

### Activation in Live Preferences
1. Open Ableton Live `Preferences > Link / Tempo / MIDI`.
2. Under **Control Surface**, select `AbletonOSC`.
3. In Live's status bar at the bottom, Live outputs:
   `AbletonOSC: Listening for OSC on port 11000`

### Logging & Diagnostics
AbletonOSC outputs logs into `Remote Scripts/AbletonOSC/logs/abletonosc.log`.  
The logging level can be dynamically queried or updated via OSC:
- Query level: `/live/api/get/log_level` -> returns `"debug"`, `"info"`, `"warning"`, or `"error"`.
- Set level: `/live/api/set/log_level "debug"`
- Status bar notification: `/live/api/show_message "Genius Connected"`

---

## 4. Handler Hierarchy & Dispatch Model

AbletonOSC organizes all functionality into modular handlers inheriting from `AbletonOSCHandler`:
- `SongHandler`: Transport, tempo, time signature, cue points, track creation, bulk queries.
- `TrackHandler`: Volume, pan, mute, solo, arm, sends, I/O routing, device lists, clip lists.
- `ClipHandler`: Playback, loop bounds, warp modes, 5-tuple MIDI note editing.
- `ClipSlotHandler`: Slot triggering, clip creation/deletion, recording status.
- `DeviceHandler`: Parameter name, value, min, max, quantization reflection, batch setting.
- `MidiMapHandler`: Physical/virtual MIDI CC binding to arbitrary LOM parameters.
- `ViewHandler`: Selected scene, track, clip, and device inspection and navigation.
