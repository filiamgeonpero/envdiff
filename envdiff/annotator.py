"""Annotate env file keys with metadata such as source environment and change status."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envdiff.comparator import CompareResult, KeyDiff


@dataclass
class AnnotatedKey:
    key: str
    values: Dict[str, Optional[str]]
    status: str  # 'ok', 'missing', 'mismatch'
    envs_missing: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"{self.key} [{self.status.upper()}]"]
        for env, val in self.values.items():
            display = repr(val) if val is not None else "<missing>"
            parts.append(f"  {env}: {display}")
        return "\n".join(parts)


@dataclass
class AnnotationResult:
    env_names: List[str]
    keys: List[AnnotatedKey]

    def by_status(self, status: str) -> List[AnnotatedKey]:
        return [k for k in self.keys if k.status == status]

    def summary(self) -> str:
        ok = len(self.by_status("ok"))
        missing = len(self.by_status("missing"))
        mismatch = len(self.by_status("mismatch"))
        return f"ok={ok} missing={missing} mismatch={mismatch}"

    def by_env_missing(self, env_name: str) -> List[AnnotatedKey]:
        """Return all keys that are missing in the given environment."""
        return [k for k in self.keys if env_name in k.envs_missing]


def annotate_result(result: CompareResult) -> AnnotationResult:
    """Build an AnnotationResult from a CompareResult."""
    env_names = result.env_names

    # Collect all keys
    all_keys: Dict[str, Dict[str, Optional[str]]] = {}
    for env in env_names:
        for key, val in result.envs[env].items():
            all_keys.setdefault(key, {})[env] = val

    diff_map: Dict[str, KeyDiff] = {d.key: d for d in result.diffs}

    annotated: List[AnnotatedKey] = []
    for key in sorted(all_keys.keys()):
        values = {env: all_keys[key].get(env) for env in env_names}
        if key in diff_map:
            diff = diff_map[key]
            status = "missing" if diff.is_missing else "mismatch"
            missing_envs = [diff.env_name] if diff.is_missing else []
        else:
            status = "ok"
            missing_envs = []
        annotated.append(AnnotatedKey(key=key, values=values, status=status, envs_missing=missing_envs))

    return AnnotationResult(env_names=env_names, keys=annotated)
