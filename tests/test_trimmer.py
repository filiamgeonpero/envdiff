"""Tests for envdiff.trimmer."""

from __future__ import annotations

import pytest

from envdiff.trimmer import TrimOptions, TrimResult, trim_env


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "SECRET_KEY": "abc123",
    "UNUSED_VAR": "junk",
}


def test_no_keep_keys_returns_all_keys():
    result = trim_env(SAMPLE_ENV)
    assert result.trimmed == SAMPLE_ENV
    assert result.removed == []
    assert not result.has_changes


def test_keep_keys_removes_others():
    opts = TrimOptions(keep_keys={"APP_NAME", "DB_HOST"})
    result = trim_env(SAMPLE_ENV, opts)
    assert set(result.trimmed.keys()) == {"APP_NAME", "DB_HOST"}
    assert "UNUSED_VAR" in result.removed
    assert "SECRET_KEY" in result.removed


def test_removed_list_excludes_kept_keys():
    opts = TrimOptions(keep_keys={"APP_NAME", "DB_HOST", "DB_PORT", "SECRET_KEY", "UNUSED_VAR"})
    result = trim_env(SAMPLE_ENV, opts)
    assert result.removed == []
    assert not result.has_changes


def test_dry_run_does_not_modify_trimmed():
    opts = TrimOptions(keep_keys={"APP_NAME"}, dry_run=True)
    result = trim_env(SAMPLE_ENV, opts)
    # trimmed should equal original in dry-run mode
    assert result.trimmed == SAMPLE_ENV
    # but removed still lists the surplus keys
    assert len(result.removed) == len(SAMPLE_ENV) - 1
    assert result.dry_run is True
    assert result.has_changes


def test_original_is_always_unchanged():
    opts = TrimOptions(keep_keys={"APP_NAME"})
    result = trim_env(SAMPLE_ENV, opts)
    assert result.original == SAMPLE_ENV


def test_summary_no_changes():
    result = trim_env(SAMPLE_ENV)
    assert result.summary() == "No unused keys found."


def test_summary_with_changes():
    opts = TrimOptions(keep_keys={"APP_NAME"})
    result = trim_env(SAMPLE_ENV, opts)
    assert "Removed" in result.summary()
    assert str(len(result.removed)) in result.summary()


def test_summary_dry_run_prefix():
    opts = TrimOptions(keep_keys={"APP_NAME"}, dry_run=True)
    result = trim_env(SAMPLE_ENV, opts)
    assert result.summary().startswith("[dry-run]")


def test_empty_env_no_changes():
    opts = TrimOptions(keep_keys={"SOME_KEY"})
    result = trim_env({}, opts)
    assert result.trimmed == {}
    assert result.removed == []
    assert not result.has_changes


def test_unknown_keep_key_does_not_add_entries():
    opts = TrimOptions(keep_keys={"DOES_NOT_EXIST"})
    result = trim_env({"REAL_KEY": "val"}, opts)
    assert "DOES_NOT_EXIST" not in result.trimmed
    assert "REAL_KEY" in result.removed
