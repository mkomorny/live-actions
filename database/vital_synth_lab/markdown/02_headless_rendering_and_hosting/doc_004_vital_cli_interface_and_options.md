---
id: 02_headless_rendering_and_hosting_doc_004_vital_cli_interface_and_options
title: Vital Command Line Interface (CLI) & Headless Rendering
category: 02_headless_rendering_and_hosting
pages: 1
words: 363
source: 02_headless_rendering_and_hosting/doc_004_vital_cli_interface_and_options.md
---
# Vital Command Line Interface (CLI) & Headless Rendering

## CLI Overview & Syntax

The standalone executable of Vital includes built-in command-line arguments that permit headless operations, automated preset-to-audio bounces, wavetable extraction, and oscilloscope image rendering.

On Windows, the executable typically resides at:
`C:\Program Files\Vital\Vital.exe`

```text
Usage:
  Vital [OPTION...]

Application Options:
  -v, --version         Show version information and exit
  --headless            Run without graphical interface
  --tabletowav          Converts a .vitaltable to a .wav file
  --tableimages         Renders an image preview for a wavetable
  --render              Render to an audio file
  -m, --midi            Note to play (with --render, e.g. 48 for C3)
  -l, --length          Note length in seconds (with --render)
  -b, --bpm             BPM to play (with --render)
  --images              Render oscilloscope images (with --render)
```

---

## Direct CLI Command Examples

### 1. Rendering a Preset to Audio
To render a single note preview from a `.vital` preset:
```powershell
& "C:\Program Files\Vital\Vital.exe" --headless --render "C:\Presets\Lead.vital" -m 60 -l 2.5 -b 120
```
This triggers Vital's internal audio engine without initializing an OpenGL context, generating a high-quality `.wav` file alongside the preset.

### 2. Batch Converting `.vitaltable` to `.wav`
```powershell
& "C:\Program Files\Vital\Vital.exe" --headless --tabletowav "C:\Presets\CustomTable.vitaltable"
```
This unpacks the wavetable frames into a 2048-sample multi-cycle `.wav` file ready for Ableton Wavetable or Simpler.

---

## Known Segfault Issue (Bug Analysis & Root Cause)

As documented in research by 0xdevalias and tracked in [Vital Issue #45](https://github.com/mtytel/vital/issues/45):
* In certain versions (notably 1.5.5 on macOS and specific Windows builds), running `--render` can trigger a segmentation fault (`SIGSEGV` / `0xC0000005` Access Violation):
  ```text
  Thread 0 Crashed: JUCE Message Thread
  juce::AudioFormatWriter::writeFromFloatArrays(float const* const*, int, int)
  SynthBase::renderAudioToFile(juce::File const&, float, float, std::vector<int>, bool)
  processCommandLine(juce::String const&)
  ```
* **Root Cause**: The standalone app initializes the JUCE audio format writer before the audio buffer pointers in `SynthBase` have completed their allocation cycle when running in strictly unattached headless mode.

### Production Solution: Headless Python Wrappers
Because the direct CLI `--render` flag can be unstable depending on the installed binary build, production tools in `Live Actions Helper` bypass `Vital.exe --render` by using:
1. **`Vita`** (`github.com/DBraun/Vita`): Direct C++ bindings without JUCE CLI argument parsing.
2. **`DawDreamer`** or **`Spotify Pedalboard`**: Loading the stable `Vital.vst3` plugin dynamically inside an isolated Python process.
