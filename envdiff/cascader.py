"""Cascade multiple .env files in priority order.

Later files override earlier ones; the result is a merged dict with
provenance tracking so callers know which file supplied each value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class CascadeEntry:
    """A single key resolved after cascading."""

    key: str
    value: str
    source: str  # filename that provided the winning value
    overridden_by: List[str] = field(default_factory=list)  # files that were shadowed

    def __str__(self) -> str:
        if self.overridden_by:
            return f"{self.key}={self.value!r} (from {self.source}, shadowed {self.overridden_by})"
        return f"{self.key}={self.value!r} (from {self.source})"


@dataclass
class CascadeResult:
    """Outcome of cascading *env_files* together."""

    env_names: List[str]
    entries: Dict[str, CascadeEntry] = field(default_factory=dict)

    # keys that only appear in a subset of files
    exclusive: Dict[str, str] = field(default_factory=dict)  # key -> only source

    def resolved(self) -> Dict[str, str]:
        """Return the final key→value mapping."""
        return {k: e.value for k, e in self.entries.items()}

    def summary(self) -> str:
        total = len(self.entries)
        overridden = sum(1 for e in self.entries.values() if e.overridden_by)
        exclusive = len(self.exclusive)
        return (
            f"{total} keys resolved across {len(self.env_names)} file(s); "
            f"{overridden} overridden, {exclusive} exclusive"
        )


def cascade_envs(
    named_envs: List[Tuple[str, Dict[str, str]]],
) -> CascadeResult:
    """Cascade *named_envs* in order (last wins).

    Parameters
    ----------
    named_envs:
        Sequence of ``(name, env_dict)`` pairs ordered from lowest to
        highest priority.
    """
    env_names = [name for name, _ in named_envs]
    result = CascadeResult(env_names=env_names)

    # Track which files contain each key
    key_sources: Dict[str, List[str]] = {}
    for name, env in named_envs:
        for key in env:
            key_sources.setdefault(key, []).append(name)

    # Build entries — last file wins
    merged: Dict[str, Tuple[str, str]] = {}  # key -> (value, winning_source)
    for name, env in named_envs:
        for key, value in env.items():
            merged[key] = (value, name)

    for key, (value, winner) in merged.items():
        sources = key_sources[key]
        shadowed = [s for s in sources if s != winner]
        entry = CascadeEntry(key=key, value=value, source=winner, overridden_by=shadowed)
        result.entries[key] = entry
        if len(sources) == 1:
            result.exclusive[key] = winner

    return result
