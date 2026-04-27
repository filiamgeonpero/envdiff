"""interpolator.py — expand variable references within a single env mapping.

Unlike resolver.py (which resolves cross-file references), the interpolator
expands self-referential variables inside one env dict, e.g.:

    BASE_URL=https://example.com
    API_URL=${BASE_URL}/api/v1   ->  https://example.com/api/v1

Supports both ${VAR} and $VAR syntax.  Circular references are detected and
reported as InterpolationIssue entries rather than raising an exception.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Matches ${VAR_NAME} or $VAR_NAME (stops at non-word char)
_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationIssue:
    """Describes a problem encountered during interpolation."""

    key: str
    reference: str
    reason: str  # 'unresolved' | 'circular'

    def __str__(self) -> str:
        return f"{self.key}: ${self.reference} — {self.reason}"


@dataclass
class InterpolationResult:
    """Holds the interpolated env mapping and any issues found."""

    original: Dict[str, str]
    interpolated: Dict[str, str]
    issues: List[InterpolationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when no issues were encountered."""
        return len(self.issues) == 0

    def summary(self) -> str:
        """Return a human-readable one-line summary."""
        if self.ok:
            return "Interpolation complete — no issues."
        kinds = {i.reason for i in self.issues}
        parts = []
        if "circular" in kinds:
            n = sum(1 for i in self.issues if i.reason == "circular")
            parts.append(f"{n} circular reference(s)")
        if "unresolved" in kinds:
            n = sum(1 for i in self.issues if i.reason == "unresolved")
            parts.append(f"{n} unresolved reference(s)")
        return "Interpolation issues: " + ", ".join(parts) + "."


def _extract_refs(value: str) -> List[str]:
    """Return every variable name referenced inside *value*."""
    return [m.group(1) or m.group(2) for m in _REF_RE.finditer(value)]


def _expand(
    key: str,
    env: Dict[str, str],
    cache: Dict[str, Optional[str]],
    visiting: set,
    issues: List[InterpolationIssue],
) -> str:
    """Recursively expand *key* within *env*, tracking cycles via *visiting*."""
    if key in cache:
        return cache[key] or env.get(key, f"${{{key}}}")

    raw = env.get(key)
    if raw is None:
        # Key not in env — leave placeholder intact, issue recorded by caller
        return f"${{{key}}}"

    refs = _extract_refs(raw)
    if not refs:
        cache[key] = raw
        return raw

    if key in visiting:
        # Circular reference detected
        issues.append(InterpolationIssue(key=key, reference=key, reason="circular"))
        cache[key] = raw  # keep raw to avoid infinite loop
        return raw

    visiting.add(key)
    result = raw
    for ref in refs:
        if ref not in env:
            issues.append(
                InterpolationIssue(key=key, reference=ref, reason="unresolved")
            )
            # Leave the placeholder as-is
            continue
        if ref in visiting:
            issues.append(
                InterpolationIssue(key=key, reference=ref, reason="circular")
            )
            continue
        expanded_ref = _expand(ref, env, cache, visiting, issues)
        result = result.replace(f"${{{ref}}}", expanded_ref)
        # Also handle bare $REF style
        result = re.sub(rf"(?<!\{{)\${re.escape(ref)}(?![A-Za-z0-9_])", expanded_ref, result)

    visiting.discard(key)
    cache[key] = result
    return result


def interpolate_env(env: Dict[str, str]) -> InterpolationResult:
    """Expand all variable references in *env* and return an InterpolationResult.

    The original mapping is never mutated.
    """
    issues: List[InterpolationIssue] = []
    cache: Dict[str, Optional[str]] = {}
    interpolated: Dict[str, str] = {}

    for key in env:
        visiting: set = set()
        interpolated[key] = _expand(key, env, cache, visiting, issues)

    # De-duplicate issues (same key+reference pair may appear multiple times)
    seen = set()
    unique_issues: List[InterpolationIssue] = []
    for issue in issues:
        token = (issue.key, issue.reference, issue.reason)
        if token not in seen:
            seen.add(token)
            unique_issues.append(issue)

    return InterpolationResult(
        original=dict(env),
        interpolated=interpolated,
        issues=unique_issues,
    )
