"""Filtering utilities for envdiff comparison results."""
from dataclasses import dataclass, field
from typing import List, Optional, Set
from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class FilterOptions:
    include_keys: Optional[Set[str]] = None  # if set, only these keys
    exclude_keys: Set[str] = field(default_factory=set)
    only_missing: bool = False
    only_mismatched: bool = False


def filter_result(result: CompareResult, opts: FilterOptions) -> CompareResult:
    """Return a new CompareResult with diffs filtered by opts."""
    filtered: List[KeyDiff] = []

    for diff in result.diffs:
        key = diff.key

        if opts.include_keys is not None and key not in opts.include_keys:
            continue
        if key in opts.exclude_keys:
            continue
        if opts.only_missing and diff.values is not None:
            continue
        if opts.only_mismatched and diff.values is None:
            continue

        filtered.append(diff)

    return CompareResult(env_names=result.env_names, diffs=filtered)
