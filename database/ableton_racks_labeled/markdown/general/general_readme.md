---
id: general_readme
title: Readme
category: general
pages: 1
words: 263
source: README.md
---
# Readme

---
license: mit
language:
- en
tags:
- xml
- labeled
- presets
- music
- audio
- sound
- ableton_11
size_categories:
- n<1K
---

# Dataset Card for Ableton Live XML Presets

## Dataset Summary

This dataset consists of **Ableton Live XML presets** paired with synthetic, multi-perspective natural language descriptions and Chain-of-Thought (CoT) reasoning. It is designed for fine-tuning Large Language Models (LLMs) to perform **text-to-preset generation**, **sound design analysis**, and **audio parameter reasoning**.

Each entry provides three distinct prompt styles (layman, technical, and emotional) alongside a detailed step-by-step technical breakdown (`chain_of_thought`) of the Ableton preset device chain.

## Dataset Structure

### File Format
* **Format:** JSON Lines (`.jsonl`)
* **File Name:** `ableton_dataset.jsonl`

### Data Fields

* `layman_prompt` (`string`): A simple, non-technical, everyday language description of the sound.
* `technical_prompt` (`string`): A precise production-oriented description using professional audio engineering and sound design terms.
* `emotional_prompt` (`string`): A vibe-driven, moody prompt focused on atmosphere, aesthetic, or feeling.
* `chain_of_thought` (`string`): Detailed reasoning process explaining the selection and settings of specific Ableton devices, effects, and parameter values.
* `xml_preset` (`string`): The full raw XML source code of the corresponding Ableton Live preset.

### Data Example

```json
{
  "layman_prompt": "A warm, crunchy bass sound that feels heavy and cozy.",
  "technical_prompt": "Saturated sub-bass with drive, low-pass filtered around 250 Hz and slight dynamic compression.",
  "emotional_prompt": "Dark, moody, and grounded in a retro, lo-fi aesthetic.",
  "chain_of_thought": "The preset utilizes a Saturator device with 6dB drive for harmonic warmth, followed by an Auto Filter cutting high frequencies above 250Hz...",
  "xml_preset": "<Ableton ... MajorVersion="\"11\"" MinorVersion="\"0\"" SchemaChangeCount="\"3\""> ... </Ableton>"
}```
