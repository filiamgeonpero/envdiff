"""Tests for envdiff.splitter."""
import pytest
from envdiff.splitter import SplitOptions, SplitResult, split_env


def make_opts(envs, sep="__", strip=True, fallback=None):
    return SplitOptions(envs=envs, prefix_sep=sep, strip_prefix=strip, fallback_env=fallback)


def test_basic_split_by_prefix():
    merged = {"prod__DB_HOST": "prod-db", "dev__DB_HOST": "dev-db"}
    result = split_env(merged, make_opts(["prod", "dev"]))
    assert result.envs["prod"] == {"DB_HOST": "prod-db"}
    assert result.envs["dev"] == {"DB_HOST": "dev-db"}


def test_unmatched_key_goes_to_unmatched():
    merged = {"GLOBAL_KEY": "value"}
    result = split_env(merged, make_opts(["prod", "dev"]))
    assert "GLOBAL_KEY" in result.unmatched
    assert result.has_unmatched()


def test_unmatched_key_goes_to_fallback_env():
    merged = {"GLOBAL_KEY": "value", "prod__X": "1"}
    result = split_env(merged, make_opts(["prod", "dev"], fallback="dev"))
    assert "GLOBAL_KEY" in result.envs["dev"]
    assert not result.has_unmatched()


def test_strip_prefix_false_keeps_original_key():
    merged = {"prod__DB": "host"}
    result = split_env(merged, make_opts(["prod"], strip=False))
    assert "prod__DB" in result.envs["prod"]


def test_custom_separator():
    merged = {"prod.DB": "host"}
    result = split_env(merged, make_opts(["prod"], sep="."))
    assert result.envs["prod"] == {"DB": "host"}


def test_case_insensitive_prefix_match():
    merged = {"PROD__KEY": "val"}
    result = split_env(merged, make_opts(["prod"]))
    assert "KEY" in result.envs["prod"]


def test_empty_merged_returns_empty_envs():
    result = split_env({}, make_opts(["prod", "dev"]))
    assert result.envs == {"prod": {}, "dev": {}}
    assert not result.has_unmatched()


def test_summary_contains_env_names():
    merged = {"prod__A": "1", "dev__B": "2"}
    result = split_env(merged, make_opts(["prod", "dev"]))
    s = result.summary()
    assert "prod" in s
    assert "dev" in s


def test_summary_reports_unmatched():
    merged = {"ORPHAN": "x"}
    result = split_env(merged, make_opts(["prod"]))
    assert "unmatched" in result.summary()


def test_multiple_keys_per_env():
    merged = {"prod__A": "1", "prod__B": "2", "dev__A": "3"}
    result = split_env(merged, make_opts(["prod", "dev"]))
    assert len(result.envs["prod"]) == 2
    assert len(result.envs["dev"]) == 1
