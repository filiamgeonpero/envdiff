"""Key renaming/aliasing support for env diff results."""
from dataclasses import dataclass, field
from typing import Dict
from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class RenameMap:
    """Maps old key names to new key names."""
    mapping: Dict[str, str] = field(default_factory=dict)

    def add(self, old: str, new: str) -> None:
        self.mapping[old] = new

    def apply(self, key: str) -> str:
        return self.mapping.get(key, key)


@dataclass
class RenameResult:
    """CompareResult with keys renamed according to a RenameMap."""
    original: CompareResult
    rename_map: RenameMap
    diffs: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.diffs = [
            KeyDiff(
                key=self.rename_map.apply(d.key),
                diff_type=d.diff_type,
                values=d.values,
                missing_in=d.missing_in,
            )
            for d in self.original.diffs
        ]

    @property
    def envs(self):
        return self.original.envs

    def has_differences(self) -> bool:
        return bool(self.diffs)


def rename_result(result: CompareResult, rename_map: RenameMap) -> RenameResult:
    """Return a new result with keys renamed according to rename_map."""
    return RenameResult(original=result, rename_map=rename_map)
