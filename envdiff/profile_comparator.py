"""Compare two ProfileResult objects and highlight notable differences."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from envdiff.profiler import ProfileResult


@dataclass
class ProfileDiff:
    field: str
    left_value: object
    right_value: object

    def __str__(self) -> str:
        return f"{self.field}: {self.left_value!r} vs {self.right_value!r}"


@dataclass
class ProfileComparison:
    left: ProfileResult
    right: ProfileResult
    diffs: List[ProfileDiff]

    def has_differences(self) -> bool:
        return bool(self.diffs)

    def summary(self) -> str:
        if not self.diffs:
            return f"Profiles '{self.left.env_name}' and '{self.right.env_name}' are similar."
        lines = [f"Profile diff: {self.left.env_name} vs {self.right.env_name}"]
        for d in self.diffs:
            lines.append(f"  {d}")
        return "\n".join(lines)


_SCALAR_FIELDS: List[str] = [
    "total_keys",
    "uppercase_keys",
    "lowercase_keys",
]
_LIST_FIELDS: List[str] = [
    "empty_values",
    "sensitive_keys",
    "url_values",
    "numeric_values",
    "boolean_values",
]


def compare_profiles(left: ProfileResult, right: ProfileResult) -> ProfileComparison:
    diffs: List[ProfileDiff] = []
    for f in _SCALAR_FIELDS:
        lv, rv = getattr(left, f), getattr(right, f)
        if lv != rv:
            diffs.append(ProfileDiff(field=f, left_value=lv, right_value=rv))
    for f in _LIST_FIELDS:
        lv: int = len(getattr(left, f))
        rv: int = len(getattr(right, f))
        if lv != rv:
            diffs.append(ProfileDiff(field=f + "_count", left_value=lv, right_value=rv))
    return ProfileComparison(left=left, right=right, diffs=diffs)
