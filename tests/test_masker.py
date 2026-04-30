"""Tests for envdiff.masker."""
import pytest
from envdiff.masker import MaskOptions, MaskResult, mask_env


def make_env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_non_sensitive_key_is_not_masked():
    env = make_env(HOST="localhost", PORT="5432")
    result = mask_env(env)
    assert not result.has_masked()
    for entry in result.entries:
        assert not entry.was_masked
        assert entry.masked == entry.original


def test_password_key_is_masked():
    env = make_env(DB_PASSWORD="s3cr3t")
    result = mask_env(env)
    assert result.has_masked()
    assert result.masked_env["DB_PASSWORD"] == "***"


def test_token_key_is_masked():
    env = make_env(AUTH_TOKEN="abc123")
    result = mask_env(env)
    assert "AUTH_TOKEN" in result.masked_keys


def test_secret_key_is_masked():
    env = make_env(APP_SECRET="xyz")
    result = mask_env(env)
    assert "APP_SECRET" in result.masked_keys


def test_api_key_is_masked():
    env = make_env(API_KEY="key-value")
    result = mask_env(env)
    assert "API_KEY" in result.masked_keys


def test_custom_mask_string():
    env = make_env(PASSWORD="hunter2")
    opts = MaskOptions(mask="[REDACTED]")
    result = mask_env(env, opts)
    assert result.masked_env["PASSWORD"] == "[REDACTED]"


def test_partial_mask_shows_first_and_last_char():
    env = make_env(DB_PASSWORD="s3cr3t")
    opts = MaskOptions(partial=True)
    result = mask_env(env, opts)
    masked = result.masked_env["DB_PASSWORD"]
    assert masked.startswith("s")
    assert masked.endswith("t")
    assert "***" in masked


def test_partial_mask_short_value_fully_masked():
    env = make_env(DB_PASSWORD="ab")
    opts = MaskOptions(partial=True)
    result = mask_env(env, opts)
    assert result.masked_env["DB_PASSWORD"] == "***"


def test_masked_env_dict_contains_all_keys():
    env = make_env(HOST="localhost", DB_PASSWORD="s3cr3t", PORT="5432")
    result = mask_env(env)
    assert set(result.masked_env.keys()) == {"HOST", "DB_PASSWORD", "PORT"}


def test_summary_counts_masked_keys():
    env = make_env(HOST="localhost", DB_PASSWORD="s3cr3t", AUTH_TOKEN="tok")
    result = mask_env(env)
    assert result.summary() == "2/3 keys masked"


def test_custom_patterns_override_defaults():
    env = make_env(MY_CUSTOM="value", PASSWORD="ignored")
    opts = MaskOptions(patterns=("custom",))
    result = mask_env(env, opts)
    assert "MY_CUSTOM" in result.masked_keys
    assert "PASSWORD" not in result.masked_keys


def test_entry_str_representation():
    env = make_env(DB_PASSWORD="s3cr3t")
    result = mask_env(env)
    entry = result.entries[0]
    assert "masked" in str(entry)
    assert "DB_PASSWORD" in str(entry)


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.entries == []
    assert not result.has_masked()
    assert result.summary() == "0/0 keys masked"
