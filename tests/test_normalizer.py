"""Tests for envdiff.normalizer."""
import pytest
from envdiff.normalizer import NormalizeOptions, NormalizeResult, normalize_env


def test_no_changes_for_clean_env():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = normalize_env(env)
    assert result.normalized == env
    assert not result.has_changes


def test_strip_whitespace_removes_surrounding_spaces():
    env = {"HOST": "  localhost  ", "PORT": "5432"}
    result = normalize_env(env)
    assert result.normalized["HOST"] == "localhost"
    assert "HOST" in result.changes


def test_strip_whitespace_disabled_preserves_spaces():
    env = {"HOST": "  localhost  "}
    opts = NormalizeOptions(strip_whitespace=False)
    result = normalize_env(env, opts)
    assert result.normalized["HOST"] == "  localhost  "
    assert not result.has_changes


def test_unify_booleans_true_variants():
    for val in ("True", "TRUE", "yes", "YES", "1", "on", "ON"):
        env = {"FLAG": val}
        result = normalize_env(env)
        assert result.normalized["FLAG"] == "true", f"Expected 'true' for {val!r}"


def test_unify_booleans_false_variants():
    for val in ("False", "FALSE", "no", "NO", "0", "off", "OFF"):
        env = {"FLAG": val}
        result = normalize_env(env)
        assert result.normalized["FLAG"] == "false", f"Expected 'false' for {val!r}"


def test_unify_booleans_disabled_preserves_value():
    env = {"FLAG": "Yes"}
    opts = NormalizeOptions(unify_booleans=False)
    result = normalize_env(env, opts)
    assert result.normalized["FLAG"] == "Yes"


def test_lowercase_keys_option():
    env = {"MY_HOST": "localhost"}
    opts = NormalizeOptions(lowercase_keys=True)
    result = normalize_env(env, opts)
    assert "my_host" in result.normalized
    assert "MY_HOST" not in result.normalized


def test_remove_empty_values():
    env = {"HOST": "localhost", "EMPTY": ""}
    opts = NormalizeOptions(remove_empty=True)
    result = normalize_env(env, opts)
    assert "EMPTY" not in result.normalized
    assert "HOST" in result.normalized


def test_remove_empty_disabled_keeps_empty():
    env = {"EMPTY": ""}
    opts = NormalizeOptions(remove_empty=False)
    result = normalize_env(env, opts)
    assert "EMPTY" in result.normalized
    assert result.normalized["EMPTY"] == ""


def test_none_value_preserved():
    env = {"KEY": None}
    result = normalize_env(env)
    assert result.normalized["KEY"] is None


def test_summary_no_changes():
    env = {"A": "1"}
    result = normalize_env(env)
    assert result.summary() == "No normalization changes."


def test_summary_with_changes():
    env = {"FLAG": "YES", "NAME": "  alice  "}
    result = normalize_env(env)
    summary = result.summary()
    assert "FLAG" in summary
    assert "NAME" in summary
    assert "Normalized" in summary


def test_original_is_unchanged():
    env = {"HOST": "  localhost  "}
    result = normalize_env(env)
    assert result.original["HOST"] == "  localhost  "
    assert result.normalized["HOST"] == "localhost"
