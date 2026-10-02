---
id: 01_remote_script_engine_doc_002_version_evolution_and_server_interfaces
title: AbletonMCP Version Evolution & Multi-Interface Topology
category: 01_remote_script_engine
pages: 1
words: 850
source: 01_remote_script_engine/doc_002_version_evolution_and_server_interfaces.md
---
# AbletonMCP Version Evolution & Multi-Interface Topology

## 1. Version Evolution: v1.7.0 vs v2.0.0+

The user's local PC previously contained `AbletonMCP` v1.7.0 (108 KB) at `<User Library>\Remote Scripts\AbletonMCP`. The `jpoindexter/ableton-mcp` repository represents the **v2.0.0+ major overhaul (307 KB)**.

### Comparative Capabilities Matrix

| Architectural Dimension | Legacy v1.7.0 | Modern v2.0.0+ (Current Repo) |
| :--- | :--- | :--- |
| **Total LOM Commands** | ~85 commands | **257 unique commands** |
| **Script Code Size** | 108,659 bytes | **307,106 bytes** |
| **Arrangement Locators** | ❌ None | ✅ `create_locator`, `delete_locator`, `get_locators`, `jump_to_cue_point` |
| **Capture MIDI** | ❌ None | ✅ `capture_midi`, `get_can_capture_midi` (recovers unrecorded jams) |
| **Drum Rack Inspection** | Basic rack names | ✅ Full 128-pad scanning, pad mute/solo, pad renaming |
| **Simpler / Sampler** | Basic parameters | ✅ Full sample path, playback mode (Classic/1-Shot/Slice), warp |
| **Audio Clip Warping** | Read-only | ✅ `set_clip_warp_mode`, add/delete warp markers |
| **Follow Actions** | ❌ None | ✅ `set_clip_follow_action`, `get_clip_follow_action` |
| **AI Music Generation** | ❌ None | ✅ 8 Drum styles, 6 Bassline styles, 13 Scales reference |
| **Humanization / Quantize**| ❌ None | ✅ Micro-timing jitter, velocity humanization, grid quantize |
| **Device Re-ordering** | ❌ None | ✅ `move_device`, `move_device_left`, `move_device_right` |
| **Session Panic Resets** | ❌ None | ✅ `solo_exclusive`, `unsolo_all`, `unmute_all`, `unarm_all` |
| **Interface Modes** | MCP Stdio only | ✅ MCP Server, FastAPI REST API, Native Max for Live GUI |

---

## 2. Multi-Interface Architecture

The repository provides three distinct connectivity layers on top of the Remote Script:

### 1. Model Context Protocol (MCP) Server (`MCP_Server/server.py`)
- Standard stdio-based MCP server built with `mcp.server.fastmcp.FastMCP`.
- Exposes all 80+ high-level tools directly into Claude Desktop or Cursor AI.
- Translates tool invocations into JSON socket requests sent to `localhost:9877`.

### 2. FastAPI REST API Server (`MCP_Server/rest_api_server.py`)
- Runs a local HTTP REST server on `http://127.0.0.1:8000`.
- Provides HTTP POST endpoints for non-MCP agents (Ollama, local Python scripts, OpenAI, Groq).
- Features Swagger documentation at `http://127.0.0.1:8000/docs`.

### 3. Native Max for Live Device (`AbletonMCP_M4L/AbletonMCP.amxd`)
- Places an AI chat window directly inside an Ableton Live track.
- Communicates directly with the remote script socket without external CLI processes.

### 4. Live Actions Genius Integration (Live Actions Helper)
- Live Actions Helper connects directly via Python `socket.create_connection(("localhost", 9877))` inside `app/helper.py`.
- Completely avoids stdio subprocess overhead, giving Live Actions instantaneous sub-millisecond execution.
