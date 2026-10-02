---
id: 01_engine_and_live_exec_doc_001_arbitrary_python_execution_engine
title: 'Arbitrary Python Execution Engine: live_eval and live_exec'
category: 01_engine_and_live_exec
pages: 1
words: 850
source: 01_engine_and_live_exec/doc_001_arbitrary_python_execution_engine.md
---
# Arbitrary Python Execution Engine: live_eval and live_exec

## 1. The Architectural Bottleneck of Static LOM Wrappers

Most Ableton Live API bridges and MCP servers implement fixed, static command dictionaries (e.g. `set_tempo`, `create_clip`, `set_volume`). When an AI agent encounters a task outside these pre-defined wrappers—such as interrogating complex third-party VST parameter hierarchies, reading tuning systems, or manipulating comping take lanes—it hits a brick wall.

**`bschoepke/ableton-live-mcp` solves this permanently by exposing `live_eval` and `live_exec`.**

```text
┌────────────────────────────────────────────────────────┐
│               Live Actions Genius (LLM)                │
└───────────────────────────┬────────────────────────────┘
                            │
                            │  live_exec(code="...")
                            ▼
┌────────────────────────────────────────────────────────┐
│              Python Remote Socket Bridge               │
│  - Receives Python code string                         │
│  - Wraps in main-thread task execution                 │
│  - Injects local context: self, song, selected_track   │
└───────────────────────────┬────────────────────────────┘
                            │
                            │  Live Application Main Thread
                            ▼
┌────────────────────────────────────────────────────────┐
│            Ableton Live Internal Interpreter           │
│  - Native C++ Boost.Python bindings                    │
│  - Zero wrapper limitations                            │
│  - Returns serialized JSON or raw python values        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Tool Signatures & Execution Semantics

### `live_eval`
Evaluates a single Python expression and returns its evaluated representation.
- `expr` (string, required): The Python expression (e.g. `"[t.name for t in self.song().tracks]"`).
- `ref` (string, optional): Target object reference to bind as `this` or `target`.
- `allow_legacy_note_api` (bool): Toggles support for pre-Live 11 note APIs.

### `live_exec`
Executes full Python code blocks with loops, variable assignments, and complex logic directly inside Live.
- `code` (string, required): Multi-line Python script.
- `ref` (string, optional): Contextual object reference.

```python
# Example: Inspecting specific plugin parameters dynamically
code = """
track = self.song().tracks[0]
synth = track.devices[0]
results = []
for p in synth.parameters:
    if "cutoff" in p.name.lower() or "filter" in p.name.lower():
        results.append({"name": p.name, "value": p.value, "str": str(p)})
return_val = results
"""
response = client.call("live_exec", {"code": code})
```

---

## 3. Safety Guardrails & Thread Synchronization

1. **Main Thread Dispatch**: All code passed to `live_exec` is scheduled onto Live's main GUI thread via the Control Surface's task manager. This prevents threading race conditions and fatal crashes.
2. **Execution Sandboxing**: While code executes with full interpreter privileges, execution timeouts prevent infinite loops from hanging Ableton Live's UI thread.
