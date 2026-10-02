# OSC Address Schema, Wildcard Matching & Data Types

> **Module:** `abletonosc.osc_server`  
> **Schema Standard:** Open Sound Control (OSC 1.0)  
> **Addressing:** Hierarchical REST-style URI mapping  

---

## 1. OSC Address Space Structure

AbletonOSC uses a consistent, three-tier or four-tier hierarchical address schema:

```text
/live/<class>/<action>/<property_or_method> [target_indices...] [arguments...]
```

### Action Types
1. **Methods (`/live/<class>/<method>`)**: Executable operations (e.g. `/live/song/start_playing`, `/live/track/delete_device`).
2. **Getters (`/live/<class>/get/<property>`)**: Queries current state (e.g. `/live/track/get/volume 0`).
3. **Setters (`/live/<class>/set/<property>`)**: Mutates current state (e.g. `/live/track/set/volume 0 0.85`).
4. **Listeners (`/live/<class>/start_listen/<property>`)**: Registers asynchronous event callbacks.
5. **Listener Terminators (`/live/<class>/stop_listen/<property>`)**: Deregisters callbacks.

---

## 2. Argument & Indexing Conventions

- **0-Indexed Numbers**: Tracks, scenes, clip slots, devices, and parameters are all strictly 0-indexed integers.
- **Master & Return Tracks**:
  - Regular tracks: `0` to `num_tracks - 1`.
  - Master track: accessed via `/live/song/...` or specialized master handlers.
  - Return tracks: accessed via return track index conventions or dedicated APIs.
- **Wildcard Pattern Matching**:
  AbletonOSC natively supports OSC wildcard patterns:
  ```text
  /live/clip/get/* 0 0
  ```
  This queries **all** readable properties of Track 0, Clip 0 simultaneously, returning an atomic burst of replies!

---

## 3. Data Types & Representation

| OSC Type Tag | Python Type | Example | Typical Use |
| :--- | :--- | :--- | :--- |
| `i` (int32) | `int` | `0`, `42`, `127` | Track index, device index, MIDI pitch, velocity |
| `f` (float32) | `float` | `120.0`, `0.85`, `-6.0` | Tempo, fader gain, pan (-1.0 to 1.0), beat time |
| `s` (string) | `str` | `"Chorus"`, `"EQ Eight"` | Track names, cue labels, device types |
| `b` (blob) | `bytes` | `b'\x00...'` | Binary payloads (if utilized) |

---

## 4. PythonOSC Client Architecture

The standard client implementation uses `pythonosc` to provide both synchronous RPC queries and asynchronous event listening:

```python
import threading
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

class AbletonOSCClient:
    def __init__(self, host="127.0.0.1", send_port=11000, recv_port=11001):
        self.client = SimpleUDPClient(host, send_port)
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self._on_osc)
        self.handlers = {}
        self.server = ThreadingOSCUDPServer(("0.0.0.0", recv_port), self.dispatcher)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def send(self, address: str, *args):
        self.client.send_message(address, list(args))

    def query(self, address: str, *args, timeout: float = 0.150):
        result = None
        event = threading.Event()
        def callback(addr, *params):
            nonlocal result
            result = params
            event.set()
        self.handlers[address] = callback
        self.send(address, *args)
        event.wait(timeout)
        self.handlers.pop(address, None)
        if not event.is_set():
            raise TimeoutError(f"No response for {address}")
        return result

    def _on_osc(self, address, *args):
        if address in self.handlers:
            self.handlers[address](address, *args)
```
