"""Tests for envdiff.filter module."""
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.filter import FilterOptions, filter_result


def make_result():
    diffs = [
        KeyDiff(key="DB_HOST", missing_in=["staging"]),
        KeyDiff(key="API_KEY", missing_in=["production"]),
        KeyDiff(key="PORT", values={"dev": "3000", "staging": "4000"}),
        KeyDiff(key="DEBUG", values={"dev": "true", "staging": "false"}),
    ]
    return CompareResult(env_names=["dev", "staging", "production"], diffs=diffs)


def test_no_filter_returns_all_diffs():
    result = make_result()
    opts = FilterOptions()
    filtered = filter_result(result, opts)
    assert len(filtered.diffs) == 4


def test_include_keys_limits_results():
    result = make_result()
    opts = FilterOptions(include_keys={"PORT", "DEBUG"})
    filtered = filter_result(result, opts)
    assert {d.key for d in filtered.diffs} == {"PORT", "DEBUG"}


def test_exclude_keys_removes_entries():
    result = make_result()
    opts = FilterOptions(exclude_keys={"API_KEY", "DEBUG"})
    filtered = filter_result(result, opts)
    keys = {d.key for d in filtered.diffs}
    assert "API_KEY" not in keys
    assert "DEBUG" not in keys
    assert len(filtered.diffs) == 2


def test_only_missing_returns_missing_diffs():
    result = make_result()
    opts = FilterOptions(only_missing=True)
    filtered = filter_result(result, opts)
    assert all(d.values is None for d in filtered.diffs)
    assert len(filtered.diffs) == 2


def test_only_mismatched_returns_value_diffs():
    result = make_result()
    opts = FilterOptions(only_mismatched=True)
    filtered = filter_result(result, opts)
    assert all(d.values is not None for d in filtered.diffs)
    assert len(filtered.diffs) == 2


def test_env_names_preserved_after_filter():
    result = make_result()
    opts = FilterOptions(only_missing=True)
    filtered = filter_result(result, opts)
    assert filtered.env_names == result.env_names


def test_empty_include_set_returns_no_diffs():
    result = make_result()
    opts = FilterOptions(include_keys=set())
    filtered = filter_result(result, opts)
    assert len(filtered.diffs) == 0
