# Third-party notices

Live Actions is published by DigiDreamWeaver under the MIT licence (see `LICENSE`). Some parts
are adapted from, or built on, work by other people. Their names, licences and what was taken are
listed here. Where a tool was given a new name for this app, the original name is shown.

## Code adapted into this repository

| In this repo | Adapted from | Author and licence |
|---|---|---|
| **Fill Forge** (`tools/fill-forge/`) | Breakdowns, <https://github.com/dnvsfn/ableton-breakdowns> | Copyright (c) 2026 E. T. Carter. MIT. Licence text: `tools/fill-forge/LICENSE` |
| **Song Mapper** (`tools/song-mapper/`) | Arrangement Helper, <https://github.com/federico-pepe/ableton-live-extensions> (`extensions/arrangement-helper`, v0.0.8) | Copyright (c) 2026 Federico P. MIT. Licence text: `tools/song-mapper/LICENSE` |
| Recipe engine and recipes (`app/recipes.py`, `app/recipes/`), session snapshot and diff (`app/session_verifier.py`) | ableton-mind, <https://github.com/Pantani/ableton-mind> | Copyright (c) 2026 ableton-mind contributors. MIT. Licence text: `app/recipes/LICENSE-ableton-mind.txt` |

Each tool folder has a `NOTICE.txt` describing what was kept and what was changed.

## Ideas and feature sets

No code was copied from these projects, but the choice of several Genius actions followed what
they offer, and they deserve the credit for the ideas:

- **Producer Pal** (<https://producer-pal.org>), GPL-3.0. The core `live_*` read/update/create
  actions cover the same jobs as Producer Pal's tools and follow its bar|beat note notation. Live
  Actions is an independent implementation on its own Max for Live device. It contains no
  Producer Pal code, does not use or modify the Producer Pal device, and is not affiliated with
  or endorsed by that project.
- **ableton-mcp-rest** (<https://github.com/EazyTom/ableton-mcp-rest>, MIT), based on AbletonMCP
  by Siddharth Ahuja: batch track operations, transport utilities, drum pad control.
- **ableton-mcp** (<https://github.com/mrinalghosh/ableton-mcp>, MIT): selection, envelope and
  pattern helpers.
- **ableton-ai** (<https://github.com/freekmurze/ableton-ai>, MIT): clip follow actions, launch
  modes, fades, markers, warp markers, automation shapes.

Key detection uses the published Krumhansl-Kessler and Temperley key profiles. Euclidean rhythms
use the Bjorklund algorithm.

## Fonts

`app/web/fonts/` holds Latin-subset WOFF2 files for 21 families, unmodified, from the Fontsource
packages (version 5.3.0). All are under the SIL Open Font License 1.1; the licence text for each
family is in the same folder (`LICENSE-<Family>.txt`, `OFL-DMSans.txt`, `OFL-SpaceMono.txt`).

Alfa Slab One, Archivo Narrow, Arimo, Caveat, Chakra Petch, DM Sans, Figtree, Hanken Grotesk,
Inconsolata, Inter, JetBrains Mono, Manrope, Oswald, Outfit, Plus Jakarta Sans, Public Sans,
Red Hat Mono, Roboto Mono, Rubik, Sofia Sans Extra Condensed, Space Mono.

## Knowledge database

The documents in `database/` are reference notes written for this app. Several summarise or draw
on other people's datasets and projects:

| Dataset | Draws on | Licence of the source |
|---|---|---|
| `ableton_god_producer` | "Ableton Live God-Level Beat Producer Dataset" by WithinUsAI (Hugging Face `11-47/ableton_god_producer_dataset`) | Apache 2.0 |
| `ableton_racks_labeled` | "ableton-racks-labeled" (Hugging Face `sixf0ur/ableton-racks-labeled`) | MIT |
| `ableton_mcp_extended` | <https://github.com/jpoindexter/ableton-mcp> | MIT |
| `ableton_live_mcp_bschoepke` | <https://github.com/bschoepke/ableton-live-mcp> | MIT |
| `abletonosc` | <https://github.com/ideoforms/AbletonOSC> | MIT |
| `mixology_db` | Figures reported for MixologyDB (University of Utah), which builds on Brecht De Man's Mix Evaluation Dataset and Mike Senior's Mixing Secrets multitracks | Summary statistics and commentary only; no audio or session files are included |
| `vital_synth_lab` | Public documentation of the Vital synthesizer's preset format | Original notes |
| `music_theory_basics` | Concepts as taught in *Open Music Theory* (CC BY-SA 4.0) and Novation's public Launchkey documentation | Original course text |

## Software this app uses but does not include

Installed by `pip` from `requirements.txt`, each under its own licence: NumPy, SciPy, soundfile,
pypdf, pyloudnorm, pywebview, pythonnet. Also used if present: ffmpeg, the Microsoft Edge
WebView2 Runtime.

Ableton, Live and Max for Live are trademarks of Ableton AG and Cycling '74. This project is not
affiliated with or endorsed by them.
