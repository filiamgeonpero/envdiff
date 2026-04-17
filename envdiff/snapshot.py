"""High-level snapshot workflow: diff current env against a saved baseline."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional

from envdiff.baseline import load_baseline, save_baseline, BaselineError
from envdiff.comparator import CompareResult, compare
from envdiff.parser import parse_env_file, EnvParseError


DEFAULT_BASELINE = Path(".envdiff_baseline.json")


def snapshot_save(env_path: Path, baseline_path: Path = DEFAULT_BASELINE) -> None:
    """Parse *env_path* and save it as the baseline."""
    env = parse_env_file(env_path)
    save_baseline(env, baseline_path)


def snapshot_diff(
    env_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
) -> CompareResult:
    """Compare *env_path* against the stored baseline and return a CompareResult."""
    baseline = load_baseline(baseline_path)
    current = parse_env_file(env_path)
    return compare(
        envs={"baseline": baseline, env_path.name: current}
    )


def compare(envs: Dict[str, Dict[str, str]]) -> CompareResult:
    """Thin wrapper so snapshot module doesn't import comparator's compare directly."""
    from envdiff.comparator import compare as _compare
    return _compare(envs)
