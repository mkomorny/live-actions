Live Actions — tools folder
===========================

Each subfolder with a tool.json becomes a card on the main Actions screen.
Clicking the card opens that tool's own screen inside this app.

The tool screen includes the same track picker as the main screen.
A tool only touches the tracks you tick. It does not apply to the whole Set
unless you click All.

Working tools:

  Fill Forge            drum fills (own dialog)
  Song Mapper           build or re-edit an arrangement from named sections (own dialog)
  Clip Namer            rename session clips
  Arrangement Skeleton  Arrangement locators
  Mutate                variation clips from the selected MIDI clip
  Empty Clips           new empty MIDI clip per ticked MIDI track
  Color Clips           color clips (and optional scenes)
  Duplicate Clips       copy clips into empty slots
  Track Batch           rename / arm / mute / send
  Reveal Device         select Chord Explorer, Dub Assistant, etc.
  Detect Key            find the key/mode of a clip, ticked track(s), or the Set
  Audio Sample          ffmpeg sample prep -- trim, convert, effects, generators (runs on host, no bridge)
  TTS Vocal             spoken vocal from text, with your own TTS API key (runs on host)

Fill Forge and Song Mapper are adapted from MIT-licensed projects by other
authors. See the NOTICE.txt in each folder and THIRD-PARTY-NOTICES.md.

Re-drop Live Actions after a js change. install.ps1 tells you if the
device already in your Set is still running the old one.
