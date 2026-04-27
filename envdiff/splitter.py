"""Split a merged env dict into per-environment files based on key prefixes or a mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SplitOptions:
    """Controls how a merged env is split into separate environments."""
    envs: List[str]                          # ordered list of environment names
    prefix_sep: str = "__"                   # separator between env prefix and key
    strip_prefix: bool = True                # remove the env prefix from output keys
    fallback_env: Optional[str] = None       # env that receives keys with no prefix match


@dataclass
class SplitResult:
    """Outcome of splitting a merged env dict."""
    options: SplitOptions
    envs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)

    def has_unmatched(self) -> bool:
        return bool(self.unmatched)

    def summary(self) -> str:
        parts = [f"{env}: {len(keys)} key(s)" for env, keys in self.envs.items()]
        if self.unmatched:
            parts.append(f"unmatched: {len(self.unmatched)} key(s)")
        return ", ".join(parts) if parts else "no keys"


def split_env(merged: Dict[str, str], options: SplitOptions) -> SplitResult:
    """Distribute keys from *merged* into per-environment buckets.

    A key is assigned to an environment when it starts with
    ``<env><sep>`` (case-insensitive).  Keys that match no environment
    go to *fallback_env* (if set) or to ``SplitResult.unmatched``.
    """
    result = SplitResult(options=options, envs={env: {} for env in options.envs})

    for raw_key, value in merged.items():
        matched = False
        for env in options.envs:
            prefix = f"{env}{options.prefix_sep}"
            if raw_key.lower().startswith(prefix.lower()):
                out_key = raw_key[len(prefix):] if options.strip_prefix else raw_key
                result.envs[env][out_key] = value
                matched = True
                break
        if not matched:
            if options.fallback_env and options.fallback_env in result.envs:
                result.envs[options.fallback_env][raw_key] = value
            else:
                result.unmatched[raw_key] = value

    return result
