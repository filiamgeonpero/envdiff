"""Promote keys from one environment to another, tracking what changed."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PromoteChange:
    key: str
    source_value: str
    target_value: Optional[str]  # None means key was absent in target

    def __str__(self) -> str:
        if self.target_value is None:
            return f"{self.key}: (missing) -> {self.source_value!r}"
        return f"{self.key}: {self.target_value!r} -> {self.source_value!r}"


@dataclass
class PromoteResult:
    source_name: str
    target_name: str
    promoted: Dict[str, str] = field(default_factory=dict)
    changes: List[PromoteChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def summary(self) -> str:
        lines = [
            f"Promote {self.source_name} -> {self.target_name}",
            f"  promoted : {len(self.changes)}",
            f"  skipped  : {len(self.skipped)}",
        ]
        return "\n".join(lines)


def promote_env(
    source: Dict[str, str],
    target: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
    source_name: str = "source",
    target_name: str = "target",
) -> PromoteResult:
    """Copy keys from *source* into *target*.

    Args:
        source: The authoritative environment to promote from.
        target: The destination environment dict (not mutated).
        keys: Explicit list of keys to promote; defaults to all source keys.
        overwrite: When False, skip keys that already exist in target.
        source_name: Label for the source environment.
        target_name: Label for the target environment.

    Returns:
        A :class:`PromoteResult` with the merged env and a change log.
    """
    result = PromoteResult(
        source_name=source_name,
        target_name=target_name,
        promoted=dict(target),
    )

    candidates = keys if keys is not None else list(source.keys())

    for key in candidates:
        if key not in source:
            result.skipped.append(key)
            continue
        if not overwrite and key in target:
            result.skipped.append(key)
            continue
        old_value = target.get(key)
        result.changes.append(
            PromoteChange(key=key, source_value=source[key], target_value=old_value)
        )
        result.promoted[key] = source[key]

    return result
