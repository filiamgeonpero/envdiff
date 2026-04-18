"""Tests for envdiff.grouper."""
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.grouper import group_by_prefix, _extract_prefix


def make_result(diffs):
    return CompareResult(env_names=["a", "b"], diffs=diffs)


def make_diff(key, missing_in=None, values=None):
    return KeyDiff(
        key=key,
        missing_in=missing_in or [],
        values=values or {"a": "v", "b": "v"},
    )


# --- _extract_prefix ---

def test_extract_prefix_with_underscore():
    assert _extract_prefix("DB_HOST") == "DB"


def test_extract_prefix_no_separator():
    assert _extract_prefix("HOST") is None


def test_extract_prefix_multiple_underscores():
    assert _extract_prefix("AWS_S3_BUCKET") == "AWS"


# --- group_by_prefix ---

def test_empty_result_returns_empty_groups():
    result = make_result([])
    grouped = group_by_prefix(result)
    assert grouped.groups == {}
    assert grouped.ungrouped.diffs == []


def test_keys_with_prefix_form_group():
    diffs = [make_diff("DB_HOST"), make_diff("DB_PORT")]
    grouped = group_by_prefix(make_result(diffs))
    assert "DB" in grouped.groups
    assert len(grouped.groups["DB"]) == 2


def test_keys_without_prefix_go_to_ungrouped():
    diffs = [make_diff("HOST"), make_diff("PORT")]
    grouped = group_by_prefix(make_result(diffs))
    assert grouped.groups == {}
    assert len(grouped.ungrouped.diffs) == 2


def test_multiple_prefixes_separated():
    diffs = [make_diff("DB_HOST"), make_diff("AWS_KEY"), make_diff("DB_PORT")]
    grouped = group_by_prefix(make_result(diffs))
    assert "DB" in grouped.groups
    assert "AWS" in grouped.groups
    assert len(grouped.groups["DB"]) == 2
    assert len(grouped.groups["AWS"]) == 1


def test_min_group_size_moves_small_groups_to_ungrouped():
    diffs = [make_diff("AWS_KEY"), make_diff("DB_HOST"), make_diff("DB_PORT")]
    grouped = group_by_prefix(make_result(diffs), min_group_size=2)
    assert "DB" in grouped.groups
    assert "AWS" not in grouped.groups
    assert any(d.key == "AWS_KEY" for d in grouped.ungrouped.diffs)


def test_all_groups_includes_ungrouped_when_nonempty():
    diffs = [make_diff("DB_HOST"), make_diff("LONE")]
    grouped = group_by_prefix(make_result(diffs))
    names = [g.prefix for g in grouped.all_groups()]
    assert "DB" in names
    assert "(ungrouped)" in names


def test_all_groups_excludes_ungrouped_when_empty():
    diffs = [make_diff("DB_HOST")]
    grouped = group_by_prefix(make_result(diffs))
    names = [g.prefix for g in grouped.all_groups()]
    assert "(ungrouped)" not in names


def test_group_has_differences_true_when_diffs_present():
    diffs = [make_diff("DB_HOST", missing_in=["b"])]
    grouped = group_by_prefix(make_result(diffs))
    assert grouped.groups["DB"].has_differences is True
