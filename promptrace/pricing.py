"""Simple, editable pricing table for cost estimation.

Prices are USD per 1,000 tokens. This is intentionally simple and meant
to be edited/extended by the user -- pass a custom dict to override or
add models, or load one from a JSON file with `load_pricing_file`.

These numbers are illustrative starting points, not guaranteed to be
up to date. Always check your provider's current pricing page.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# (input_price_per_1k, output_price_per_1k)
DEFAULT_PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (0.015, 0.075),
    "claude-sonnet-5": (0.003, 0.015),
    "claude-haiku-4-5": (0.0008, 0.004),
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4.1": (0.002, 0.008),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
}


def load_pricing_file(path: str | Path) -> dict[str, tuple[float, float]]:
    """Load a JSON pricing file: {"model": [input_per_1k, output_per_1k], ...}"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: (float(v[0]), float(v[1])) for k, v in data.items()}


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: Optional[dict[str, tuple[float, float]]] = None,
) -> Optional[float]:
    """Return estimated USD cost, or None if the model isn't in the table."""
    table = pricing if pricing is not None else DEFAULT_PRICING
    rates = table.get(model)
    if rates is None:
        return None
    in_rate, out_rate = rates
    return (prompt_tokens / 1000.0) * in_rate + (completion_tokens / 1000.0) * out_rate
