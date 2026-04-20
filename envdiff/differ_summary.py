"""Summarise differences between multiple env file pairs at a high level."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class EnvPairSummary:
    """High-level summary for a single pair of compared env files."""

    env_a: str
    env_b: str
    total_keys: int
    missing_count: int
    mismatch_count: int

    @property
    def match_count(self) -> int:
        return self.total_keys - self.missing_count - self.mismatch_count

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.env_a} vs {self.env_b}: "
            f"{self.total_keys} keys, "
            f"{self.missing_count} missing, "
            f"{self.mismatch_count} mismatched, "
            f"{self.match_count} matching"
        )


@dataclass
class MultiSummary:
    """Aggregated summary across several env comparisons."""

    pairs: List[EnvPairSummary] = field(default_factory=list)

    @property
    def total_pairs(self) -> int:
        return len(self.pairs)

    @property
    def any_differences(self) -> bool:
        return any(p.missing_count > 0 or p.mismatch_count > 0 for p in self.pairs)

    def worst_pair(self) -> EnvPairSummary | None:
        if not self.pairs:
            return None
        return max(self.pairs, key=lambda p: p.missing_count + p.mismatch_count)


def summarise_pair(result: CompareResult) -> EnvPairSummary:
    """Build an EnvPairSummary from a CompareResult."""
    all_keys: set[str] = set()
    for diff in result.diffs:
        all_keys.add(diff.key)
    # Add keys that matched (present in both envs with same value)
    # CompareResult stores only differing keys; we need env data to get full count.
    # Use the union of keys from both env dicts if available, else fall back to diffs.
    env_names = result.env_names
    missing = sum(1 for d in result.diffs if d.missing_in is not None)
    mismatch = sum(1 for d in result.diffs if d.missing_in is None)
    total = len(all_keys)
    return EnvPairSummary(
        env_a=env_names[0] if env_names else "env_a",
        env_b=env_names[1] if len(env_names) > 1 else "env_b",
        total_keys=total,
        missing_count=missing,
        mismatch_count=mismatch,
    )


def summarise_many(results: List[CompareResult]) -> MultiSummary:
    """Build a MultiSummary from a list of CompareResults."""
    return MultiSummary(pairs=[summarise_pair(r) for r in results])
