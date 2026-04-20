"""Tests for envdiff.differ_summary."""
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.differ_summary import (
    EnvPairSummary,
    MultiSummary,
    summarise_pair,
    summarise_many,
)


def make_result(env_a: str, env_b: str, diffs: list) -> CompareResult:
    return CompareResult(env_names=[env_a, env_b], diffs=diffs)


def make_missing(key: str, missing_in: str) -> KeyDiff:
    return KeyDiff(key=key, missing_in=missing_in, values={})


def make_mismatch(key: str, values: dict) -> KeyDiff:
    return KeyDiff(key=key, missing_in=None, values=values)


# --- EnvPairSummary ---

def test_match_count_computed_correctly():
    s = EnvPairSummary(env_a="a", env_b="b", total_keys=10, missing_count=3, mismatch_count=2)
    assert s.match_count == 5


def test_match_count_all_matching():
    s = EnvPairSummary(env_a="a", env_b="b", total_keys=5, missing_count=0, mismatch_count=0)
    assert s.match_count == 5


# --- summarise_pair ---

def test_summarise_pair_no_diffs():
    result = make_result("prod", "staging", [])
    summary = summarise_pair(result)
    assert summary.env_a == "prod"
    assert summary.env_b == "staging"
    assert summary.total_keys == 0
    assert summary.missing_count == 0
    assert summary.mismatch_count == 0


def test_summarise_pair_counts_missing():
    diffs = [make_missing("KEY_A", "staging"), make_missing("KEY_B", "prod")]
    result = make_result("prod", "staging", diffs)
    summary = summarise_pair(result)
    assert summary.missing_count == 2
    assert summary.mismatch_count == 0
    assert summary.total_keys == 2


def test_summarise_pair_counts_mismatches():
    diffs = [make_mismatch("DB_URL", {"prod": "x", "staging": "y"})]
    result = make_result("prod", "staging", diffs)
    summary = summarise_pair(result)
    assert summary.mismatch_count == 1
    assert summary.missing_count == 0


def test_summarise_pair_mixed_diffs():
    diffs = [
        make_missing("SECRET", "staging"),
        make_mismatch("PORT", {"prod": "80", "staging": "8080"}),
    ]
    result = make_result("prod", "staging", diffs)
    summary = summarise_pair(result)
    assert summary.missing_count == 1
    assert summary.mismatch_count == 1
    assert summary.total_keys == 2


def test_summarise_pair_env_names_stored():
    result = make_result("alpha", "beta", [])
    summary = summarise_pair(result)
    assert summary.env_a == "alpha"
    assert summary.env_b == "beta"


# --- summarise_many / MultiSummary ---

def test_summarise_many_empty():
    ms = summarise_many([])
    assert ms.total_pairs == 0
    assert not ms.any_differences
    assert ms.worst_pair() is None


def test_summarise_many_counts_pairs():
    r1 = make_result("a", "b", [make_missing("X", "b")])
    r2 = make_result("b", "c", [])
    ms = summarise_many([r1, r2])
    assert ms.total_pairs == 2


def test_any_differences_true_when_missing():
    r = make_result("a", "b", [make_missing("K", "b")])
    ms = summarise_many([r])
    assert ms.any_differences


def test_any_differences_false_when_clean():
    r = make_result("a", "b", [])
    ms = summarise_many([r])
    assert not ms.any_differences


def test_worst_pair_selected_correctly():
    r1 = make_result("a", "b", [make_missing("X", "b")])
    r2 = make_result("b", "c", [
        make_missing("Y", "c"),
        make_mismatch("Z", {"b": "1", "c": "2"}),
        make_missing("W", "b"),
    ])
    ms = summarise_many([r1, r2])
    worst = ms.worst_pair()
    assert worst is not None
    assert worst.env_a == "b"
    assert worst.env_b == "c"
