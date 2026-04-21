"""Tests for envdiff.sanitizer."""

import pytest
from envdiff.sanitizer import sanitize_env, SanitizeResult


def test_clean_env_has_no_issues():
    result = sanitize_env({"HOST": "localhost", "PORT": "5432"}, "prod")
    assert result.clean
    assert result.sanitized == {"HOST": "localhost", "PORT": "5432"}


def test_lowercase_key_normalized_to_uppercase():
    result = sanitize_env({"host": "localhost"}, "prod")
    assert "HOST" in result.sanitized
    assert result.sanitized["HOST"] == "localhost"
    assert not result.clean
    assert any("normalized" in i.message for i in result.issues)


def test_mixed_case_key_normalized():
    result = sanitize_env({"My_Key": "value"}, "dev")
    assert "MY_KEY" in result.sanitized


def test_invalid_key_skipped():
    result = sanitize_env({"123INVALID": "value"}, "dev")
    assert "123INVALID" not in result.sanitized
    assert any("skipped" in i.message for i in result.issues)


def test_key_with_spaces_stripped_and_normalized():
    result = sanitize_env({"  db_host  ": "pg"}, "staging")
    assert "DB_HOST" in result.sanitized


def test_unsafe_control_char_removed_from_value():
    result = sanitize_env({"KEY": "val\x00ue"}, "prod")
    assert result.sanitized["KEY"] == "value"
    assert any("control characters" in i.message for i in result.issues)


def test_normal_value_unchanged():
    result = sanitize_env({"URL": "https://example.com/path?q=1"}, "prod")
    assert result.sanitized["URL"] == "https://example.com/path?q=1"
    assert result.clean


def test_normalize_keys_disabled_preserves_lowercase():
    result = sanitize_env({"host": "localhost"}, "dev", normalize_keys=False)
    assert "host" in result.sanitized
    assert result.clean


def test_strip_unsafe_disabled_preserves_control_chars():
    result = sanitize_env({"KEY": "val\x01ue"}, "dev", strip_unsafe_values=False)
    assert result.sanitized["KEY"] == "val\x01ue"
    assert result.clean


def test_summary_no_issues():
    result = sanitize_env({"A": "1"}, "prod")
    assert "no issues" in result.summary()


def test_summary_with_issues():
    result = sanitize_env({"a": "1"}, "dev")
    summary = result.summary()
    assert "dev" in summary
    assert "1 issue" in summary


def test_empty_env_is_clean():
    result = sanitize_env({}, "empty")
    assert result.clean
    assert result.sanitized == {}


def test_env_name_stored():
    result = sanitize_env({}, "myenv")
    assert result.env_name == "myenv"
