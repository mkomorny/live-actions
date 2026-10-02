---
id: 02_sound_similarity_engine_doc_004_neural_audio_feature_decoding_and_cosine_search
title: Neural Audio Feature Decoding & Fast Cosine Similarity Search
category: 02_sound_similarity_engine
pages: 1
words: 840
source: 02_sound_similarity_engine/doc_004_neural_audio_feature_decoding_and_cosine_search.md
---
# Neural Audio Feature Decoding & Fast Cosine Similarity Search

## 1. Feature Vector Binary Packing Protocol

In `similar_sounds.py`, the binary feature BLOB stored by Ableton Live is decoded using standard Python `struct`:

```python
import struct
import math

def decode_feature(blob: bytes) -> list[float]:
    # Ableton stores a 12-byte header followed by 32-bit little-endian IEEE floating-point numbers
    header_size = 12
    float_bytes = blob[header_size:]
    num_floats = len(float_bytes) // 4
    return list(struct.unpack(f"<{num_floats}f", float_bytes))
```

---

## 2. Cosine Similarity & Distance Computation

To find sounds that match a target reference sample, the vector cosine similarity is evaluated:

$$	ext{Cosine Similarity}(A, B) = rac{A \cdot B}{\|A\| \|B\|} = rac{\sum_{i=1}^n A_i B_i}{\sqrt{\sum_{i=1}^n A_i^2} \sqrt{\sum_{i=1}^n B_i^2}}$$

```python
def cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    sim = dot / (norm_a * norm_b)
    return 1.0 - max(-1.0, min(1.0, sim))
```

---

## 3. Executing Similar Sound Queries in Python

The tool `find_similar_sounds` accepts either:
1. `base`: Path or filename of a reference sample in the user library.
2. `query`: Plain text search filter (e.g. `"snare"`, `"acoustic kick"`).
3. `limit`: Number of similar candidates to return (default 5).

```python
# Live Actions Genius implementation
def find_similar_samples(reference_sample_path: str, limit: int = 5):
    from src.similar_sounds import find_similar
    matches = find_similar(base_file=reference_sample_path, limit=limit)
    return [
        {"path": m.path, "name": m.name, "distance": round(m.distance, 4)}
        for m in matches
    ]
```

This delivers instant AI sound replacement directly from chat: *"Replace the active snare sample with the closest acoustic equivalent in my library."*
