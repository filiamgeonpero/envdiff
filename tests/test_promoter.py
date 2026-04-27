"""Tests for envdiff.promoter."""
import pytest
from envdiff.promoter import PromoteChange, promote_env


SOURCE = {"DB_HOST": "prod-db", "DB_PORT": "5432", "API_KEY": "secret"}
TARGET = {"DB_HOST": "staging-db", "APP_ENV": "staging"}


def test_all_source_keys_promoted_by_default():
    result = promote_env(SOURCE, TARGET)
    for key in SOURCE:
        assert key in result.promoted


def test_target_only_keys_preserved():
    result = promote_env(SOURCE, TARGET)
    assert result.promoted["APP_ENV"] == "staging"


def test_overwrite_replaces_existing_value():
    result = promote_env(SOURCE, TARGET)
    assert result.promoted["DB_HOST"] == "prod-db"


def test_overwrite_false_skips_existing_key():
    result = promote_env(SOURCE, TARGET, overwrite=False)
    assert result.promoted["DB_HOST"] == "staging-db"
    assert "DB_HOST" in result.skipped


def test_overwrite_false_still_adds_missing_key():
    result = promote_env(SOURCE, TARGET, overwrite=False)
    assert result.promoted["DB_PORT"] == "5432"


def test_explicit_keys_limits_promotion():
    result = promote_env(SOURCE, TARGET, keys=["DB_HOST"])
    assert result.promoted["DB_HOST"] == "prod-db"
    assert result.promoted.get("DB_PORT") is None


def test_explicit_key_not_in_source_is_skipped():
    result = promote_env(SOURCE, TARGET, keys=["NONEXISTENT"])
    assert "NONEXISTENT" in result.skipped
    assert len(result.changes) == 0


def test_has_changes_true_when_keys_promoted():
    result = promote_env(SOURCE, TARGET)
    assert result.has_changes is True


def test_has_changes_false_when_nothing_promoted():
    result = promote_env(SOURCE, TARGET, keys=[])
    assert result.has_changes is False


def test_change_records_old_value_for_overwrite():
    result = promote_env(SOURCE, TARGET)
    change = next(c for c in result.changes if c.key == "DB_HOST")
    assert change.target_value == "staging-db"
    assert change.source_value == "prod-db"


def test_change_records_none_for_new_key():
    result = promote_env(SOURCE, TARGET)
    change = next(c for c in result.changes if c.key == "API_KEY")
    assert change.target_value is None


def test_source_not_mutated():
    original = dict(SOURCE)
    promote_env(SOURCE, TARGET)
    assert SOURCE == original


def test_target_not_mutated():
    original = dict(TARGET)
    promote_env(SOURCE, TARGET)
    assert TARGET == original


def test_summary_contains_env_names():
    result = promote_env(SOURCE, TARGET, source_name="prod", target_name="staging")
    s = result.summary()
    assert "prod" in s
    assert "staging" in s


def test_change_str_shows_arrow():
    c = PromoteChange(key="FOO", source_value="new", target_value="old")
    assert "->" in str(c)


def test_change_str_missing_shows_missing():
    c = PromoteChange(key="FOO", source_value="new", target_value=None)
    assert "missing" in str(c)
