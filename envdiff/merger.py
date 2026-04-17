"""Merge multiple .env files into a unified template with all known keys."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MergeOptions:
    fill_missing: bool = True
    placeholder: str = ""
    comment_source: bool = True


@dataclass
class MergeResult:
    keys: List[str] = field(default_factory=list)
    # key -> list of (env_name, value)
    values: Dict[str, List[Tuple[str, Optional[str]]]] = field(default_factory=dict)

    def as_template(self, options: MergeOptions) -> str:
        lines: List[str] = []
        for key in self.keys:
            entries = self.values.get(key, [])
            sources = {env: val for env, val in entries if val is not None}
            if options.comment_source and sources:
                first_env, first_val = next(iter(sources.items()))
                lines.append(f"# from {first_env}")
            val = next(iter(sources.values())) if sources else options.placeholder
            lines.append(f"{key}={val}")
        return "\n".join(lines)


def merge_envs(
    envs: Dict[str, Dict[str, str]],
    options: Optional[MergeOptions] = None,
) -> MergeResult:
    """Merge multiple parsed env dicts into a MergeResult."""
    if options is None:
        options = MergeOptions()

    seen: Dict[str, int] = {}
    ordered_keys: List[str] = []
    for env_dict in envs.values():
        for key in env_dict:
            if key not in seen:
                seen[key] = len(ordered_keys)
                ordered_keys.append(key)

    result = MergeResult(keys=ordered_keys)
    for key in ordered_keys:
        result.values[key] = [
            (env_name, env_dict.get(key))
            for env_name, env_dict in envs.items()
        ]
    return result
