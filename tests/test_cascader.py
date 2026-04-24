"""Tests for envdiff.cascader."""
from __future__ import annotations

import pytest

from envdiff.cascader import CascadeEntry, CascadeResult, cascade_envs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_named(*pairs):
    """Accept (name, dict) pairs and return list for cascade_envs."""
    return list(pairs)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_single_file_returns_all_keys():
    result = cascade_envs([("base", {"A": "1", "B": "2"})])
    assert result.resolved() == {"A": "1", "B": "2"}


def test_later_file_overrides_earlier():
    result = cascade_envs([
        ("base", {"KEY": "old"}),
        ("prod", {"KEY": "new"}),
    ])
    assert result.resolved()["KEY"] == "new"


def test_non_overlapping_keys_all_present():
    result = cascade_envs([
        ("a", {"X": "1"}),
        ("b", {"Y": "2"}),
    ])
    assert result.resolved() == {"X": "1", "Y": "2"}


def test_override_recorded_in_entry():
    result = cascade_envs([
        ("base", {"K": "base_val"}),
        ("override", {"K": "override_val"}),
    ])
    entry = result.entries["K"]
    assert entry.source == "override"
    assert "base" in entry.overridden_by


def test_no_override_when_key_unique():
    result = cascade_envs([
        ("base", {"A": "1"}),
        ("extra", {"B": "2"}),
    ])
    assert result.entries["A"].overridden_by == []
    assert result.entries["B"].overridden_by == []


def test_exclusive_keys_detected():
    result = cascade_envs([
        ("base", {"SHARED": "x", "ONLY_BASE": "y"}),
        ("prod", {"SHARED": "z"}),
    ])
    assert "ONLY_BASE" in result.exclusive
    assert "SHARED" not in result.exclusive


def test_env_names_stored():
    result = cascade_envs([("dev", {}), ("prod", {})])
    assert result.env_names == ["dev", "prod"]


def test_summary_contains_key_count():
    result = cascade_envs([
        ("base", {"A": "1", "B": "2"}),
        ("prod", {"A": "99"}),
    ])
    s = result.summary()
    assert "2" in s  # total keys


def test_three_file_cascade_last_wins():
    result = cascade_envs([
        ("base", {"DB": "localhost"}),
        ("stage", {"DB": "stage-host"}),
        ("prod", {"DB": "prod-host"}),
    ])
    assert result.resolved()["DB"] == "prod-host"
    entry = result.entries["DB"]
    assert entry.source == "prod"
    assert set(entry.overridden_by) == {"base", "stage"}


def test_empty_envs_returns_empty_result():
    result = cascade_envs([])
    assert result.resolved() == {}
    assert result.entries == {}


def test_cascade_entry_str_with_override():
    entry = CascadeEntry(key="K", value="v", source="prod", overridden_by=["base"])
    assert "prod" in str(entry)
    assert "base" in str(entry)


def test_cascade_entry_str_no_override():
    entry = CascadeEntry(key="K", value="v", source="base")
    text = str(entry)
    assert "K" in text
    assert "base" in text
