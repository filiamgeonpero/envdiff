"""Tests for envdiff.redactor."""
import re
import pytest
from envdiff.redactor import (
    RedactOptions,
    redact_env,
    redact_envs,
    REDACTED,
)


def test_non_sensitive_key_unchanged():
    env = {"APP_NAME": "myapp", "PORT": "8080"}
    result = redact_env(env)
    assert result == env


def test_password_key_is_redacted():
    env = {"DB_PASSWORD": "s3cr3t"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == REDACTED


def test_token_key_is_redacted():
    env = {"AUTH_TOKEN": "abc123"}
    result = redact_env(env)
    assert result["AUTH_TOKEN"] == REDACTED


def test_api_key_is_redacted():
    env = {"STRIPE_API_KEY": "pk_live_xyz"}
    result = redact_env(env)
    assert result["STRIPE_API_KEY"] == REDACTED


def test_secret_key_is_redacted():
    env = {"SECRET": "topsecret", "DJANGO_SECRET_KEY": "abc"}
    result = redact_env(env)
    assert result["SECRET"] == REDACTED
    assert result["DJANGO_SECRET_KEY"] == REDACTED


def test_original_dict_not_mutated():
    env = {"DB_PASSWORD": "s3cr3t", "HOST": "localhost"}
    original = dict(env)
    redact_env(env)
    assert env == original


def test_custom_placeholder():
    env = {"API_KEY": "xyz"}
    opts = RedactOptions(placeholder="<hidden>")
    result = redact_env(env, opts)
    assert result["API_KEY"] == "<hidden>"


def test_custom_pattern_matches():
    env = {"MY_CUSTOM_CRED": "value", "NORMAL": "ok"}
    opts = RedactOptions(patterns=[re.compile(r"cred", re.I)])
    result = redact_env(env, opts)
    assert result["MY_CUSTOM_CRED"] == REDACTED
    assert result["NORMAL"] == "ok"


def test_redact_envs_multiple():
    envs = {
        "production": {"DB_PASSWORD": "prod_pass", "HOST": "prod.host"},
        "staging": {"DB_PASSWORD": "stg_pass", "HOST": "stg.host"},
    }
    result = redact_envs(envs)
    assert result["production"]["DB_PASSWORD"] == REDACTED
    assert result["staging"]["DB_PASSWORD"] == REDACTED
    assert result["production"]["HOST"] == "prod.host"
    assert result["staging"]["HOST"] == "stg.host"


def test_empty_env_returns_empty():
    assert redact_env({}) == {}
