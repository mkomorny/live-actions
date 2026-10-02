# Song Control, Cue Points & Real-Time Beat Clock

> **Module:** `abletonosc.song`  
> **Upstream Handlers:** `SongHandler`  
> **Key Capabilities:** Transport, Locators, Arrangement Markers, Real-Time Beat Event Listener  

---

## 1. Global Transport & Song Methods

AbletonOSC exposes comprehensive global song management:

| OSC Address | Query Parameters | Description |
| :--- | :--- | :--- |
| `/live/song/start_playing` | (none) | Starts session playback. |
| `/live/song/stop_playing` | (none) | Stops playback. |
| `/live/song/continue_playing` | (none) | Resumes playback from current position. |
| `/live/song/stop_all_clips` | (none) | Stops all active playing clips across all tracks. |
| `/live/song/tap_tempo` | (none) | Triggers a virtual tap of the Tap Tempo button. |
| `/live/song/trigger_session_record` | (none) | Toggles session recording mode. |
| `/live/song/capture_midi` | (none) | Triggers Live's retrospective Capture MIDI. |
| `/live/song/undo` / `/live/song/redo` | (none) | Global undo / redo stack manipulation. |
| `/live/song/jump_by` | `time: float` | Jumps playback head by relative beats (+4.0, -8.0). |

---

## 2. Read/Write Song Properties

Queried via `/live/song/get/<property>` and modified via `/live/song/set/<property> <value>`:

| Property | Type | Range / Description |
| :--- | :--- | :--- |
| `tempo` | `float` | `20.0` to `999.0` BPM. |
| `signature_numerator` | `int` | e.g. `4`, `3`, `7`. |
| `signature_denominator` | `int` | e.g. `4`, `8`, `16`. |
| `current_song_time` | `float` | Current playhead position in beats. |
| `loop` | `int` | `1` = Loop enabled, `0` = Loop disabled. |
| `loop_start` | `float` | Loop start point in beats. |
| `loop_length` | `float` | Loop length in beats. |
| `metronome` | `int` | `1` = On, `0` = Off. |
| `groove_amount` | `float` | Global groove intensity (`0.0` to `1.0`). |
| `clip_trigger_quantization` | `int` | Global launch quantization setting. |

---

## 3. Cue Point (Locator) Navigation & Renaming

AbletonOSC provides direct semantic navigation to arrangement locators:

### 1. Querying All Cue Points
```text
/live/song/get/cue_points
```
Returns a flat tuple of pairs: `(name_1, time_1, name_2, time_2, ...)`.

### 2. Semantic Jumping by Name or Index
```text
/live/song/cue_point/jump "Chorus"
/live/song/cue_point/jump 2
```
If a string is passed, AbletonOSC scans `song.cue_points` for a matching `cue_point.name` and immediately jumps the playback position.

### 3. Creating & Renaming Locators
- Toggle locator at playhead: `/live/song/cue_point/add_or_delete`
- Set name: `/live/song/cue_point/set/name <cue_index: int> <name: str>`

---

## 4. Real-Time Beat Event Listener (`/live/song/start_listen/beat`)

AbletonOSC provides a built-in beat clock emitter:

```python
# In song.py:
def start_beat_listener(params):
    self.song.add_current_song_time_listener(self.current_song_time_changed)

def current_song_time_changed(self):
    if (self.song.current_song_time < self.last_song_time) or \
            (int(self.song.current_song_time) > int(self.last_song_time)):
        self.osc_server.send("/live/song/get/beat", (int(self.song.current_song_time),))
    self.last_song_time = self.song.current_song_time
```

### Usage:
1. Send `/live/song/start_listen/beat`
2. Every time Live's transport crosses an integer beat boundary (quarter note), AbletonOSC transmits:
   ```text
   /live/song/get/beat <current_beat: int>
   ```
3. To stop: send `/live/song/stop_listen/beat`.
