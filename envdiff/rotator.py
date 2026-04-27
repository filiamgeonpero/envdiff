"""Key rotation helper: detect stale keys and suggest replacements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RotateEntry:
    key: str
    old_value: str
    new_value: Optional[str]
    rotated: bool

    def __str__(self) -> str:
        status = "rotated" if self.rotated else "unchanged"
        return f"{self.key}: [{status}]"


@dataclass
class RotateResult:
    env_name: str
    entries: List[RotateEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.rotated for e in self.entries)

    @property
    def rotated_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.rotated]

    @property
    def unchanged_keys(self) -> List[str]:
        return [e.key for e in self.entries if not e.rotated]

    def summary(self) -> str:
        total = len(self.entries)
        changed = len(self.rotated_keys)
        return f"{self.env_name}: {changed}/{total} keys rotated"


def rotate_env(
    env: Dict[str, str],
    rotation_map: Dict[str, str],
    env_name: str = "env",
) -> RotateResult:
    """Apply a rotation map to an env dict.

    Keys present in *rotation_map* get their value replaced with the mapped
    value.  Keys absent from the map are left untouched.
    """
    entries: List[RotateEntry] = []
    for key, old_value in env.items():
        if key in rotation_map:
            new_value = rotation_map[key]
            entries.append(RotateEntry(key=key, old_value=old_value, new_value=new_value, rotated=True))
        else:
            entries.append(RotateEntry(key=key, old_value=old_value, new_value=None, rotated=False))
    return RotateResult(env_name=env_name, entries=entries)


def apply_rotation(env: Dict[str, str], result: RotateResult) -> Dict[str, str]:
    """Return a new env dict with rotated values applied."""
    out = dict(env)
    for entry in result.entries:
        if entry.rotated and entry.new_value is not None:
            out[entry.key] = entry.new_value
    return out
