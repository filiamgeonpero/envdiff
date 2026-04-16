"""Compare parsed .env files and report missing or mismatched keys."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyDiff:
    key: str
    status: str  # 'missing_in', 'mismatch'
    missing_in: Optional[str] = None
    values: Optional[Dict[str, str]] = None

    def __str__(self) -> str:
        if self.status == "missing_in":
            return f"[MISSING] '{self.key}' not found in '{self.missing_in}'"
        elif self.status == "mismatch":
            parts = ", ".join(f"{env}={v!r}" for env, v in (self.values or {}).items())
            return f"[MISMATCH] '{self.key}': {parts}"
        return f"[UNKNOWN] '{self.key}'"


@dataclass
class CompareResult:
    env_names: List[str]
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return len(self.diffs) > 0

    def missing_keys(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "missing_in"]

    def mismatched_keys(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "mismatch"]


def compare_envs(
    envs: Dict[str, Dict[str, str]],
    ignore_values: bool = False,
) -> CompareResult:
    """Compare multiple parsed env dicts.

    Args:
        envs: mapping of env_name -> {key: value}
        ignore_values: if True, only report missing keys, not mismatches

    Returns:
        CompareResult with all detected diffs
    """
    env_names = list(envs.keys())
    result = CompareResult(env_names=env_names)

    all_keys: set = set()
    for env_dict in envs.values():
        all_keys.update(env_dict.keys())

    for key in sorted(all_keys):
        present_in = {name: envs[name][key] for name in env_names if key in envs[name]}
        absent_from = [name for name in env_names if key not in envs[name]]

        for missing_env in absent_from:
            result.diffs.append(KeyDiff(key=key, status="missing_in", missing_in=missing_env))

        if not ignore_values and len(absent_from) == 0:
            unique_values = set(present_in.values())
            if len(unique_values) > 1:
                result.diffs.append(KeyDiff(key=key, status="mismatch", values=present_in))

    return result
