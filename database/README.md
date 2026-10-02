# Knowledge database

This folder is what Genius searches (`library_db_search`) before it answers a production question
from memory. It ships built and ready; the installer does not download anything.

## What is included

| Topic key | Contents |
|---|---|
| `ableton_god_producer` | Beat-making recipes by genre: drum programming, bass sound design, mixing and mastering chains |
| `ableton_racks_labeled` | 134 preset racks described: signal chain, devices, settings, macros |
| `mixology_db` | Mix engineering reference: gain and pan ratios by genre, EQ curves per instrument, mix-critique rules |
| `vital_synth_lab` | Vital synth: preset format, rendering, wavetables, translating patches to Live's own synths |
| `music_theory_basics` | A beginner music theory course with keyboard practice |
| `ableton_mcp_extended` | Notes on the jpoindexter/ableton-mcp project |
| `ableton_live_mcp_bschoepke` | Notes on the bschoepke/ableton-live-mcp project |
| `abletonosc` | Notes on the ideoforms/AbletonOSC project |

About 210 documents, under 4 MB. Sources and licences are listed in
[`../THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md).

It is deliberately small. It contains no commercial books, no paid course material and no vendor
manuals, because those cannot be redistributed. If you own such material, add it yourself (below);
it stays on your PC.

Each dataset folder holds:

- `markdown/`: the documents, as plain Markdown
- `<name>.db`: a SQLite full-text index built from them
- `search.py`: the search command the app runs

## Add your own dataset

1. Make a folder here with a `markdown` subfolder, for example `database/my_notes/markdown/`.
2. Put `.md` files in it. Subfolders become categories. An optional header sets the title:

   ```markdown
   ---
   title: Parallel compression on drums
   category: mixing
   ---
   # Parallel compression on drums
   ...
   ```

3. Build it:

   ```powershell
   .venv\Scripts\python database\build_database.py my_notes
   ```

4. Ask Genius "what datasets can you search?" Yours appears as `my_notes`.

Run the build again after you change the Markdown. Running it with no name rebuilds everything.

Try a search from the command line:

```powershell
.venv\Scripts\python database\mixology_db\search.py "kick drum eq" --limit 3
```

## Use a different database folder

Set **Preferences → Folders → Music / audio database folder** to any folder laid out the same way
(one subfolder per dataset, each with its own `search.py` that accepts
`<query> --limit N --json` and prints a JSON list).

## Loose files instead

For a handful of notes or a PDF manual you own, the `knowledge/` folder is simpler: drop files in
and Genius finds them by name.
