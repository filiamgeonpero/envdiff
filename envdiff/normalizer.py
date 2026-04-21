"""Normalize .env values for consistent comparison (trim whitespace, unify booleans, etc.)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


@dataclass
class NormalizeOptions:
    strip_whitespace: bool = True
    unify_booleans: bool = True
    lowercase_keys: bool = False
    remove_empty: bool = False


@dataclass
class NormalizeResult:
    original: Dict[str, Optional[str]]
    normalized: Dict[str, Optional[str]]
    changes: Dict[str, tuple] = field(default_factory=dict)  # key -> (before, after)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def summary(self) -> str:
        if not self.has_changes:
            return "No normalization changes."
        lines = [f"Normalized {len(self.changes)} key(s):"]
        for key, (before, after) in self.changes.items():
            lines.append(f"  {key}: {before!r} -> {after!r}")
        return "\n".join(lines)


def _normalize_value(value: Optional[str], opts: NormalizeOptions) -> Optional[str]:
    if value is None:
        return None
    if opts.strip_whitespace:
        value = value.strip()
    if opts.unify_booleans and value.lower() in _BOOL_TRUE:
        value = "true"
    elif opts.unify_booleans and value.lower() in _BOOL_FALSE:
        value = "false"
    return value


def normalize_env(
    env: Dict[str, Optional[str]],
    opts: Optional[NormalizeOptions] = None,
) -> NormalizeResult:
    if opts is None:
        opts = NormalizeOptions()

    normalized: Dict[str, Optional[str]] = {}
    changes: Dict[str, tuple] = {}

    for raw_key, raw_value in env.items():
        key = raw_key.lower() if opts.lowercase_keys else raw_key
        new_value = _normalize_value(raw_value, opts)

        if opts.remove_empty and new_value == "":
            changes[key] = (raw_value, None)
            continue

        normalized[key] = new_value
        if key != raw_key or new_value != raw_value:
            changes[key] = (raw_value, new_value)

    return NormalizeResult(original=dict(env), normalized=normalized, changes=changes)
