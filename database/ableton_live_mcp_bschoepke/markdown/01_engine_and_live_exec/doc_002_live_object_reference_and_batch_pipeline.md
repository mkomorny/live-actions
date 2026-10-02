---
id: 01_engine_and_live_exec_doc_002_live_object_reference_and_batch_pipeline
title: Live Object Model Reference Protocol & Atomic Batch Pipeline
category: 01_engine_and_live_exec
pages: 1
words: 820
source: 01_engine_and_live_exec/doc_002_live_object_reference_and_batch_pipeline.md
---
# Live Object Model Reference Protocol & Atomic Batch Pipeline

## 1. Structured Object References (`ref`)

Rather than passing ambiguous track or device numbers, `bschoepke/ableton-live-mcp` implements canonical path-based object references (`ref`):

- `live_set`: Root song object (`self.song()`).
- `live_set/tracks/0`: First audio/MIDI track.
- `live_set/tracks/0/devices/0`: First device on track 0.
- `live_set/tracks/0/devices/0/parameters/1`: Specific device parameter.
- `live_set/tracks/0/clip_slots/0/clip`: Clip on track 0, slot 0.
- `live_set/return_tracks/0`: First return track.
- `live_set/master_track`: Master track.

### Generic CRUD Operations
- `live_get(ref, properties)`: Reads targeted properties without serializing the entire track.
- `live_set(ref, property, value)`: Writes a property value directly to the object.
- `live_call(ref, method, args)`: Invokes an arbitrary LOM method on the target object.
- `live_children(ref, collection)`: Lists child objects from any collection.

---

## 2. Atomic Batch Operation Pipeline (`live_batch`)

When setting up complex mixing sessions or instrument chains, making dozens of discrete socket round-trips introduces network latency.

The `live_batch` tool packages multiple mutations into a single atomic payload executed sequentially on the main thread:

```json
{
  "operations": [
    {"method": "live_set", "params": {"ref": "live_set/tracks/0", "property": "name", "value": "Lead Synth"}},
    {"method": "live_set", "params": {"ref": "live_set/tracks/0/mixer_device", "property": "panning", "value": -0.25}},
    {"method": "live_call", "params": {"ref": "live_set/tracks/0/clip_slots/0", "method": "fire"}}
  ]
}
```

### Benefits
- **Zero Latency**: Executes all steps in a single Live main-thread frame.
- **Atomic Rollback**: If a step fails, the batch pipeline reports the exact operation index and error context.
