"""promptrace: lightweight, dependency-free logging & analytics for LLM calls."""
from .analyze import group_by_model, group_by_tag, load_entries, summarize, to_csv
from .logger import LLMLogger
from .models import LogEntry
from .pricing import DEFAULT_PRICING, estimate_cost, load_pricing_file

__version__ = "0.1.0"

__all__ = [
    "LLMLogger",
    "LogEntry",
    "load_entries",
    "summarize",
    "group_by_model",
    "group_by_tag",
    "to_csv",
    "estimate_cost",
    "load_pricing_file",
    "DEFAULT_PRICING",
]
