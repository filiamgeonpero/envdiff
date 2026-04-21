"""Trim unused keys from a .env file given a set of known/required keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TrimOptions:
    keep_keys: Set[str] = field(default_factory=set)
    dry_run: bool = False


@dataclass
class TrimResult:
    original: Dict[str, str]
    trimmed: Dict[str, str]
    removed: List[str]
    dry_run: bool = False

    @property
    def has_changes(self) -> bool:
        return len(self.removed) > 0

    def summary(self) -> str:
        if not self.has_changes:
            return "No unused keys found."
        prefix = "[dry-run] " if self.dry_run else ""
        keys = ", ".join(sorted(self.removed))
        return f"{prefix}Removed {len(self.removed)} unused key(s): {keys}"


def trim_env(
    env: Dict[str, str],
    options: Optional[TrimOptions] = None,
) -> TrimResult:
    """Return a TrimResult removing keys not in *keep_keys*.

    If *keep_keys* is empty every key is retained (no-op).
    """
    if options is None:
        options = TrimOptions()

    if not options.keep_keys:
        return TrimResult(
            original=dict(env),
            trimmed=dict(env),
            removed=[],
            dry_run=options.dry_run,
        )

    removed: List[str] = [
        k for k in env if k not in options.keep_keys
    ]

    if options.dry_run:
        trimmed = dict(env)
    else:
        trimmed = {k: v for k, v in env.items() if k in options.keep_keys}

    return TrimResult(
        original=dict(env),
        trimmed=trimmed,
        removed=removed,
        dry_run=options.dry_run,
    )
