---
title: God-Level Producer Dataset Overview & Manifesto
category: foundations_and_guardrails
subcategory: overview
id: doc_001_god_producer_overview_and_manifesto
words: 156
source: README.md
---
# Ableton Live God-Level Beat Producer Dataset: Overview & Manifesto

Source: HuggingFace (11-47/ableton_god_producer_dataset)
License: Apache 2.0
Corpus: 9,956 instruction/reasoning turns covering drum programming, bass design, and mixing/mastering in Ableton Live 12.

## Key Features
- **Fact-Based Ableton Live 12 Workflows**: Real device chains, specific parameter values, and rack routings.
- **God-Level Chain-of-Thought Reasoning**: Every example features an extensive `<think>` phase articulating the psychoacoustic and musical rationale behind each decision.
- **Precision Tool Calling**: Exact instructions designed for automated DAW tool calling (e.g. `live_create_device`, `live_write_notes`).
- **Production Styles**: Trap, Drill, Lo-Fi Hip Hop, Future Bass, Techno, UK Garage, Phonk, Jungle, Drum & Bass, Ambient Electronic, IDM, House, and Hyperpop.

## Fine-Tuning & Model Architecture Recommendations
- **Recommended Base Models**: Qwen2.5-72B, Llama-3.3-70B, Claude-3.5-Sonnet, DeepSeek-V3.
- **Training Methodology**: ORPO (Odds Ratio Preference Optimization) + Direct Tool-Calling Fine-Tuning.
- **Minimum Context Window**: 8,192 tokens.
- **Goal**: Producing models that act directly upon the DAW rather than providing generic conversational descriptions.
