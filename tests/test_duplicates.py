"""Tests for envdiff.duplicates module."""
import pytest
from envdiff.duplicates import (
    detect_duplicates,
    find_duplicates_in_raw,
    DuplicateEntry,
    DuplicateResult,
)


DEV_LINES = [
    "APP_NAME=myapp\n",
    "DB_HOST=localhost\n",
    "DB_HOST=remotehost\n",  # duplicate
    "SECRET=abc\n",
]

CLEAN_LINES = [
    "APP_NAME=myapp\n",
    "DB_HOST=localhost\n",
    "SECRET=abc\n",
]


def test_no_duplicates_returns_empty():
    entries = find_duplicates_in_raw("clean", CLEAN_LINES)
    assert entries == []


def test_duplicate_key_detected():
    entries = find_duplicates_in_raw("dev", DEV_LINES)
    assert len(entries) == 1
    assert entries[0].key == "DB_HOST"
    assert entries[0].env_name == "dev"
    assert entries[0].occurrences == 2


def test_comments_and_blanks_ignored():
    lines = ["# comment\n", "\n", "KEY=val\n", "KEY=val2\n"]
    entries = find_duplicates_in_raw("env", lines)
    assert len(entries) == 1
    assert entries[0].key == "KEY"


def test_line_without_equals_ignored():
    lines = ["NOEQUALS\n", "KEY=val\n", "KEY=val2\n"]
    entries = find_duplicates_in_raw("env", lines)
    assert all(e.key == "KEY" for e in entries)


def test_detect_duplicates_aggregates_envs():
    result = detect_duplicates([("dev", DEV_LINES), ("prod", CLEAN_LINES)])
    assert result.has_duplicates()
    assert "dev" in result.envs
envs


def test_detect_duplicates_no_issues():
    result = detect_duplicates([("prod", CLEAN_LINES)])
    assert not result.has_duplicates()


def test_for_env_filters_correctly():
    result = detect_duplicates([("dev", DEV_LINES), ("prod", CLEAN_LINES)])
    dev_entries = result.for_env("dev")
    assert len(dev_entries) == 1
    assert result.for_env("prod") == []


def test_summary_no_duplicates():
    result = DuplicateResult(envs=["prod"])
    assert result.summary() == "No duplicate keys found."


def test_summary_with_duplicates():
    result = detect_duplicates([("dev", DEV_LINES)])
    summary = result.summary()
    assert "DB_HOST" in summary
    assert "dev" in summary


def test_str_entry():
    e = DuplicateEntry(key="FOO", env_name="staging", occurrences=3)
    assert "FOO" in str(e)
    assert "staging" in str(e)
    assert "3" in str(e)
