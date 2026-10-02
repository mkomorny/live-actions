---
id: 03_wavetable_synthesis_and_extraction_doc_007_vitaltable_format_and_conversion
title: Vitaltable Architecture & 2048-Sample Multi-Cycle WAV Conversion
category: 03_wavetable_synthesis_and_extraction
pages: 1
words: 369
source: 03_wavetable_synthesis_and_extraction/doc_007_vitaltable_format_and_conversion.md
---
# Vitaltable Architecture & 2048-Sample Multi-Cycle WAV Conversion

## The `.vitaltable` File Format

Vital stores custom wavetable definitions in `.vitaltable` files. Like `.vital` presets, `.vitaltable` files are JSON documents containing algorithmic component recipes or discrete Fourier coefficients:

```json
{
  "author": "Matt Tytel",
  "name": "Harmonic Series",
  "full_normalize": true,
  "remove_all_dc": true,
  "components": [
    {
      "type": "Wave Source",
      "keyframes": [
        {
          "position": 0,
          "wave_data": [0.0, 0.05, 0.1, "..."]
        }
      ]
    },
    {
      "type": "Frequency Filter",
      "cutoff": 64.0
    }
  ]
}
```

---

## The Industry Standard 2048-Sample Wavetable Standard

Professional software synthesizers (Ableton Live Wavetable, Vital, Serum, Pigments, Surge XT) all adhere to the **2048-Sample Multi-Cycle Standard**:
* **Single Frame Length**: Exactly 2,048 audio samples per waveform cycle.
* **Table Length**: Typically 64, 128, or 256 consecutive frames. A 256-frame table contains $256 \times 2,048 = 524,288$ samples (approx. 11.88 seconds of audio at 44.1 kHz).
* **Format**: 32-bit floating point or 24-bit PCM mono WAV file.
* **Header Clue**: Often includes a `clm ` or `uhsh` chunk or standard subchunk markers indicating loop markers.

---

## Procedural 2048-Sample Wavetable Generation in Python

You can generate custom multi-cycle wavetables mathematically using NumPy and export them directly to disk without requiring Vital:

```python
import numpy as np
import scipy.io.wavfile as wavfile
from pathlib import Path

def generate_harmonic_morph_table(output_path: Path, num_frames: int = 64, frame_size: int = 2048):
    """
    Generate a 2048-sample multi-cycle wavetable morphing from pure Sine
    to rich Sawtooth across 64 frames.
    """
    table_data = np.zeros(num_frames * frame_size, dtype=np.float32)
    t = np.linspace(0.0, 2.0 * np.pi, frame_size, endpoint=False)
    
    for frame_idx in range(num_frames):
        alpha = frame_idx / float(num_frames - 1)  # 0.0 (Sine) to 1.0 (Saw)
        
        # Additive harmonic synthesis: sum of (1/k) * sin(k*t)
        max_harmonics = int(1 + alpha * 31)  # Up to 32 harmonics
        frame_wave = np.zeros(frame_size, dtype=np.float32)
        
        for k in range(1, max_harmonics + 1):
            amplitude = (1.0 / k) ** (1.0 - alpha * 0.5)
            frame_wave += amplitude * np.sin(k * t)
            
        # Normalize frame
        peak = np.max(np.abs(frame_wave))
        if peak > 0:
            frame_wave = frame_wave / peak * 0.95
            
        # Store in master table buffer
        start = frame_idx * frame_size
        table_data[start:start + frame_size] = frame_wave
        
    # Write 32-bit float WAV
    wavfile.write(str(output_path), 44100, table_data)
    print(f"Generated wavetable: {output_path} ({num_frames} frames, {len(table_data)} samples)")
```
