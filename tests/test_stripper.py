"""Tests for envdiff.stripper."""
import pytest
from envdiff.stripper import StripOptions, StripResult, strip_env


REF_KEYS = {"DB_HOST", "DB_PORT", "APP_SECRET"}


def make_env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_no_extra_keys_returns_same_env():
    env = make_env(DB_HOST="localhost", DB_PORT="5432")
    result = strip_env(env, REF_KEYS)
    assert result.stripped == env
    assert result.removed == []
    assert not result.has_changes()


def test_extra_key_is_removed():
    env = make_env(DB_HOST="localhost", STALE_KEY="old")
    result = strip_env(env, REF_KEYS)
    assert "STALE_KEY" not in result.stripped
    assert "STALE_KEY" in result.removed
    assert result.has_changes()


def test_all_reference_keys_present_are_kept():
    env = make_env(DB_HOST="h", DB_PORT="5432", APP_SECRET="s", EXTRA="x")
    result = strip_env(env, REF_KEYS)
    for key in REF_KEYS:
        assert key in result.stripped


def test_original_is_not_mutated():
    env = make_env(DB_HOST="localhost", ORPHAN="gone")
    original_copy = dict(env)
    strip_env(env, REF_KEYS)
    assert env == original_copy


# ---------------------------------------------------------------------------
# dry_run
# ---------------------------------------------------------------------------

def test_dry_run_does_not_remove_keys():
    env = make_env(DB_HOST="h", STALE="s")
    result = strip_env(env, REF_KEYS, StripOptions(dry_run=True))
    assert "STALE" in result.stripped
    assert "STALE" in result.removed  # reported but not actually removed


def test_dry_run_stripped_equals_original():
    env = make_env(DB_HOST="h", STALE="s")
    result = strip_env(env, REF_KEYS, StripOptions(dry_run=True))
    assert result.stripped == env


# ---------------------------------------------------------------------------
# keep_unknown
# ---------------------------------------------------------------------------

def test_keep_unknown_preserves_extra_keys():
    env = make_env(DB_HOST="h", UNKNOWN_KEY="v")
    result = strip_env(env, REF_KEYS, StripOptions(keep_unknown=True))
    assert "UNKNOWN_KEY" in result.stripped
    assert "UNKNOWN_KEY" in result.kept_unknown
    assert result.removed == []


def test_keep_unknown_not_counted_as_removed():
    env = make_env(DB_HOST="h", UNKNOWN_KEY="v")
    result = strip_env(env, REF_KEYS, StripOptions(keep_unknown=True))
    assert not result.has_changes()


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    env = make_env(DB_HOST="h")
    result = strip_env(env, REF_KEYS)
    assert result.summary() == "No keys removed."


def test_summary_lists_removed_keys():
    env = make_env(DB_HOST="h", OLD="x", STALE="y")
    result = strip_env(env, REF_KEYS)
    summary = result.summary()
    assert "OLD" in summary
    assert "STALE" in summary


def test_summary_mentions_kept_unknown():
    env = make_env(DB_HOST="h", MYSTERY="m")
    result = strip_env(env, REF_KEYS, StripOptions(keep_unknown=True))
    # no removals, so summary is the plain "no keys removed" message
    assert "No keys removed" in result.summary()
