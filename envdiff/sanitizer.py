"""Sanitize env dicts by normalizing keys and stripping unsafe characters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SanitizeIssue:
    key: str
    original_key: str
    message: str

    def __str__(self) -> str:
        return f"{self.original_key!r} -> {self.key!r}: {self.message}"


@dataclass
class SanitizeResult:
    env_name: str
    sanitized: Dict[str, str]
    issues: List[SanitizeIssue] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.clean:
            return f"{self.env_name}: no issues found"
        lines = [f"{self.env_name}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


_UNSAFE_VALUE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_VALID_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _normalize_key(key: str) -> Optional[str]:
    """Uppercase and strip surrounding whitespace; return None if still invalid."""
    normalized = key.strip().upper()
    if _VALID_KEY_RE.match(normalized):
        return normalized
    return None


def sanitize_env(
    env: Dict[str, str],
    env_name: str = "env",
    *,
    strip_unsafe_values: bool = True,
    normalize_keys: bool = True,
) -> SanitizeResult:
    """Return a sanitized copy of *env* and a list of issues encountered."""
    sanitized: Dict[str, str] = {}
    issues: List[SanitizeIssue] = []

    for raw_key, raw_value in env.items():
        key = raw_key

        if normalize_keys:
            normalized = _normalize_key(raw_key)
            if normalized is None:
                issues.append(
                    SanitizeIssue(
                        key=raw_key,
                        original_key=raw_key,
                        message="invalid key characters; key skipped",
                    )
                )
                continue
            if normalized != raw_key:
                issues.append(
                    SanitizeIssue(
                        key=normalized,
                        original_key=raw_key,
                        message="key normalized to uppercase",
                    )
                )
            key = normalized

        value = raw_value
        if strip_unsafe_values:
            cleaned = _UNSAFE_VALUE_RE.sub("", raw_value)
            if cleaned != raw_value:
                issues.append(
                    SanitizeIssue(
                        key=key,
                        original_key=raw_key,
                        message="unsafe control characters removed from value",
                    )
                )
                value = cleaned

        sanitized[key] = value

    return SanitizeResult(env_name=env_name, sanitized=sanitized, issues=issues)
