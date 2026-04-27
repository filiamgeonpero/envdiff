"""Strip unused or stale keys from an env file based on a reference set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class StripOptions:
    """Options controlling strip behaviour."""
    dry_run: bool = False
    keep_unknown: bool = False  # when True, unknown keys are kept rather than removed


@dataclass
class StripResult:
    """Outcome of stripping an env dict against a reference set."""
    original: Dict[str, str]
    stripped: Dict[str, str]
    removed: List[str] = field(default_factory=list)
    kept_unknown: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.removed)

    def summary(self) -> str:
        if not self.has_changes():
            return "No keys removed."
        parts = [f"Removed {len(self.removed)} key(s): {', '.join(sorted(self.removed))}"]
        if self.kept_unknown:
            parts.append(
                f"Kept {len(self.kept_unknown)} unknown key(s): {', '.join(sorted(self.kept_unknown))}"
            )
        return "; ".join(parts)


def strip_env(
    env: Dict[str, str],
    reference_keys: Set[str],
    options: Optional[StripOptions] = None,
) -> StripResult:
    """Remove keys from *env* that are not present in *reference_keys*.

    Args:
        env: The environment dictionary to strip.
        reference_keys: The authoritative set of valid keys.
        options: Behavioural flags.

    Returns:
        A :class:`StripResult` describing what was (or would be) removed.
    """
    if options is None:
        options = StripOptions()

    removed: List[str] = []
    kept_unknown: List[str] = []
    stripped: Dict[str, str] = {}

    for key, value in env.items():
        if key in reference_keys:
            stripped[key] = value
        else:
            if options.keep_unknown:
                kept_unknown.append(key)
                stripped[key] = value
            else:
                removed.append(key)

    if options.dry_run:
        # Report what *would* happen but return the original mapping unchanged.
        return StripResult(
            original=env,
            stripped=dict(env),
            removed=removed,
            kept_unknown=kept_unknown,
        )

    return StripResult(
        original=env,
        stripped=stripped,
        removed=removed,
        kept_unknown=kept_unknown,
    )
