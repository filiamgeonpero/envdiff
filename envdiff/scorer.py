"""Score how similar two env files are based on key overlap and value matches."""
from dataclasses import dataclass
from typing import Dict

from envdiff.comparator import CompareResult


@dataclass
class SimilarityScore:
    total_keys: int
    shared_keys: int
    matching_values: int
    missing_keys: int
    mismatched_values: int

    @property
    def key_overlap(self) -> float:
        """Fraction of keys present in both envs."""
        if self.total_keys == 0:
            return 1.0
        return self.shared_keys / self.total_keys

    @property
    def value_similarity(self) -> float:
        """Fraction of shared keys whose values agree."""
        if self.shared_keys == 0:
            return 1.0
        return self.matching_values / self.shared_keys

    @property
    def overall(self) -> float:
        """Weighted combination of key overlap and value similarity."""
        return round(0.4 * self.key_overlap + 0.6 * self.value_similarity, 4)

    def summary(self) -> str:
        return (
            f"Keys: {self.shared_keys}/{self.total_keys} shared, "
            f"{self.missing_keys} missing, "
            f"{self.mismatched_values} mismatched | "
            f"Score: {self.overall:.2%}"
        )


def score_result(result: CompareResult) -> SimilarityScore:
    """Compute a similarity score from a CompareResult."""
    all_keys: set = set()
    # Collect all keys seen across both envs via diffs
    missing_keys = 0
    mismatched_values = 0

    for diff in result.diffs:
        all_keys.add(diff.key)
        if diff.is_missing:
            missing_keys += 1
        else:
            mismatched_values += 1

    # Keys that appear in diffs are either missing or mismatched
    # Keys not in diffs are shared and matching
    # We need total_keys from both envs combined
    env_names = result.env_names
    if len(env_names) >= 2:
        keys_a = set(result.envs[env_names[0]].keys())
        keys_b = set(result.envs[env_names[1]].keys())
        total_keys = len(keys_a | keys_b)
        shared_keys = len(keys_a & keys_b)
    else:
        total_keys = len(all_keys)
        shared_keys = total_keys - missing_keys

    matching_values = shared_keys - mismatched_values

    return SimilarityScore(
        total_keys=total_keys,
        shared_keys=shared_keys,
        matching_values=max(matching_values, 0),
        missing_keys=missing_keys,
        mismatched_values=mismatched_values,
    )
