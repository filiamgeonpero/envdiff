"""Tests for envdiff.comparator module."""

import pytest
from envdiff.comparator import compare_envs, CompareResult, KeyDiff


ENV_A = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
ENV_B = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}


def test_no_differences_identical_envs():
    result = compare_envs({"a": ENV_A.copy(), "b": ENV_A.copy()})
    assert not result.has_differences


def test_detects_missing_key_in_second_env():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    missing = result.missing_keys()
    missing_keys_set = {d.key for d in missing}
    assert "DEBUG" in missing_keys_set
    assert "SECRET" in missing_keys_set


def test_missing_key_records_correct_env_name():
    result = compare_envs({"dev": {"FOO": "1", "BAR": "2"}, "prod": {"FOO": "1"}})
    missing = result.missing_keys()
    assert len(missing) == 1
    assert missing[0].key == "BAR"
    assert missing[0].missing_in == "prod"


def test_detects_value_mismatch():
    result = compare_envs({"a": ENV_A, "b": ENV_B})
    mismatches = result.mismatched_keys()
    mismatch_keys = {d.key for d in mismatches}
    assert "HOST" in mismatch_keys


def test_no_mismatch_for_same_values():
    result = compare_envs({"a": {"PORT": "5432"}, "b": {"PORT": "5432"}})
    assert len(result.mismatched_keys()) == 0


def test_ignore_values_skips_mismatches():
    result = compare_envs({"a": ENV_A, "b": ENV_B}, ignore_values=True)
    assert len(result.mismatched_keys()) == 0


def test_three_envs_missing_key():
    envs = {
        "dev": {"A": "1", "B": "2"},
        "staging": {"A": "1"},
        "prod": {"A": "1", "B": "2"},
    }
    result = compare_envs(envs)
    missing = result.missing_keys()
    assert len(missing) == 1
    assert missing[0].missing_in == "staging"


def test_keydiff_str_missing():
    d = KeyDiff(key="FOO", status="missing_in", missing_in="prod")
    assert "MISSING" in str(d)
    assert "FOO" in str(d)
    assert "prod" in str(d)


def test_keydiff_str_mismatch():
    d = KeyDiff(key="HOST", status="mismatch", values={"dev": "localhost", "prod": "example.com"})
    assert "MISMATCH" in str(d)
    assert "HOST" in str(d)


def test_result_env_names():
    result = compare_envs({"x": {}, "y": {}})
    assert result.env_names == ["x", "y"]
