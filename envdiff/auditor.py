"""Audit trail for .env file changes — records who changed what and when."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

AUDIT_VERSION = 1


@dataclass
class AuditEntry:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    env_file: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))

    def __str__(self) -> str:
        action = "added" if self.old_value is None else ("removed" if self.new_value is None else "changed")
        return f"[{self.timestamp}] {self.author}: {action} {self.key!r} in {self.env_file}"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "env_file": self.env_file,
            "timestamp": self.timestamp,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            key=d["key"],
            old_value=d.get("old_value"),
            new_value=d.get("new_value"),
            env_file=d["env_file"],
            timestamp=d["timestamp"],
            author=d["author"],
        )


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def for_key(self, key: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.key == key]

    def for_file(self, env_file: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.env_file == env_file]

    def summary(self) -> str:
        if not self.entries:
            return "No audit entries recorded."
        return "\n".join(str(e) for e in self.entries)


class AuditError(Exception):
    pass


def save_audit(log: AuditLog, path: Path) -> None:
    data = {"version": AUDIT_VERSION, "entries": [e.to_dict() for e in log.entries]}
    path.write_text(json.dumps(data, indent=2))


def load_audit(path: Path) -> AuditLog:
    if not path.exists():
        raise AuditError(f"Audit log not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AuditError(f"Invalid audit log JSON: {exc}") from exc
    if data.get("version") != AUDIT_VERSION:
        raise AuditError(f"Unsupported audit log version: {data.get('version')}")
    return AuditLog(entries=[AuditEntry.from_dict(e) for e in data.get("entries", [])])


def diff_to_audit(old: Dict[str, str], new: Dict[str, str], env_file: str) -> List[AuditEntry]:
    """Produce audit entries by comparing two env dicts."""
    entries: List[AuditEntry] = []
    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        ov, nv = old.get(key), new.get(key)
        if ov != nv:
            entries.append(AuditEntry(key=key, old_value=ov, new_value=nv, env_file=env_file))
    return entries
