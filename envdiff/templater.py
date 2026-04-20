"""Generate .env template files from merged environment data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.merger import MergeResult


@dataclass
class TemplateOptions:
    include_values: bool = False
    placeholder: str = "<FILL_ME>"
    add_comments: bool = True
    group_by_prefix: bool = False


@dataclass
class TemplateResult:
    lines: List[str] = field(default_factory=list)
    total_keys: int = 0
    missing_in_any: int = 0

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def _prefix(key: str) -> str:
    parts = key.split("_", 1)
    return parts[0] if len(parts) > 1 else ""


def build_template(
    merge_result: MergeResult,
    options: Optional[TemplateOptions] = None,
) -> TemplateResult:
    """Build a .env template from a MergeResult."""
    if options is None:
        options = TemplateOptions()

    keys = list(merge_result.values.keys())
    result = TemplateResult(total_keys=len(keys))

    if options.group_by_prefix:
        keys = sorted(keys, key=lambda k: (_prefix(k), k))

    current_prefix: str = ""

    for key in keys:
        env_values: Dict[str, Optional[str]] = merge_result.values[key]
        is_missing_in_any = any(v is None for v in env_values.values())

        if is_missing_in_any:
            result.missing_in_any += 1

        if options.group_by_prefix:
            pfx = _prefix(key)
            if pfx and pfx != current_prefix:
                if result.lines:
                    result.lines.append("")
                if options.add_comments:
                    result.lines.append(f"# --- {pfx} ---")
                current_prefix = pfx

        if options.add_comments and is_missing_in_any:
            missing_envs = [e for e, v in env_values.items() if v is None]
            result.lines.append(f"# missing in: {', '.join(missing_envs)}")

        if options.include_values:
            first_value = next(
                (v for v in env_values.values() if v is not None),
                options.placeholder,
            )
            result.lines.append(f"{key}={first_value}")
        else:
            result.lines.append(f"{key}={options.placeholder}")

    return result
