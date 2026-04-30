"""Tests for envdiff.flattener."""
import pytest
from envdiff.flattener import FlattenOptions, FlattenResult, flatten_env


def make_env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_flat_key_replaces_delimiter():
    env = make_env(DB__HOST="localhost")
    result = flatten_env(env)
    assert "DB.HOST" in result.flat_env


def test_original_key_preserved_in_entry():
    env = make_env(APP__SECRET__KEY="abc")
    result = flatten_env(env)
    assert result.entries[0].original_key == "APP__SECRET__KEY"


def test_flat_env_value_unchanged():
    env = make_env(DB__PORT="5432")
    result = flatten_env(env)
    assert result.flat_env["DB.PORT"] == "5432"


def test_depth_computed_correctly():
    env = make_env(A__B__C="v")
    result = flatten_env(env)
    assert result.entries[0].depth == 2


def test_single_segment_key_has_depth_zero():
    env = make_env(SIMPLE="value")
    result = flatten_env(env)
    assert result.entries[0].depth == 0


def test_no_changes_when_no_delimiter_in_keys():
    env = make_env(FOO="bar", BAZ="qux")
    result = flatten_env(env)
    assert not result.has_changes


def test_has_changes_true_when_delimiter_present():
    env = make_env(FOO__BAR="baz")
    result = flatten_env(env)
    assert result.has_changes


def test_prefix_filter_skips_non_matching_keys():
    env = make_env(DB__HOST="h", APP__NAME="n")
    opts = FlattenOptions(prefix_filter="DB")
    result = flatten_env(env, opts)
    assert "APP__NAME" in result.skipped
    assert len(result.entries) == 1


def test_prefix_filter_includes_matching_keys():
    env = make_env(DB__HOST="h", DB__PORT="5432")
    opts = FlattenOptions(prefix_filter="DB")
    result = flatten_env(env, opts)
    assert len(result.entries) == 2


def test_lowercase_keys_option():
    env = make_env(DB__HOST="localhost")
    opts = FlattenOptions(lowercase_keys=True)
    result = flatten_env(env, opts)
    assert "db.host" in result.flat_env


def test_custom_delimiter():
    env = {"DB_HOST": "localhost"}
    opts = FlattenOptions(delimiter="_")
    result = flatten_env(env, opts)
    assert "DB.HOST" in result.flat_env


def test_summary_contains_counts():
    env = make_env(A__B="v", PLAIN="x")
    result = flatten_env(env)
    s = result.summary()
    assert "2 keys processed" in s
    assert "1 renamed" in s


def test_empty_env_returns_empty_result():
    result = flatten_env({})
    assert result.flat_env == {}
    assert not result.has_changes
    assert result.skipped == []
