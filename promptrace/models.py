"""Data model for a single logged LLM call."""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class LogEntry:
    """A single record of one LLM call."""

    id: str
    timestamp: float
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Prompt/response text is optional and can be stored either in full
    # or redacted (only length + sha256 hash), so sensitive data never
    # has to touch disk if the caller doesn't want it to.
    prompt_text: Optional[str] = None
    response_text: Optional[str] = None
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None
    prompt_len: Optional[int] = None
    response_len: Optional[int] = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def now() -> float:
        return time.time()

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def redact(cls, text: Optional[str]) -> tuple[Optional[str], Optional[int]]:
        """Return (hash, length) for a piece of text, or (None, None)."""
        if text is None:
            return None, None
        return cls._hash(text), len(text)
