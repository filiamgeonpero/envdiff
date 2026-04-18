"""Sort and rank env keys by various criteria."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class SortOptions:
    by: str = "key"  # "key" | "env" | "diff_type"
    reverse: bool = False


@dataclass
class SortedResult:
    envs: List[str]
    diffs: List[KeyDiff]

    def keys(self) -> List[str]:
        return [d.key for d in self.diffs]


def _diff_type_rank(diff: KeyDiff) -> int:
    if diff.is_missing:
        return 0
    return 1


def sort_result(result: CompareResult, options: SortOptions | None = None) -> SortedResult:
    """Return a SortedResult with diffs ordered by the given options."""
    if options is None:
        options = SortOptions()

    diffs = list(result.all_diffs())

    if options.by == "key":
        diffs.sort(key=lambda d: d.key, reverse=options.reverse)
    elif options.by == "env":
        diffs.sort(key=lambda d: (d.env or "", d.key), reverse=options.reverse)
    elif options.by == "diff_type":
        diffs.sort(key=lambda d: (_diff_type_rank(d), d.key), reverse=options.reverse)
    else:
        raise ValueError(f"Unknown sort key: {options.by!r}")

    return SortedResult(envs=list(result.envs), diffs=diffs)
