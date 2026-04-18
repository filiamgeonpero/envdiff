"""Tests for envdiff.scorer."""
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.scorer import SimilarityScore, score_result


def make_result(envs: dict, diffs=None) -> CompareResult:
    if diffs is None:
        diffs = []
    return CompareResult(envs=envs, diffs=diffs, env_names=list(envs.keys()))


def test_identical_envs_score_is_one():
    envs = {"a": {"KEY": "val"}, "b": {"KEY": "val"}}
    result = make_result(envs)
    score = score_result(result)
    assert score.overall == 1.0
    assert score.missing_keys == 0
    assert score.mismatched_values == 0


def test_completely_different_keys():
    envs = {"a": {"FOO": "1"}, "b": {"BAR": "2"}}
    diffs = [
        KeyDiff(key="FOO", is_missing=True, env_name="b", value_a="1", value_b=None),
        KeyDiff(key="BAR", is_missing=True, env_name="a", value_a=None, value_b="2"),
    ]
    result = make_result(envs, diffs)
    score = score_result(result)
    assert score.total_keys == 2
    assert score.shared_keys == 0
    assert score.key_overlap == 0.0
    assert score.overall < 0.5


def test_partial_overlap():
    envs = {
        "a": {"A": "1", "B": "2", "C": "3"},
        "b": {"A": "1", "B": "99", "D": "4"},
    }
    diffs = [
        KeyDiff(key="B", is_missing=False, env_name=None, value_a="2", value_b="99"),
        KeyDiff(key="C", is_missing=True, env_name="b", value_a="3", value_b=None),
        KeyDiff(key="D", is_missing=True, env_name="a", value_a=None, value_b="4"),
    ]
    result = make_result(envs, diffs)
    score = score_result(result)
    assert score.total_keys == 4
    assert score.shared_keys == 2  # A and B
    assert score.matching_values == 1  # only A matches
    assert score.mismatched_values == 1
    assert score.missing_keys == 2


def test_value_similarity_all_match():
    envs = {"a": {"X": "1", "Y": "2"}, "b": {"X": "1", "Y": "2"}}
    result = make_result(envs)
    score = score_result(result)
    assert score.value_similarity == 1.0


def test_summary_string_contains_score():
    envs = {"a": {"KEY": "v"}, "b": {"KEY": "v"}}
    result = make_result(envs)
    score = score_result(result)
    summary = score.summary()
    assert "Score:" in summary
    assert "%" in summary


def test_empty_envs_score_is_one():
    envs = {"a": {}, "b": {}}
    result = make_result(envs)
    score = score_result(result)
    assert score.overall == 1.0
    assert score.total_keys == 0
