---
title: Helper Bot Guardrails & Verification Protocol
category: foundations_and_guardrails
subcategory: guardrails
id: doc_002_helper_bot_guardrails_and_integration_rules
words: 222
source: HELPER_BOT_NOTES.md
---
# Helper Bot Guardrails & Verification Protocol

Mandatory rules for Live Actions, AI Skills, and LLM assistants when utilizing this dataset.

## The 9 Mandatory Ingestion Rules

1. **Inspiration, Not Dogma**: Treat this corpus as retrieval fuel and structured prompt templates—never as infallible truth about Ableton Live or mixing acoustics.
2. **Prioritize Real Live Context**: When the user's actual session state, Live version, or installed plugin inventory conflicts with a dataset example, always adhere to the live project state.
3. **Recognize Templated Archetypes**: Thousands of examples share identical drum grid formulas and synth envelopes with genre labels swapped. Do not assume advice is bespoke unless mathematically verified.
4. **Not Native Live Sets**: This dataset contains zero `.als`, `.adg`, or audio sample files. It is pure instruction text.
5. **Pair with Concrete XML Racks**: When building physical racks, combine this dataset with labeled Ableton XML presets (`sixf0ur-ableton-racks-labeled`).
6. **Verify Parameter Plausibility**: LUFS targets (-8 LUFS vs -14 LUFS streaming standards), filter cutoffs, and compressor ratios must be sanity-checked against standard production practices.
7. **Tool-Calling Translation**: Translate training targets into actual Live Actions OSC tool calls (`live_create_device`, `live_update_device`, `live_write_notes`).
8. **Field Filtering**: Leverage metadata fields (`category`, `style`, `tags`) for surgical semantic retrieval.
9. **Safe Retrieval Pattern**: Retrieve relevant recipes -> Adapt to the user's Live 12 environment -> Disclose any assumptions.
