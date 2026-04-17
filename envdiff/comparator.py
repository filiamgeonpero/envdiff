"""Compare two parsed env dictionaries and produce a structured diff."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyDiff:
    key: str
    missing_in: Optional[str] = None   # env name where key is absent
    value_a: Optional[str] = None
    value_b: Optional[str] = None

    def __str__(self) -> str:
        if self.missing_in:
            return f"Key '{self.key}' missing in '{self.missing_in}'"
        return f"Key '{self.key}' has mismatched values: {self.value_a!r} vs {self.value_b!r}"


@dataclass
class CompareResult:
    missing_keys: List[KeyDiff] = field(default_factory=list)
    mismatched_values: List[KeyDiff] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.missing_keys or self.mismatched_values)

    @property
    def all_diffs(self) -> List[KeyDiff]:
        return self.missing_keys + self.mismatched_values


def compare(
    env_a: Dict[str, str],
    env_b: Dict[str, str],
    name_a: str = "env_a",
    name_b: str = "env_b",
) -> CompareResult:
    """Compare two env dicts and return a CompareResult."""
    missing: List[KeyDiff] = []
    mismatched: List[KeyDiff] = []

    all_keys = set(env_a) | set(env_b)

    for key in sorted(all_keys):
        in_a = key in env_a
        in_b = key in env_b

        if in_a and not in_b:
            missing.append(KeyDiff(key=key, missing_in=name_b))
        elif in_b and not in_a:
            missing.append(KeyDiff(key=key, missing_in=name_a))
        elif env_a[key] != env_b[key]:
            mismatched.append(KeyDiff(key=key, value_a=env_a[key], value_b=env_b[key]))

    return CompareResult(missing_keys=missing, mismatched_values=mismatched)
