"""Apply a patch (dict of key->value) to an env file, updating or adding keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PatchResult:
    path: str
    updated: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    content: str = ""

    @property
    def has_changes(self) -> bool:
        return bool(self.updated or self.added)

    def summary(self) -> str:
        parts = []
        if self.updated:
            parts.append(f"{len(self.updated)} updated")
        if self.added:
            parts.append(f"{len(self.added)} added")
        return ", ".join(parts) if parts else "no changes"


def patch_env_file(
    path: str,
    patch: Dict[str, str],
    *,
    add_missing: bool = True,
    dry_run: bool = False,
) -> PatchResult:
    """Apply *patch* to the env file at *path*.

    Keys already present are updated in-place; keys absent are appended
    at the end unless *add_missing* is False.
    """
    src = Path(path)
    original_lines: List[str] = src.read_text().splitlines(keepends=True) if src.exists() else []

    result = PatchResult(path=path)
    remaining = dict(patch)
    out_lines: List[str] = []

    for line in original_lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("#") or "=" not in stripped:
            out_lines.append(line)
            continue
        key, _, _val = stripped.partition("=")
        key = key.strip()
        if key in remaining:
            new_val = remaining.pop(key)
            out_lines.append(f"{key}={new_val}\n")
            result.updated.append(key)
        else:
            out_lines.append(line)

    if add_missing:
        for key, val in remaining.items():
            out_lines.append(f"{key}={val}\n")
            result.added.append(key)

    result.content = "".join(out_lines)
    if not dry_run:
        src.write_text(result.content)
    return result
