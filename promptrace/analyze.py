"""Functions for loading and summarizing logged LLM calls."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .models import LogEntry


def load_entries(path: str | Path) -> list[LogEntry]:
    """Load all entries from a JSONL log file. Skips malformed lines."""
    path = Path(path)
    if not path.exists():
        return []
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(LogEntry.from_dict(json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
    return entries


def summarize(entries: list[LogEntry]) -> dict[str, Any]:
    """Overall stats across all entries."""
    if not entries:
        return {
            "calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "avg_latency_ms": None,
        }
    known_costs = [e.cost_usd for e in entries if e.cost_usd is not None]
    known_latencies = [e.latency_ms for e in entries if e.latency_ms is not None]
    return {
        "calls": len(entries),
        "prompt_tokens": sum(e.prompt_tokens for e in entries),
        "completion_tokens": sum(e.completion_tokens for e in entries),
        "total_tokens": sum(e.total_tokens for e in entries),
        "cost_usd": round(sum(known_costs), 6) if known_costs else 0.0,
        "avg_latency_ms": round(sum(known_latencies) / len(known_latencies), 1)
        if known_latencies
        else None,
    }


def group_by_model(entries: list[LogEntry]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[LogEntry]] = defaultdict(list)
    for e in entries:
        buckets[e.model].append(e)
    return {model: summarize(items) for model, items in buckets.items()}


def group_by_tag(entries: list[LogEntry]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[LogEntry]] = defaultdict(list)
    for e in entries:
        if not e.tags:
            buckets["(untagged)"].append(e)
        for tag in e.tags:
            buckets[tag].append(e)
    return {tag: summarize(items) for tag, items in buckets.items()}


def to_csv(entries: list[LogEntry], path: str | Path) -> None:
    """Export entries to a flat CSV (text fields included if present)."""
    fieldnames = [
        "id", "timestamp", "model", "prompt_tokens", "completion_tokens",
        "total_tokens", "latency_ms", "cost_usd", "tags",
        "prompt_len", "response_len", "prompt_hash", "response_hash",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in entries:
            row = e.to_dict()
            row["total_tokens"] = e.total_tokens
            row["tags"] = ";".join(e.tags)
            writer.writerow({k: row.get(k, "") for k in fieldnames})
