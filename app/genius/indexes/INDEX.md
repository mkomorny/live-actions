# Genius library index

This is the map Genius reads first. It ships with the app and describes the bundled knowledge
database. If you put your own `INDEX.md` in your Knowledge folder (Preferences → Folders), Genius
reads yours instead.

## Decide first

| The ask is about… | Search here | Then in Live |
|---|---|---|
| A beat in a named genre (trap, house, techno, drill, D&B, UK garage, lo-fi, jungle, phonk…) | `library_db_search` topic `ableton_god_producer` | `live_create_device` Drum Rack, `live_write_notes` |
| Bass sound design (808s, sub, Operator, Vital, Serum-style patches) | `ableton_god_producer`, then `vital_synth_lab` | `live_create_device`, `live_update_device` |
| "How is this kind of rack built?" (amps, vocal chains, drum buses, creative FX) | `ableton_racks_labeled` | `live_create_device`, `live_read_macros`, `live_update_macro` |
| Levels, panning, headroom, EQ moves per instrument, "what's wrong with my mix" | `mixology_db` | `live_analyze_mix`, `live_analyze_audio`, `live_update_device` EQ Eight |
| Vital presets, wavetables, rendering a patch, translating a patch to Drift or Wavetable | `vital_synth_lab` | `live_create_device` Drift / Wavetable |
| Notes, intervals, scales, chords, keys, rhythm basics | `music_theory_basics` | `live_generate_chords`, `live_write_notes`, `live_detect_key` |
| How other Ableton remote-control projects do something (OSC addresses, Remote Script commands) | `abletonosc`, `ableton_mcp_extended`, `ableton_live_mcp_bschoepke` | `live_api` only if no `live_*` tool covers it |
| Anything else | `library_db_search` with topic `?` to list every dataset, including the user's own | — |

## Rules

1. Search the database before answering from memory. Quote the document and section you used.
2. If nothing matches, try `library_search` over the user's Knowledge folder, then say plainly
   that the library has nothing on it and answer from general knowledge, labelled as such.
3. Read the Set (`live_connect`, `live_read_set`) before changing it.
4. Never invent a device or parameter name. Use the names `live_read_device` or
   `live_inspect_plugin` returned.

## Your own material

- **Knowledge folder**: drop `.md`, `.txt` or `.pdf` files in it. `library_search` finds them by
  name and `library_read` opens them.
- **Your own dataset**: make `database/<name>/markdown/`, add Markdown files, run
  `python database/build_database.py <name>`. It then shows up under topic `?` as `<name>`.
