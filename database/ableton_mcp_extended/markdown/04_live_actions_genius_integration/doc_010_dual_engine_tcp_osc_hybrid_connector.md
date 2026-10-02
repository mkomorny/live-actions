---
id: 04_live_actions_genius_integration_doc_010_dual_engine_tcp_osc_hybrid_connector
title: 'Dual-Engine Hybrid Topology: OSC Bridge (UDP 11924) & AbletonMCP (TCP 9877)'
category: 04_live_actions_genius_integration
pages: 1
words: 860
source: 04_live_actions_genius_integration/doc_010_dual_engine_tcp_osc_hybrid_connector.md
---
# Dual-Engine Hybrid Topology: OSC Bridge (UDP 11924) & AbletonMCP (TCP 9877)

## 1. The Dual-Engine Architectural Concept

Live Actions Helper combines two complementary communication protocols to achieve 100% Ableton Live control without modifying official third-party M4L devices:

```text
                               ┌─────────────────────────────┐
                               │   Live Actions Genius UI    │
                               │     (Chat / Execution)      │
                               └──────────────┬──────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
             UDP Port 11924 / 11925                             TCP Port 9877
                      ▼                                               ▼
     ┌─────────────────────────────────┐             ┌─────────────────────────────────┐
     │      Live Actions Bridge        │             │           AbletonMCP            │
     │      (Max for Live OSC)         │             │      (Python Remote Script)     │
     ├─────────────────────────────────┤             ├─────────────────────────────────┤
     │ • Real-time fader / pan updates │             │ • Retrospective Capture MIDI    │
     │ • Native instrument insertion   │             │ • Arrangement locators / cues   │
     │ • Calibrated EQ Eight curves    │             │ • Drum Rack pad inspection      │
     │ • Ticked audio/MIDI track scope │             │ • Programmatic browser loading  │
     │ • Zero external installation    │             │ • Re-ordering devices on track  │
     └─────────────────────────────────┘             └─────────────────────────────────┘
```

---

## 2. Python TCP Client Implementation in `helper.py`

A lightweight, robust socket client connecting directly to `localhost:9877`:

```python
import socket
import json
import logging

logger = logging.getLogger("AbletonMCP_Client")

class AbletonMCPClient:
    def __init__(self, host="localhost", port=9877, timeout=5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, payload: dict) -> dict:
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                msg_bytes = json.dumps(payload).encode("utf-8")
                sock.sendall(msg_bytes)
                
                # Receive buffer
                chunks = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    # Check for valid JSON termination
                    try:
                        raw = b"".join(chunks).decode("utf-8")
                        data = json.loads(raw)
                        return data
                    except (ValueError, json.JSONDecodeError):
                        continue
                
                raw = b"".join(chunks).decode("utf-8")
                return json.loads(raw)
        except Exception as exc:
            logger.warning(f"AbletonMCP socket call failed: {exc}")
            return {"status": "error", "message": str(exc)}
```

---

## 3. Intelligent Routing in Live Actions Genius

When a tool call arrives in `call_live_tool`:
1. **Core Live Actions (Track volume, pan, EQ Eight, standard device insert)**:
   Routed to the OSC Bridge (`bridge.call_live(...)`).
2. **Extended Live Actions (Capture MIDI, Locators, Drum Rack pad mute, Simpler info, Browser loading)**:
   Routed to `AbletonMCPClient().send({"type": cmd, "params": params})`.
3. **Graceful Fallback**:
   If `AbletonMCP` is not enabled in Live's Control Surfaces, Genius informs the user with a 1-click instruction to select `AbletonMCP` under Ableton Preferences > Link, Tempo & MIDI.
