---
id: 01_remote_script_engine_doc_001_socket_server_and_dispatch_architecture
title: AbletonMCP Socket Server & JSON Dispatch Architecture
category: 01_remote_script_engine
pages: 1
words: 820
source: 01_remote_script_engine/doc_001_socket_server_and_dispatch_architecture.md
---
# AbletonMCP Socket Server & JSON Dispatch Architecture

## 1. System Overview

**AbletonMCP** (`jpoindexter/ableton-mcp`) is a Python MIDI Remote Script running directly within Ableton Live's internal Python interpreter. It connects Ableton Live to external AI agents, LLMs, and client tools via a persistent TCP socket interface listening on **port 9877**.

```text
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Claude, App, CLI)             │
│   - Claude Desktop MCP Server (server.py)                   │
│   - Local REST API Server (rest_api_server.py)              │
│   - Live Actions Genius / Live Actions Helper (helper.py)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ TCP Socket (Port 9877)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Ableton Live Control Surface Engine           │
│   - Host: localhost (0.0.0.0 / 127.0.0.1)                   │
│   - Default Port: 9877                                      │
│   - Buffer Size: 1 MB (1,048,576 bytes)                     │
│   - Client Timeout: 300.0 seconds (5 min)                   │
│   - Max Concurrent Clients: 10                              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ Thread-Safe Command Dispatch
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Ableton Live Object Model (LOM)              │
│   - Song, Tracks, Return Tracks, Master                     │
│   - Clips, Notes, Envelopes, Warp Markers                   │
│   - Devices, Drum Rack Pads, Simpler, Racks                 │
│   - Cue Points / Locators, Transport, Views                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Communication Protocol & JSON Schema

All communication between the client and `AbletonMCP` occurs over raw TCP sockets using newline-delimited or buffer-flushed JSON objects.

### Request Format
Every incoming command is a JSON object with:
- `type` (string, required): The target command identifier (e.g. `"get_session_info"`, `"create_clip"`, `"capture_midi"`).
- `params` (object, optional): Key-value arguments specific to the command.

```json
{
  "type": "create_clip",
  "params": {
    "track_index": 0,
    "clip_index": 0,
    "length": 4.0
  }
}
```

### Response Format
Every response returns a structured JSON payload:
- `status` (string): `"success"` or `"error"`.
- `result` (any): Data payload returned on success (track list, parameters, confirmation).
- `message` (string, optional): Human-readable error message if `status == "error"`.

```json
{
  "status": "success",
  "result": {
    "track_index": 0,
    "clip_index": 0,
    "length": 4.0,
    "name": "Clip 1"
  }
}
```

---

## 3. Server Initialization & Thread Safety

Inside Ableton Live's `AbletonMCP/__init__.py`:

```python
class AbletonMCP(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.server = None
        self.client_threads = []
        self._threads_lock = threading.Lock()
        self.running = True
        self._song = self.song()
        self.start_server()

    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("localhost", 9877))
        self.server.listen(5)
        self.server_thread = threading.Thread(target=self._accept_clients)
        self.server_thread.daemon = True
        self.server_thread.start()
```

Each connected client spawns an isolated worker thread (`_handle_client`). Commands are parsed, synchronized with Live's application state, executed against the LOM, and returned immediately.
