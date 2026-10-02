# Live Actions

A desktop companion for Ableton Live 12 on Windows, by DigiDreamWeaver.

Live Actions sits beside Live and does two things:

- **Tools**: one-click jobs on the tracks you tick, such as naming clips, colouring them, building
  an arrangement from named sections, writing drum fills, detecting the key.
- **Genius**: an AI assistant that can read your Set and change it. You type a request, it calls
  some of its 128 actions (create tracks and clips, write MIDI, load and set devices, write
  automation, analyse audio), and tells you what it did.

It talks to Live through its own Max for Live device and, optionally, a small Remote Script for
Live's browser. Everything runs on your PC.

> **Genius needs your own API key.** No key is included. To use Genius you need an account and an
> API key with xAI, OpenAI, Google (Gemini) or Anthropic, and that provider bills you for what you
> use. The Tools work without any key. See [API keys and privacy](#api-keys-and-privacy).

## What you need

- Windows 10 or 11
- Ableton Live 12 with Max for Live (Live Suite, or Standard with the Max for Live add-on).
  Native device insertion needs Live 12.3 or newer.
- Python 3.10 or newer (3.12 recommended), from [python.org](https://www.python.org/downloads/)
- Microsoft Edge WebView2 Runtime (already present on most Windows 11 PCs)
- Optional: [ffmpeg](https://ffmpeg.org/), for the Audio Sample and TTS Vocal tools

## Install

```powershell
git clone https://github.com/mkomorny/live-actions.git
cd live-actions
powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer creates a private `.venv`, installs the Python packages, copies the device into
your Ableton User Library, and adds a Desktop shortcut. It needs no admin rights and never asks
for an API key. Full steps and troubleshooting are in [INSTALL.md](INSTALL.md).

Then:

1. In Live, drag **User Library → Presets → Audio Effects → Max Audio Effect → Live Actions**
   onto any track. Audio passes through it unchanged.
2. Open **Live Actions** from the Desktop shortcut. The badge turns green when it hears the device.
3. Tick some tracks and try a tool.

## Tools (no API key needed)

| Tool | What it does |
|---|---|
| Clip Namer | Rename Session clips from a pattern |
| Color Clips | Colour clips, and optionally scenes |
| Empty Clips | A new empty MIDI clip on each ticked MIDI track |
| Duplicate Clips | Copy each track's clips into its empty slots |
| Mutate | Variation clips from the selected MIDI clip |
| Track Batch | Rename, arm, mute or set sends on many tracks |
| Arrangement Skeleton | Lay out Arrangement locators |
| Song Mapper | Build or re-edit an arrangement from named, coloured sections |
| Fill Forge | Drum fills by genre and technique; audition before inserting |
| Detect Key | Key and mode of a clip, tracks or the whole Set |
| Reveal Device | Jump to a named device |
| Audio Sample | Trim, convert and process audio files (needs ffmpeg) |
| TTS Vocal | Spoken vocal from text (needs ffmpeg and your own TTS key) |

A tool only touches the tracks you tick.

## Genius

Open the Genius tab, add a key under **Preferences → AI provider**, pick a model, and ask:

- "Read my Set and tell me what's in it."
- "Write a 4-bar bassline in F# minor on the Bass track."
- "Make a techno drum pattern at 132 and put a Drum Rack on a new track."
- "What's clashing in my low end?"

The six PDFs in [`Genius User Guide/`](Genius%20User%20Guide/) cover what it can do, good
prompts, and its limits.

### The knowledge database

Genius answers production questions from a small bundled database in [`database/`](database/)
before it answers from memory: beat-making recipes by genre, preset-rack breakdowns, mix
engineering figures, Vital sound design, beginner music theory, and notes on other Ableton
remote-control projects. It installs with the app; there is nothing to download.

You can add your own. Put notes or manuals in the `knowledge/` folder, or build a searchable
dataset from Markdown. See [database/README.md](database/README.md).

## API keys and privacy

- **You supply the key.** Genius does nothing until you paste a key from xAI, OpenAI, Google or
  Anthropic. Usage is billed to you by that provider, at their prices. The model picker shows an
  approximate price per million tokens; check your provider for the real figure.
- **Where the key is kept.** In `%APPDATA%\Live Actions\settings.json` on your PC, as plain text.
  It is not in this folder and is never sent anywhere except to the provider it belongs to.
  Anyone who can read your Windows user profile can read it, so treat that file like a password.
- **What is sent to the provider.** What you type, the action results Genius reads back (track
  names, clip contents, device settings), and any knowledge-database passages it looks up. Audio
  files and your project file are not uploaded. TTS Vocal sends the text you approve to your TTS
  provider.
- **Nothing else phones home.** There is no telemetry and no account.

## Disclaimer

Live Actions changes your Live Set. Save before you let Genius make large edits; some multi-step
actions are many separate undo steps. An AI model can misunderstand a request or describe work
it did not do, so check the result. The software is provided as is, with no warranty; see
[LICENSE](LICENSE).

This project is not affiliated with or endorsed by Ableton, Cycling '74, or Producer Pal.

## Credits

Fill Forge and Song Mapper are adapted from MIT-licensed tools by E. T. Carter and Federico P.,
and the recipe engine from the ableton-mind project. Full credits, including the sources behind
the knowledge database and the bundled fonts, are in
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Folder layout

| Folder | Contents |
|---|---|
| `app/` | The desktop app (Python) and its web UI |
| `bridge/` | The Max for Live device and its scripts |
| `remote_script/` | The optional browser Remote Script (LiveActionsRS) |
| `tools/` | One folder per tool card |
| `database/` | The bundled knowledge database and its builder |
| `knowledge/` | Empty; for your own notes and manuals |
| `Genius User Guide/` | Six PDF guides |
| `docs/guide-v2-build/` | The scripts that generate those PDFs |

To run the tests: `cd app` then `python -m unittest discover -p "test_*.py"`.

## Licence

MIT. Copyright (c) 2026 DigiDreamWeaver. Parts adapted from other authors keep their own
copyright and licence; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
