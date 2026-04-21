"""Resolve variable references (e.g. ${VAR}) within .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_REF_RE = re.compile(r"\$\{([^}]+)\}")


@dataclass
class ResolveIssue:
    key: str
    ref: str  # the referenced variable name that could not be resolved

    def __str__(self) -> str:
        return f"{self.key}: unresolved reference '${{{self.ref}}}'"


@dataclass
class ResolveResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    issues: List[ResolveIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.ok:
            return f"All {len(self.resolved)} keys resolved successfully."
        return (
            f"{len(self.resolved)} keys resolved; "
            f"{len(self.issues)} unresolved reference(s)."
        )


def _resolve_value(
    value: str,
    env: Dict[str, str],
    key: str,
    issues: List[ResolveIssue],
) -> str:
    """Replace ${REF} placeholders in *value* using *env*."""

    def replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        ref = match.group(1)
        if ref in env:
            return env[ref]
        issues.append(ResolveIssue(key=key, ref=ref))
        return match.group(0)  # leave original text on failure

    return _REF_RE.sub(replacer, value)


def resolve_env(env: Dict[str, str]) -> ResolveResult:
    """Expand all ${VAR} references found in *env* values.

    Resolution is single-pass: references are looked up in the *original*
    mapping, so circular or chained references are not expanded.
    """
    issues: List[ResolveIssue] = []
    resolved: Dict[str, str] = {}

    for key, value in env.items():
        resolved[key] = _resolve_value(value, env, key, issues)

    return ResolveResult(resolved=resolved, issues=issues)
