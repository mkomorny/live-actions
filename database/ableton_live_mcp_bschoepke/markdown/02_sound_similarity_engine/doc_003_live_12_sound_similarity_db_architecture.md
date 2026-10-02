---
id: 02_sound_similarity_engine_doc_003_live_12_sound_similarity_db_architecture
title: Live 12 Native Sound Similarity Database Architecture
category: 02_sound_similarity_engine
pages: 1
words: 860
source: 02_sound_similarity_engine/doc_003_live_12_sound_similarity_db_architecture.md
---
# Live 12 Native Sound Similarity Database Architecture

## 1. Overview of Ableton's Machine-Learning Audio Analysis

Ableton Live 12 introduced native **Sound Similarity Search**, allowing producers to click a similarity icon next to any drum hit, loop, or sample to instantly discover acoustically similar sounds across their entire library.

Under the hood, Live runs a background neural audio feature extractor that analyzes audio files and stores high-dimensional vector embeddings in a local SQLite database.

---

## 2. Database Locations on Windows & macOS

Live stores its analysis databases in the application cache:

- **Windows**:
  - `%LOCALAPPDATA%\Ableton\Live Database\Live-files-*.db`
  - (Typical location: `C:\Users\<you>\AppData\Local\Ableton\Live Database\Live-files-12300.db`, 562 MB)
- **macOS**:
  - `~/Library/Application Support/Ableton/Live Database/Live-files-*.db`

### Active Database Discovery Algorithm (`similar_sounds.py`)
```python
def latest_live_files_db() -> Path:
    db_dirs = [Path(os.environ["LOCALAPPDATA"]) / "Ableton" / "Live Database"]
    candidates = sorted(
        (path for db_dir in db_dirs for path in db_dir.glob("Live-files-*.db")),
        key=lambda item: item.stat().st_mtime,
        reverse=True
    )
    return candidates[0]
```

---

## 3. Database Schema & Tables

The `Live-files-*.db` database contains three primary tables:

1. **`files`**:
   - `id`: Integer primary key.
   - `path`: Normalized file path or content hash URI.
   - `name`: Clean audio filename (e.g. `Kick_Tight_808.wav`).
   - `size`: File size in bytes.
   - `mtime`: Last modified timestamp.

2. **`sound_analysis`**:
   - `file_id`: Foreign key referencing `files.id`.
   - `feature_vector`: Binary BLOB containing encoded audio features (spectral centroid, bark bands, MFCC-style timbre representations).
   - `duration`: Audio file length in seconds.
   - `sample_rate`: Original sample rate.

3. **`metadata`**:
   - Engine version and feature vector dimensionality metadata.
