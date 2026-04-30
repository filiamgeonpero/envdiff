"""masker.py – selectively mask env values for safe display or logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_SENSITIVE_PATTERNS = ("password", "secret", "token", "api_key", "private", "auth")
_DEFAULT_MASK = "***"


@dataclass
class MaskOptions:
    patterns: tuple[str, ...] = _DEFAULT_SENSITIVE_PATTERNS
    mask: str = _DEFAULT_MASK
    partial: bool = False  # if True, show first/last char around mask
    case_sensitive: bool = False


@dataclass
class MaskedEntry:
    key: str
    original: str
    masked: str
    was_masked: bool

    def __str__(self) -> str:
        status = "masked" if self.was_masked else "plain"
        return f"{self.key}={self.masked}  [{status}]"


@dataclass
class MaskResult:
    entries: List[MaskedEntry] = field(default_factory=list)

    @property
    def masked_env(self) -> Dict[str, str]:
        return {e.key: e.masked for e in self.entries}

    @property
    def masked_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.was_masked]

    def has_masked(self) -> bool:
        return any(e.was_masked for e in self.entries)

    def summary(self) -> str:
        total = len(self.entries)
        count = len(self.masked_keys)
        return f"{count}/{total} keys masked"


def _key_matches(key: str, patterns: tuple[str, ...], case_sensitive: bool) -> bool:
    haystack = key if case_sensitive else key.lower()
    return any((p if case_sensitive else p.lower()) in haystack for p in patterns)


def _apply_mask(value: str, mask: str, partial: bool) -> str:
    if not partial or len(value) < 3:
        return mask
    return f"{value[0]}{mask}{value[-1]}"


def mask_env(env: Dict[str, str], options: Optional[MaskOptions] = None) -> MaskResult:
    """Return a MaskResult with each key either masked or left plain."""
    opts = options or MaskOptions()
    entries: List[MaskedEntry] = []
    for key, value in env.items():
        should_mask = _key_matches(key, opts.patterns, opts.case_sensitive)
        masked_value = _apply_mask(value, opts.mask, opts.partial) if should_mask else value
        entries.append(MaskedEntry(key=key, original=value, masked=masked_value, was_masked=should_mask))
    return MaskResult(entries=entries)
