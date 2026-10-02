"""Best-effort $/1M-token pricing for known chat models, shown as a subtle tag next to
each model in the key/model picker (components.js's modelSelect, prefs.js's modelOptions).

None of the four provider APIs this app talks to (xAI, OpenAI, Gemini, Anthropic -- see
PROVIDER_DEFAULTS in ai_providers.py) return pricing from their /models endpoint, so there
is no live source to pull a price from at "Detect provider" time. This table is a
hand-maintained seed of well-known model families, matched by substring against the model
id (longest substring wins). A model that matches nothing -- a brand-new release, a
preview/custom id, a self-hosted model -- simply gets no price tag rather than a guessed
one: a wrong price is worse than no price.

Update this table by hand when a provider changes pricing or ships a family you use.
Prices are USD per 1,000,000 tokens, as (input, output).
"""

from __future__ import annotations

# provider -> [(substring, input_per_million, output_per_million), ...]
_PRICING: dict[str, list[tuple[str, float, float]]] = {
    "gemini": [
        ("gemini-2.5-flash-lite", 0.10, 0.40),
        ("gemini-2.5-flash", 0.30, 2.50),
        ("gemini-2.5-pro", 1.25, 10.00),
        ("gemini-2.0-flash-lite", 0.075, 0.30),
        ("gemini-2.0-flash", 0.10, 0.40),
        ("gemini-1.5-flash", 0.075, 0.30),
        ("gemini-1.5-pro", 1.25, 5.00),
    ],
    "openai": [
        ("gpt-4o-mini", 0.15, 0.60),
        ("gpt-4o", 2.50, 10.00),
        ("gpt-4.1-nano", 0.10, 0.40),
        ("gpt-4.1-mini", 0.40, 1.60),
        ("gpt-4.1", 2.00, 8.00),
        ("o4-mini", 1.10, 4.40),
        ("o3-mini", 1.10, 4.40),
        ("o3", 2.00, 8.00),
    ],
    "anthropic": [
        ("claude-3-5-haiku", 0.80, 4.00),
        ("claude-3-haiku", 0.25, 1.25),
        ("claude-opus", 15.00, 75.00),
        ("claude-3-5-sonnet", 3.00, 15.00),
        ("claude-3-7-sonnet", 3.00, 15.00),
        ("claude-sonnet", 3.00, 15.00),
    ],
    "xai": [
        ("grok-3-mini", 0.30, 0.50),
        ("grok-3", 3.00, 15.00),
        ("grok-4", 3.00, 15.00),
        ("grok-2", 2.00, 10.00),
    ],
}


def price_for(provider: str, model: str) -> tuple[float, float] | None:
    """USD per 1M tokens as (input, output) for a known model, or None if unrecognized."""
    rows = _PRICING.get((provider or "").strip().lower())
    if not rows or not model:
        return None
    m = model.strip().lower()
    best: tuple[float, float] | None = None
    best_len = -1
    for substr, p_in, p_out in rows:
        if substr in m and len(substr) > best_len:
            best, best_len = (p_in, p_out), len(substr)
    return best


def pricing_for_models(provider: str, models: list[str]) -> dict[str, list[float]]:
    """{model: [input, output]} for every model in `models` that has a known price."""
    out: dict[str, list[float]] = {}
    for m in models:
        p = price_for(provider, m)
        if p is not None:
            out[m] = [p[0], p[1]]
    return out
