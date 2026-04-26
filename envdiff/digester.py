"""Compute and compare checksums for .env files."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DigestEntry:
    name: str
    path: str
    sha256: str
    key_count: int

    def __str__(self) -> str:
        return f"{self.name}: {self.sha256[:12]}… ({self.key_count} keys)"


@dataclass
class DigestResult:
    entries: List[DigestEntry] = field(default_factory=list)
    _index: Dict[str, DigestEntry] = field(default_factory=dict, repr=False, init=False)

    def __post_init__(self) -> None:
        self._index = {e.name: e for e in self.entries}

    def get(self, name: str) -> Optional[DigestEntry]:
        return self._index.get(name)

    @property
    def all_match(self) -> bool:
        hashes = {e.sha256 for e in self.entries}
        return len(hashes) <= 1

    def mismatched_pairs(self) -> List[tuple[str, str]]:
        """Return pairs of env names whose digests differ."""
        pairs: List[tuple[str, str]] = []
        entries = self.entries
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                if entries[i].sha256 != entries[j].sha256:
                    pairs.append((entries[i].name, entries[j].name))
        return pairs

    def summary(self) -> str:
        if not self.entries:
            return "No files digested."
        if self.all_match:
            return f"All {len(self.entries)} file(s) have identical digests."
        pairs = self.mismatched_pairs()
        return f"{len(pairs)} differing pair(s) detected across {len(self.entries)} file(s)."


def _digest_env(env: Dict[str, str]) -> str:
    """Produce a deterministic SHA-256 digest of a parsed env mapping."""
    canonical = "\n".join(f"{k}={env[k]}" for k in sorted(env))
    return hashlib.sha256(canonical.encode()).hexdigest()


def digest_envs(named_envs: Dict[str, Dict[str, str]]) -> DigestResult:
    """Digest each named env dict and return a DigestResult."""
    entries: List[DigestEntry] = []
    for name, env in named_envs.items():
        sha = _digest_env(env)
        entries.append(DigestEntry(name=name, path=name, sha256=sha, key_count=len(env)))
    return DigestResult(entries=entries)


def digest_files(paths: List[Path]) -> DigestResult:
    """Parse and digest a list of .env file paths."""
    from envdiff.parser import parse_env_file

    named: Dict[str, Dict[str, str]] = {}
    for p in paths:
        named[p.name] = parse_env_file(p)
    result = digest_envs(named)
    for entry in result.entries:
        # Overwrite path with the real filesystem path
        matched = next((p for p in paths if p.name == entry.name), None)
        if matched:
            entry.path = str(matched)
    return result
