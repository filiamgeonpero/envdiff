"""Key aliasing: map legacy or alternate key names to canonical names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasMap:
    """Holds canonical -> list-of-aliases mappings."""
    _map: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, canonical: str, *aliases: str) -> None:
        """Register one or more aliases for a canonical key."""
        existing = self._map.setdefault(canonical, [])
        for alias in aliases:
            if alias not in existing:
                existing.append(alias)

    def canonical_for(self, key: str) -> Optional[str]:
        """Return the canonical name if *key* is a known alias, else None."""
        for canonical, aliases in self._map.items():
            if key in aliases:
                return canonical
        return None

    def aliases_for(self, canonical: str) -> List[str]:
        """Return aliases registered for *canonical* (empty list if none)."""
        return list(self._map.get(canonical, []))

    def all_aliases(self) -> Dict[str, List[str]]:
        """Return a copy of the full alias mapping."""
        return {k: list(v) for k, v in self._map.items()}


@dataclass
class AliasResult:
    """Outcome of applying an AliasMap to an env dict."""
    original: Dict[str, str]
    resolved: Dict[str, str]
    renames: Dict[str, str]  # alias_key -> canonical_key

    @property
    def rename_count(self) -> int:
        return len(self.renames)

    def summary(self) -> str:
        if not self.renames:
            return "No aliases resolved."
        lines = [f"Resolved {self.rename_count} alias(es):"]
        for alias, canonical in self.renames.items():
            lines.append(f"  {alias} -> {canonical}")
        return "\n".join(lines)


def apply_aliases(env: Dict[str, str], alias_map: AliasMap) -> AliasResult:
    """Return a new env dict with aliased keys replaced by canonical names.

    If both an alias and its canonical key exist in *env*, the canonical
    value takes precedence and the alias entry is dropped.
    """
    resolved: Dict[str, str] = {}
    renames: Dict[str, str] = {}

    for key, value in env.items():
        canonical = alias_map.canonical_for(key)
        if canonical is not None:
            renames[key] = canonical
            if canonical not in env:  # don't overwrite real canonical
                resolved[canonical] = value
        else:
            resolved[key] = value

    return AliasResult(original=dict(env), resolved=resolved, renames=renames)
