"""Pin current env values as a reference snapshot for drift detection."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PIN_VERSION = 1
PIN_SUFFIX = ".pin.json"


class PinError(Exception):
    """Raised when a pin file cannot be read or is malformed."""


@dataclass
class PinEntry:
    key: str
    value: str
    pinned_at: float = field(default_factory=time.time)


@dataclass
class DriftItem:
    key: str
    pinned_value: str
    current_value: Optional[str]  # None means key is missing now

    def __str__(self) -> str:
        if self.current_value is None:
            return f"{self.key}: pinned={self.pinned_value!r} (now MISSING)"
        return f"{self.key}: pinned={self.pinned_value!r} current={self.current_value!r}"


@dataclass
class DriftResult:
    env_name: str
    drifted: List[DriftItem] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.drifted)

    def summary(self) -> str:
        if not self.has_drift:
            return f"{self.env_name}: no drift detected"
        lines = [f"{self.env_name}: {len(self.drifted)} drifted key(s)"]
        lines.extend(f"  {item}" for item in self.drifted)
        return "\n".join(lines)


def save_pin(env: Dict[str, str], path: Path) -> None:
    """Persist current env values to a pin file."""
    payload = {
        "version": PIN_VERSION,
        "pinned_at": time.time(),
        "entries": [{"key": k, "value": v} for k, v in env.items()],
    }
    path.write_text(json.dumps(payload, indent=2))


def load_pin(path: Path) -> Dict[str, str]:
    """Load pinned values from a pin file. Returns key→value mapping."""
    if not path.exists():
        raise PinError(f"Pin file not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PinError(f"Invalid JSON in pin file: {exc}") from exc
    if data.get("version") != PIN_VERSION:
        raise PinError(f"Unsupported pin version: {data.get('version')}")
    return {e["key"]: e["value"] for e in data.get("entries", [])}


def detect_drift(pinned: Dict[str, str], current: Dict[str, str], env_name: str = "env") -> DriftResult:
    """Compare pinned values against current env and return any drifted keys."""
    result = DriftResult(env_name=env_name)
    for key, pinned_value in pinned.items():
        current_value = current.get(key)
        if current_value != pinned_value:
            result.drifted.append(DriftItem(key=key, pinned_value=pinned_value, current_value=current_value))
    return result
