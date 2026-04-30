"""Flatten nested key structures by expanding delimiter-separated keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenOptions:
    delimiter: str = "__"
    prefix_filter: Optional[str] = None
    lowercase_keys: bool = False


@dataclass
class FlattenEntry:
    original_key: str
    flat_key: str
    value: str
    depth: int

    def __str__(self) -> str:
        return f"{self.flat_key}={self.value}  (was: {self.original_key})"


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def flat_env(self) -> Dict[str, str]:
        return {e.flat_key: e.value for e in self.entries}

    @property
    def has_changes(self) -> bool:
        return any(e.original_key != e.flat_key for e in self.entries)

    def summary(self) -> str:
        changed = sum(1 for e in self.entries if e.original_key != e.flat_key)
        return (
            f"{len(self.entries)} keys processed, "
            f"{changed} renamed, "
            f"{len(self.skipped)} skipped"
        )


def flatten_env(
    env: Dict[str, str],
    options: Optional[FlattenOptions] = None,
) -> FlattenResult:
    """Flatten delimiter-separated keys into dot-notation style flat keys."""
    if options is None:
        options = FlattenOptions()

    result = FlattenResult()
    delim = options.delimiter

    for key, value in env.items():
        if options.prefix_filter and not key.startswith(options.prefix_filter):
            result.skipped.append(key)
            continue

        parts = key.split(delim)
        flat_key = ".".join(p for p in parts if p)

        if options.lowercase_keys:
            flat_key = flat_key.lower()

        depth = len(parts) - 1
        result.entries.append(
            FlattenEntry(
                original_key=key,
                flat_key=flat_key,
                value=value,
                depth=depth,
            )
        )

    return result
