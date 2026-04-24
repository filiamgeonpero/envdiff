"""Scope filtering: restrict env keys to a named prefix scope."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeOptions:
    prefix: str
    separator: str = "_"
    strip_prefix: bool = False


@dataclass
class ScopeEntry:
    original_key: str
    scoped_key: str
    value: str

    def __str__(self) -> str:
        return f"{self.scoped_key}={self.value}"


@dataclass
class ScopeResult:
    scope: str
    entries: List[ScopeEntry] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)

    @property
    def matched(self) -> int:
        return len(self.entries)

    @property
    def total(self) -> int:
        return len(self.entries) + len(self.excluded)

    def as_dict(self) -> Dict[str, str]:
        return {e.scoped_key: e.value for e in self.entries}

    def summary(self) -> str:
        return (
            f"Scope '{self.scope}': {self.matched}/{self.total} keys matched."
        )


def scope_env(
    env: Dict[str, str],
    options: ScopeOptions,
) -> ScopeResult:
    """Filter *env* to keys that begin with *options.prefix* + separator.

    If *strip_prefix* is True the prefix and separator are removed from the
    key names in the result.
    """
    prefix_token = options.prefix.upper() + options.separator
    result = ScopeResult(scope=options.prefix)

    for key, value in env.items():
        if key.upper().startswith(prefix_token):
            scoped_key = key[len(prefix_token):] if options.strip_prefix else key
            result.entries.append(
                ScopeEntry(original_key=key, scoped_key=scoped_key, value=value)
            )
        else:
            result.excluded.append(key)

    return result
