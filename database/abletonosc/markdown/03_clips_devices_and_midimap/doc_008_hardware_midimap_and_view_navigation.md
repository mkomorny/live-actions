# Hardware MIDI Mapping & GUI View Navigation

> **Module:** `abletonosc.midimap`, `abletonosc.view`  
> **Upstream Handlers:** `MidiMapHandler`, `ViewHandler`  
> **Key Capabilities:** Programmatic MIDI CC binding, GUI focus management  

---

## 1. Dynamic Hardware MIDI Mapping (`/live/midimap/map_cc`)

AbletonOSC includes a specialized handler for binding any physical or virtual MIDI CC directly to any device parameter:

```python
# In midimap.py:
def make_midi_map(params):
    track_index = int(params[0])
    device_index = int(params[1])
    parameter_index = int(params[2])
    channel = int(params[3])
    cc = int(params[4])

    parameter = self.song.tracks[track_index].devices[device_index].parameters[parameter_index]
    self.manager.midi_mappings[(channel, cc)] = parameter
    self.manager.request_rebuild_midi_map()
```

### Command Syntax:
```text
/live/midimap/map_cc <track_index> <device_index> <parameter_index> <midi_channel> <midi_cc>
```

### Applications for Live Actions Helper:
1. **Novation Launchkey MK4 Custom Modes**: Bind physical faders and encoders to specific track devices on demand.
2. **Loopback MIDI Automation**: Use Windows MIDI Services / LoopMIDI to automate un-exposed parameters via high-speed MIDI CC streams.
3. **Hardware Macro Knobs**: Assign external physical knobs to rack macros without manual MIDI learn.

---

## 2. GUI View Navigation & Selection

AbletonOSC allows reading and altering what is currently highlighted in Live's GUI:

### Selected Track:
- Query: `/live/view/get/selected_track` -> returns `track_index`.
- Select: `/live/view/set/selected_track <track_index>`
- Listen: `/live/view/start_listen/selected_track`

### Selected Scene:
- Query: `/live/view/get/selected_scene` -> returns `scene_index`.
- Select: `/live/view/set/selected_scene <scene_index>`

### Selected Clip:
- Query: `/live/view/get/selected_clip` -> returns `(track_index, scene_index)`.
- Select: `/live/view/set/selected_clip <track_index> <scene_index>`

### Selected Device:
- Query: `/live/view/get/selected_device` -> returns `(track_index, device_index)`.
- Select: `/live/view/set/selected_device <track_index> <device_index>`
