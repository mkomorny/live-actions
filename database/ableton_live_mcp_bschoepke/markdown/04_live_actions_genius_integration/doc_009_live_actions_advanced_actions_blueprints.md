---
id: 04_live_actions_genius_integration_doc_009_live_actions_advanced_actions_blueprints
title: 'Live Actions Genius Blueprints: Advanced Live Actions Suite'
category: 04_live_actions_genius_integration
pages: 1
words: 850
source: 04_live_actions_genius_integration/doc_009_live_actions_advanced_actions_blueprints.md
---
# Live Actions Genius Blueprints: Advanced Live Actions Suite

## 1. Blueprint: Live 12 Sound Similarity Search (`live_find_similar_sounds`)

```python
def live_find_similar_sounds(reference_sample: str, limit: int = 5):
    """Queries Ableton Live 12's local 562MB Sound Similarity database."""
    import sqlite3, struct, math, os
    from pathlib import Path

    db_path = Path(os.environ["LOCALAPPDATA"]) / "Ableton" / "Live Database" / "Live-files-12300.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Query target embedding
    cur.execute("SELECT id, feature_vector FROM files JOIN sound_analysis ON files.id=sound_analysis.file_id WHERE path LIKE ? LIMIT 1", (f"%{reference_sample}%",))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"ok": False, "message": f"Sample '{reference_sample}' not found in similarity DB."}

    ref_id, blob = row
    ref_vec = list(struct.unpack(f"<{(len(blob)-12)//4}f", blob[12:]))

    # Fast scan top candidates
    cur.execute("SELECT files.path, sound_analysis.feature_vector FROM files JOIN sound_analysis ON files.id=sound_analysis.file_id WHERE files.id != ? LIMIT 2000", (ref_id,))
    candidates = cur.fetchall()
    conn.close()

    scores = []
    for path, c_blob in candidates:
        c_vec = list(struct.unpack(f"<{(len(c_blob)-12)//4}f", c_blob[12:]))
        dot = sum(a * b for a, b in zip(ref_vec, c_vec))
        norm_a = math.sqrt(sum(a * a for a in ref_vec))
        norm_b = math.sqrt(sum(b * b for b in c_vec))
        dist = 1.0 - (dot / (norm_a * norm_b)) if norm_a and norm_b else 1.0
        scores.append((dist, Path(path).name, path))

    scores.sort(key=lambda x: x[0])
    results = [{"name": s[1], "path": s[2], "distance": round(s[0], 4)} for s in scores[:limit]]
    return {"ok": True, "matches": results}
```

---

## 2. Blueprint: Arbitrary Python Execution (`live_exec_python`)

```python
def live_exec_python(code_snippet: str):
    """Runs arbitrary Python code directly on Ableton Live's main thread."""
    client = get_socket_bridge_client()
    return client.call("live_exec", {"code": code_snippet})
```

---

## 3. Blueprint: Session-to-Arrangement Sequencer (`live_stamp_session_to_arrangement`)

```python
def live_stamp_session_to_arrangement(track_index: int, slot_index: int, start_bar: int):
    """Duplicates a Session clip into the linear Arrangement timeline at start_bar."""
    beat_start = (start_bar - 1) * 4.0
    client = get_socket_bridge_client()
    return client.call("live_clip_duplicate_to_arrangement", {
        "clip_ref": f"live_set/tracks/{track_index}/clip_slots/{slot_index}/clip",
        "time": float(beat_start)
    })
```
