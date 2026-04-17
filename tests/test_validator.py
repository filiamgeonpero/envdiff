"""Tests for envdiff.validator."""
import pytest
from envdiff.validator import KeyRule, validate_env, ValidationResult


SCHEMA = {
    "DATABASE_URL": KeyRule(required=True, pattern=r"postgres://.+"),
    "DEBUG": KeyRule(required=False, pattern=r"true|false"),
    "SECRET_KEY": KeyRule(required=True, allow_empty=False),
    "OPTIONAL_TAG": KeyRule(required=False, allow_empty=True),
}


def test_valid_env_passes():
    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "DEBUG": "true",
        "SECRET_KEY": "abc123",
    }
    result = validate_env(env, SCHEMA, "production")
    assert result.valid
    assert result.errors == []


def test_missing_required_key_fails():
    env = {"DEBUG": "true", "SECRET_KEY": "abc"}
    result = validate_env(env, SCHEMA, "staging")
    assert not result.valid
    keys = [e.key for e in result.errors]
    assert "DATABASE_URL" in keys


def test_missing_optional_key_does_not_fail():
    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "abc",
    }
    result = validate_env(env, SCHEMA, "dev")
    assert result.valid


def test_empty_value_fails_when_not_allowed():
    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "",
    }
    result = validate_env(env, SCHEMA, "dev")
    assert not result.valid
    assert any(e.key == "SECRET_KEY" for e in result.errors)


def test_empty_value_allowed_when_flagged():
    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "x",
        "OPTIONAL_TAG": "",
    }
    result = validate_env(env, SCHEMA, "dev")
    assert result.valid


def test_pattern_mismatch_fails():
    env = {
        "DATABASE_URL": "mysql://localhost/db",
        "SECRET_KEY": "abc",
    }
    result = validate_env(env, SCHEMA, "prod")
    assert not result.valid
    err = next(e for e in result.errors if e.key == "DATABASE_URL")
    assert "pattern" in err.message


def test_error_str_contains_env_name_and_key():
    env = {"SECRET_KEY": "s"}
    result = validate_env(env, SCHEMA, "myenv")
    strs = [str(e) for e in result.errors]
    assert any("myenv" in s and "DATABASE_URL" in s for s in strs)


def test_multiple_errors_collected():
    env = {}
    result = validate_env(env, SCHEMA, "empty")
    required_keys = {k for k, r in SCHEMA.items() if r.required}
    found_keys = {e.key for e in result.errors}
    assert required_keys == found_keys
