"""Deduplicator: merge duplicate keys within a single env dict, applying a
configurable resolution strategy (first, last, or error)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Strategy(str, Enum):
    FIRST = "first"   # keep the first occurrence
    LAST = "last"     # keep the last occurrence
    ERROR = "error"   # raise if any duplicate is found


class DeduplicateError(Exception):
    """Raised when strategy=ERROR and duplicates are detected."""


@dataclass
class DuplicateKey:
    key: str
    values: List[str]          # all values seen, in order
    kept: str                  # value that was kept

    def __str__(self) -> str:
        vals = ", ".join(repr(v) for v in self.values)
        return f"{self.key}: [{vals}] -> kept {self.kept!r}"


@dataclass
class DeduplicateResult:
    env: Dict[str, str]
    duplicates: List[DuplicateKey] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    def summary(self) -> str:
        if not self.has_duplicates:
            return "No duplicate keys found."
        lines = [f"{len(self.duplicates)} duplicate key(s) resolved:"]
        for d in self.duplicates:
            lines.append(f"  {d}")
        return "\n".join(lines)


def deduplicate_env(
    raw_pairs: List[tuple[str, str]],
    strategy: Strategy = Strategy.LAST,
) -> DeduplicateResult:
    """Resolve duplicate keys in *raw_pairs* (key, value) using *strategy*.

    Parameters
    ----------
    raw_pairs:
        Ordered list of (key, value) tuples as produced by a line-by-line
        parser that does NOT collapse duplicates.
    strategy:
        How to handle duplicates.  Defaults to LAST (mirrors shell behaviour).
    """
    seen: Dict[str, List[str]] = {}
    for key, value in raw_pairs:
        seen.setdefault(key, []).append(value)

    dup_keys = [k for k, vals in seen.items() if len(vals) > 1]

    if strategy is Strategy.ERROR and dup_keys:
        raise DeduplicateError(
            f"Duplicate keys found: {', '.join(dup_keys)}"
        )

    resolved: Dict[str, str] = {}
    duplicates: List[DuplicateKey] = []

    for key, values in seen.items():
        if len(values) == 1:
            resolved[key] = values[0]
        else:
            kept = values[0] if strategy is Strategy.FIRST else values[-1]
            resolved[key] = kept
            duplicates.append(DuplicateKey(key=key, values=values, kept=kept))

    return DeduplicateResult(env=resolved, duplicates=duplicates)
