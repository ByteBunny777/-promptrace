"""Core logging API: LLMLogger writes JSONL records of LLM calls."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from .models import LogEntry
from .pricing import estimate_cost


class _CallHandle:
    """Handle returned inside a `with logger.track(...)` block.

    Lets the caller attach the response and token counts once they
    know them, without having to pass everything up front.
    """

    def __init__(self, entry: LogEntry, start_time: float, keep_text: bool = True):
        self._entry = entry
        self._start_time = start_time
        self._keep_text = keep_text

    def set_response(
        self,
        response_text: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        store_text: Optional[bool] = None,
    ) -> None:
        self._entry.prompt_tokens = prompt_tokens
        self._entry.completion_tokens = completion_tokens
        if response_text is not None:
            keep = self._keep_text if store_text is None else store_text
            if keep:
                self._entry.response_text = response_text
            h, ln = LogEntry.redact(response_text)
            self._entry.response_hash, self._entry.response_len = h, ln


class LLMLogger:
    """Append-only JSONL logger for LLM calls.

    Example
    -------
    >>> logger = LLMLogger("logs/session.jsonl")
    >>> with logger.track(model="claude-sonnet-5", prompt="Hello") as call:
    ...     reply = "Hi there!"
    ...     call.set_response(reply, prompt_tokens=5, completion_tokens=3)
    """

    def __init__(
        self,
        path: str | Path,
        pricing: Optional[dict[str, tuple[float, float]]] = None,
        store_text: bool = True,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.pricing = pricing
        self.store_text = store_text

    def log(
        self,
        model: str,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: Optional[float] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        store_text: Optional[bool] = None,
    ) -> LogEntry:
        """Log one completed call directly."""
        keep_text = self.store_text if store_text is None else store_text
        p_hash, p_len = LogEntry.redact(prompt)
        r_hash, r_len = LogEntry.redact(response)

        entry = LogEntry(
            id=LogEntry.new_id(),
            timestamp=LogEntry.now(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=estimate_cost(model, prompt_tokens, completion_tokens, self.pricing),
            tags=tags or [],
            metadata=metadata or {},
            prompt_text=prompt if keep_text else None,
            response_text=response if keep_text else None,
            prompt_hash=p_hash,
            response_hash=r_hash,
            prompt_len=p_len,
            response_len=r_len,
        )
        self._append(entry)
        return entry

    @contextmanager
    def track(
        self,
        model: str,
        prompt: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        store_text: Optional[bool] = None,
    ) -> Iterator[_CallHandle]:
        """Context manager that measures latency automatically.

        Yields a handle; call `handle.set_response(...)` inside the
        block once the response is available.
        """
        keep_text = self.store_text if store_text is None else store_text
        p_hash, p_len = LogEntry.redact(prompt)
        entry = LogEntry(
            id=LogEntry.new_id(),
            timestamp=LogEntry.now(),
            model=model,
            tags=tags or [],
            metadata=metadata or {},
            prompt_text=prompt if keep_text else None,
            prompt_hash=p_hash,
            prompt_len=p_len,
        )
        handle = _CallHandle(entry, time.perf_counter(), keep_text=keep_text)
        try:
            yield handle
        finally:
            entry.latency_ms = (time.perf_counter() - handle._start_time) * 1000.0
            entry.cost_usd = estimate_cost(
                model, entry.prompt_tokens, entry.completion_tokens, self.pricing
            )
            self._append(entry)

    def _append(self, entry: LogEntry) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
