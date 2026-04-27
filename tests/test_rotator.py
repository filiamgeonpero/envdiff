"""Tests for envdiff.rotator."""
import pytest

from envdiff.rotator import RotateEntry, RotateResult, apply_rotation, rotate_env


ENV = {
    "DB_PASSWORD": "old_pass",
    "API_KEY": "old_key",
    "APP_NAME": "myapp",
}

ROTATION_MAP = {
    "DB_PASSWORD": "new_pass",
    "API_KEY": "new_key",
}


def test_rotated_keys_are_marked(tmp_path):
    result = rotate_env(ENV, ROTATION_MAP, env_name="prod")
    assert "DB_PASSWORD" in result.rotated_keys
    assert "API_KEY" in result.rotated_keys


def test_unchanged_keys_are_marked():
    result = rotate_env(ENV, ROTATION_MAP, env_name="prod")
    assert "APP_NAME" in result.unchanged_keys


def test_has_changes_true_when_any_rotated():
    result = rotate_env(ENV, ROTATION_MAP)
    assert result.has_changes is True


def test_has_changes_false_when_no_rotation():
    result = rotate_env(ENV, {}, env_name="staging")
    assert result.has_changes is False


def test_entry_new_value_set_for_rotated_key():
    result = rotate_env(ENV, ROTATION_MAP)
    entry = next(e for e in result.entries if e.key == "DB_PASSWORD")
    assert entry.new_value == "new_pass"
    assert entry.rotated is True


def test_entry_new_value_none_for_unchanged_key():
    result = rotate_env(ENV, ROTATION_MAP)
    entry = next(e for e in result.entries if e.key == "APP_NAME")
    assert entry.new_value is None
    assert entry.rotated is False


def test_apply_rotation_updates_values():
    result = rotate_env(ENV, ROTATION_MAP)
    updated = apply_rotation(ENV, result)
    assert updated["DB_PASSWORD"] == "new_pass"
    assert updated["API_KEY"] == "new_key"


def test_apply_rotation_preserves_unchanged_keys():
    result = rotate_env(ENV, ROTATION_MAP)
    updated = apply_rotation(ENV, result)
    assert updated["APP_NAME"] == "myapp"


def test_apply_rotation_does_not_mutate_original():
    result = rotate_env(ENV, ROTATION_MAP)
    apply_rotation(ENV, result)
    assert ENV["DB_PASSWORD"] == "old_pass"


def test_summary_contains_env_name():
    result = rotate_env(ENV, ROTATION_MAP, env_name="production")
    assert "production" in result.summary()


def test_summary_shows_rotated_count():
    result = rotate_env(ENV, ROTATION_MAP, env_name="prod")
    assert "2/3" in result.summary()


def test_str_entry_rotated():
    entry = RotateEntry(key="SECRET", old_value="x", new_value="y", rotated=True)
    assert "rotated" in str(entry)


def test_str_entry_unchanged():
    entry = RotateEntry(key="NAME", old_value="foo", new_value=None, rotated=False)
    assert "unchanged" in str(entry)
