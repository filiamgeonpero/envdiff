"""Baseline management: save and load a reference snapshot of an env."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

BASELINE_VERSION = 1


class BaselineError(Exception):
    pass


def save_baseline(env: Dict[str, str], path: Path) -> None:
    """Persist a parsed env dict as a JSON baseline file."""
    payload = {"version": BASELINE_VERSION, "env": env}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_baseline(path: Path) -> Dict[str, str]:
    """Load a previously saved baseline. Raises BaselineError on problems."""
    if not path.exists():
        raise BaselineError(f"Baseline file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BaselineError(f"Invalid JSON in baseline: {exc}") from exc
    if payload.get("version") != BASELINE_VERSION:
        raise BaselineError(
            f"Unsupported baseline version: {payload.get('version')}"
        )
    env = payload.get("env")
    if not isinstance(env, dict):
        raise BaselineError("Baseline 'env' field is missing or not a dict.")
    return env
