"""Tests for envdiff.sorter."""
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.sorter import SortOptions, SortedResult, sort_result


def make_result(diffs):
    return CompareResult(envs=["a.env", "b.env"], diffs=diffs)


def make_diff(key, env=None, is_missing=False, values=None):
    return KeyDiff(
        key=key,
        env=env,
        is_missing=is_missing,
        values=values or {},
    )


def test_sort_by_key_default():
    result = make_result([
        make_diff("ZEBRA"),
        make_diff("APPLE"),
        make_diff("MANGO"),
    ])
    sorted_result = sort_result(result)
    assert sorted_result.keys() == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_by_key_reverse():
    result = make_result([
        make_diff("APPLE"),
        make_diff("ZEBRA"),
    ])
    sorted_result = sort_result(result, SortOptions(by="key", reverse=True))
    assert sorted_result.keys() == ["ZEBRA", "APPLE"]


def test_sort_by_env():
    result = make_result([
        make_diff("KEY", env="z.env"),
        make_diff("KEY", env="a.env"),
    ])
    sorted_result = sort_result(result, SortOptions(by="env"))
    assert sorted_result.diffs[0].env == "a.env"
    assert sorted_result.diffs[1].env == "z.env"


def test_sort_by_diff_type_missing_first():
    result = make_result([
        make_diff("B_KEY", is_missing=False),
        make_diff("A_KEY", is_missing=True),
    ])
    sorted_result = sort_result(result, SortOptions(by="diff_type"))
    assert sorted_result.diffs[0].key == "A_KEY"
    assert sorted_result.diffs[1].key == "B_KEY"


def test_sort_by_diff_type_reverse():
    result = make_result([
        make_diff("A_KEY", is_missing=True),
        make_diff("B_KEY", is_missing=False),
    ])
    sorted_result = sort_result(result, SortOptions(by="diff_type", reverse=True))
    assert sorted_result.diffs[0].key == "B_KEY"
    assert sorted_result.diffs[1].key == "A_KEY"


def test_sorted_result_preserves_envs():
    result = make_result([make_diff("X")])
    sorted_result = sort_result(result)
    assert sorted_result.envs == ["a.env", "b.env"]


def test_invalid_sort_key_raises():
    result = make_result([make_diff("X")])
    with pytest.raises(ValueError, match="Unknown sort key"):
        sort_result(result, SortOptions(by="invalid"))


def test_empty_diffs_returns_empty():
    result = make_result([])
    sorted_result = sort_result(result)
    assert sorted_result.diffs == []
    assert sorted_result.keys() == []
