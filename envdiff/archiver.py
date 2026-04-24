"""archiver.py — snapshot and archive .env files with timestamps for audit trails.

Provides utilities to save versioned snapshots of parsed environments,
list archived versions, and restore or compare against a specific archive entry.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

FORMAT_VERSION = 1
DEFAULT_ARCHIVE_DIR = ".envdiff_archive"


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


@dataclass
class ArchiveEntry:
    """A single versioned snapshot of a named environment."""

    env_name: str
    timestamp: str  # ISO-8601 UTC
    keys: Dict[str, str]
    label: Optional[str] = None

    def summary(self) -> str:
        label_part = f" [{self.label}]" if self.label else ""
        return f"{self.env_name}{label_part} @ {self.timestamp} ({len(self.keys)} keys)"

    def to_dict(self) -> dict:
        return {
            "version": FORMAT_VERSION,
            "env_name": self.env_name,
            "timestamp": self.timestamp,
            "label": self.label,
            "keys": self.keys,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveEntry":
        if data.get("version") != FORMAT_VERSION:
            raise ArchiveError(
                f"Unsupported archive version: {data.get('version')!r}"
            )
        return cls(
            env_name=data["env_name"],
            timestamp=data["timestamp"],
            keys=data["keys"],
            label=data.get("label"),
        )


def _archive_path(archive_dir: Path, env_name: str, timestamp: str) -> Path:
    """Build a deterministic file path for an archive entry."""
    safe_name = env_name.replace(os.sep, "_").replace(" ", "_")
    safe_ts = timestamp.replace(":", "-")
    return archive_dir / f"{safe_name}__{safe_ts}.json"


def archive_env(
    env_name: str,
    keys: Dict[str, str],
    archive_dir: str = DEFAULT_ARCHIVE_DIR,
    label: Optional[str] = None,
) -> ArchiveEntry:
    """Persist a snapshot of *keys* under *env_name* to *archive_dir*.

    Returns the :class:`ArchiveEntry` that was written.
    """
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = ArchiveEntry(env_name=env_name, timestamp=ts, keys=keys, label=label)
    dest = Path(archive_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = _archive_path(dest, env_name, ts)
    path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
    return entry


def list_archives(
    archive_dir: str = DEFAULT_ARCHIVE_DIR,
    env_name: Optional[str] = None,
) -> List[ArchiveEntry]:
    """Return all archive entries in *archive_dir*, optionally filtered by *env_name*.

    Entries are sorted oldest-first by timestamp.
    """
    dest = Path(archive_dir)
    if not dest.exists():
        return []

    entries: List[ArchiveEntry] = []
    for path in sorted(dest.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entry = ArchiveEntry.from_dict(data)
        except (json.JSONDecodeError, KeyError, ArchiveError):
            # Skip corrupt or unrecognised files silently
            continue
        if env_name is None or entry.env_name == env_name:
            entries.append(entry)

    entries.sort(key=lambda e: e.timestamp)
    return entries


def load_archive(
    env_name: str,
    timestamp: str,
    archive_dir: str = DEFAULT_ARCHIVE_DIR,
) -> ArchiveEntry:
    """Load a specific archive entry identified by *env_name* and *timestamp*.

    Raises :class:`ArchiveError` if the entry cannot be found.
    """
    path = _archive_path(Path(archive_dir), env_name, timestamp)
    if not path.exists():
        raise ArchiveError(
            f"Archive entry not found: env={env_name!r}, timestamp={timestamp!r}"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"Invalid JSON in archive file {path}: {exc}") from exc
    return ArchiveEntry.from_dict(data)
