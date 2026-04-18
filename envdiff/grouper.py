"""Group keys by prefix (e.g. DB_, AWS_) for structured comparison reports."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class KeyGroup:
    prefix: str
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.diffs)

    def __len__(self) -> int:
        return len(self.diffs)


@dataclass
class GroupedResult:
    groups: Dict[str, KeyGroup]
    ungrouped: KeyGroup

    def all_groups(self) -> List[KeyGroup]:
        return list(self.groups.values()) + ([self.ungrouped] if self.ungrouped.diffs else [])


def _extract_prefix(key: str, separator: str = "_") -> str | None:
    """Return the first segment before separator, or None if no separator."""
    if separator in key:
        return key.split(separator, 1)[0].upper()
    return None


def group_by_prefix(
    result: CompareResult,
    separator: str = "_",
    min_group_size: int = 1,
) -> GroupedResult:
    """Group KeyDiffs in a CompareResult by key prefix.

    Args:
        result: The comparison result to group.
        separator: Character used to split key prefixes.
        min_group_size: Minimum number of keys for a prefix to form its own group.
    """
    raw: Dict[str, List[KeyDiff]] = {}
    ungrouped_diffs: List[KeyDiff] = []

    for diff in result.all_diffs():
        prefix = _extract_prefix(diff.key, separator)
        if prefix:
            raw.setdefault(prefix, []).append(diff)
        else:
            ungrouped_diffs.append(diff)

    groups: Dict[str, KeyGroup] = {}
    for prefix, diffs in raw.items():
        if len(diffs) >= min_group_size:
            groups[prefix] = KeyGroup(prefix=prefix, diffs=diffs)
        else:
            ungrouped_diffs.extend(diffs)

    return GroupedResult(
        groups=groups,
        ungrouped=KeyGroup(prefix="(ungrouped)", diffs=ungrouped_diffs),
    )
