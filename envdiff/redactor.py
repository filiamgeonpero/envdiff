"""Redact sensitive values in env diffs and reports."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict

DEFAULT_PATTERNS = [
    re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)", re.I),
]

REDACTED = "***REDACTED***"


@dataclass
class RedactOptions:
    patterns: list = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    placeholder: str = REDACTED


def _key_is_sensitive(key: str, options: RedactOptions) -> bool:
    return any(p.search(key) for p in options.patterns)


def redact_env(env: Dict[str, str], options: RedactOptions | None = None) -> Dict[str, str]:
    """Return a copy of env with sensitive values replaced."""
    if options is None:
        options = RedactOptions()
    return {
        k: (options.placeholder if _key_is_sensitive(k, options) else v)
        for k, v in env.items()
    }


def redact_envs(
    envs: Dict[str, Dict[str, str]], options: RedactOptions | None = None
) -> Dict[str, Dict[str, str]]:
    """Redact multiple named envs."""
    if options is None:
        options = RedactOptions()
    return {name: redact_env(env, options) for name, env in envs.items()}
