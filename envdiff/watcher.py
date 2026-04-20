"""Watch .env files for changes and report diffs automatically."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from envdiff.comparator import CompareResult, compare_envs
from envdiff.parser import parse_env_file


@dataclass
class WatchOptions:
    """Configuration for the file watcher."""

    # How often to poll for changes, in seconds
    interval: float = 1.0
    # Maximum number of change events to capture (0 = unlimited)
    max_events: int = 0
    # Whether to print a timestamp alongside each diff report
    show_timestamp: bool = True


@dataclass
class ChangeEvent:
    """Represents a detected change in one or more watched files."""

    changed_files: List[str]
    result: CompareResult
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        files = ", ".join(self.changed_files)
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        return f"[{ts}] Change detected in: {files}"


def _file_hash(path: Path) -> Optional[str]:
    """Return the MD5 hex digest of a file's contents, or None if unreadable."""
    try:
        data = path.read_bytes()
        return hashlib.md5(data).hexdigest()
    except OSError:
        return None


def _snapshot_hashes(paths: List[Path]) -> Dict[str, Optional[str]]:
    """Return a mapping of path string -> MD5 hash for each file."""
    return {str(p): _file_hash(p) for p in paths}


def watch_envs(
    paths: List[Path],
    env_names: List[str],
    options: Optional[WatchOptions] = None,
    on_change: Optional[Callable[[ChangeEvent], None]] = None,
) -> List[ChangeEvent]:
    """Poll the given .env files and invoke *on_change* whenever any file
    changes.  Returns the list of all captured :class:`ChangeEvent` objects.

    Parameters
    ----------
    paths:
        Ordered list of .env file paths to monitor.
    env_names:
        Human-readable labels for each file (must match *paths* in length).
    options:
        Polling configuration.  Defaults are used when *None*.
    on_change:
        Optional callback invoked with each :class:`ChangeEvent`.  If *None*
        the caller must inspect the returned list.

    Notes
    -----
    This function blocks indefinitely unless *options.max_events* is set to a
    positive integer, in which case it returns after that many events have been
    captured.  Use :func:`watch_envs` inside a thread or process when you need
    non-blocking behaviour.
    """
    if options is None:
        options = WatchOptions()

    if len(paths) != len(env_names):
        raise ValueError("paths and env_names must have the same length")

    events: List[ChangeEvent] = []
    previous_hashes = _snapshot_hashes(paths)

    try:
        while True:
            time.sleep(options.interval)
            current_hashes = _snapshot_hashes(paths)

            changed: List[str] = [
                name
                for path, name in zip(paths, env_names)
                if current_hashes[str(path)] != previous_hashes[str(path)]
            ]

            if changed:
                # Re-parse all files and build a fresh comparison
                envs: Dict[str, Dict[str, str]] = {}
                for path, name in zip(paths, env_names):
                    try:
                        envs[name] = parse_env_file(path)
                    except Exception:  # noqa: BLE001
                        envs[name] = {}

                result = compare_envs(envs)
                event = ChangeEvent(
                    changed_files=changed,
                    result=result,
                )
                events.append(event)

                if on_change is not None:
                    on_change(event)

                previous_hashes = current_hashes

                if options.max_events > 0 and len(events) >= options.max_events:
                    break

    except KeyboardInterrupt:
        pass

    return events
