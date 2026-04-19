"""Detect duplicate keys across multiple env files."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DuplicateEntry:
    key: str
    env_name: str
    occurrences: int

    def __str__(self) -> str:
        return f"{self.key} in '{self.env_name}' appears {self.occurrences}x"


@dataclass
class DuplicateResult:
    envs: List[str]
    _entries: List[DuplicateEntry] = field(default_factory=list)

    def has_duplicates(self) -> bool:
        return len(self._entries) > 0

    def entries(self) -> List[DuplicateEntry]:
        return list(self._entries)

    def for_env(self, env_name: str) -> List[DuplicateEntry]:
        return [e for e in self._entries if e.env_name == env_name]

    def summary(self) -> str:
        if not self.has_duplicates():
            return "No duplicate keys found."
        lines = [f"Duplicate keys found ({len(self._entries)} total):"]
        for e in self._entries:
            lines.append(f"  {e}")
        return "\n".join(lines)


def find_duplicates_in_raw(env_name: str, raw_lines: List[str]) -> List[DuplicateEntry]:
    """Count key occurrences in raw lines (before deduplication by parser)."""
    counts: Dict[str, int] = {}
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        counts[key] = counts.get(key, 0) + 1
    return [
        DuplicateEntry(key=k, env_name=env_name, occurrences=v)
        for k, v in counts.items()
        if v > 1
    ]


def detect_duplicates(named_lines: List[Tuple[str, List[str]]]) -> DuplicateResult:
    """named_lines: list of (env_name, raw_lines) pairs."""
    env_names = [name for name, _ in named_lines]
    result = DuplicateResult(envs=env_names)
    for env_name, lines in named_lines:
        result._entries.extend(find_duplicates_in_raw(env_name, lines))
    return result
