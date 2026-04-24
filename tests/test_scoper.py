"""Tests for envdiff.scoper."""
import pytest
from envdiff.scoper import ScopeOptions, ScopeResult, ScopeEntry, scope_env


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_NAME": "envdiff",
    "APP_DEBUG": "true",
    "SECRET_KEY": "abc123",
}


def test_scope_filters_to_prefix():
    opts = ScopeOptions(prefix="DB")
    result = scope_env(SAMPLE_ENV, opts)
    keys = [e.scoped_key for e in result.entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "APP_NAME" not in keys


def test_excluded_keys_recorded():
    opts = ScopeOptions(prefix="DB")
    result = scope_env(SAMPLE_ENV, opts)
    assert "APP_NAME" in result.excluded
    assert "SECRET_KEY" in result.excluded


def test_strip_prefix_removes_prefix():
    opts = ScopeOptions(prefix="DB", strip_prefix=True)
    result = scope_env(SAMPLE_ENV, opts)
    keys = [e.scoped_key for e in result.entries]
    assert "HOST" in keys
    assert "PORT" in keys
    assert "DB_HOST" not in keys


def test_strip_prefix_original_key_preserved():
    opts = ScopeOptions(prefix="DB", strip_prefix=True)
    result = scope_env(SAMPLE_ENV, opts)
    originals = [e.original_key for e in result.entries]
    assert "DB_HOST" in originals


def test_no_match_returns_empty_entries():
    opts = ScopeOptions(prefix="REDIS")
    result = scope_env(SAMPLE_ENV, opts)
    assert result.matched == 0
    assert len(result.excluded) == len(SAMPLE_ENV)


def test_matched_and_total_counts():
    opts = ScopeOptions(prefix="APP")
    result = scope_env(SAMPLE_ENV, opts)
    assert result.matched == 2
    assert result.total == len(SAMPLE_ENV)


def test_as_dict_returns_mapping():
    opts = ScopeOptions(prefix="APP", strip_prefix=True)
    result = scope_env(SAMPLE_ENV, opts)
    d = result.as_dict()
    assert d["NAME"] == "envdiff"
    assert d["DEBUG"] == "true"


def test_summary_contains_scope_name():
    opts = ScopeOptions(prefix="DB")
    result = scope_env(SAMPLE_ENV, opts)
    assert "DB" in result.summary()


def test_summary_contains_counts():
    opts = ScopeOptions(prefix="DB")
    result = scope_env(SAMPLE_ENV, opts)
    assert "2" in result.summary()
    assert str(len(SAMPLE_ENV)) in result.summary()


def test_case_insensitive_prefix_match():
    env = {"db_host": "localhost", "db_port": "5432", "APP_NAME": "x"}
    opts = ScopeOptions(prefix="db")
    result = scope_env(env, opts)
    assert result.matched == 2


def test_str_representation_of_entry():
    entry = ScopeEntry(original_key="DB_HOST", scoped_key="HOST", value="localhost")
    assert str(entry) == "HOST=localhost"
