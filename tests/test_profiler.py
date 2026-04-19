import pytest
from envdiff.profiler import profile_env, ProfileResult


ENV = {
    "DATABASE_URL": "postgres://localhost/db",
    "API_KEY": "abc123",
    "DEBUG": "true",
    "PORT": "8080",
    "EMPTY_VAR": "",
    "SECRET_TOKEN": "s3cr3t",
    "lowercase_key": "value",
}


def test_total_keys():
    r = profile_env("prod", ENV)
    assert r.total_keys == len(ENV)


def test_empty_values_detected():
    r = profile_env("prod", ENV)
    assert "EMPTY_VAR" in r.empty_values


def test_sensitive_keys_detected():
    r = profile_env("prod", ENV)
    assert "API_KEY" in r.sensitive_keys
    assert "SECRET_TOKEN" in r.sensitive_keys


def test_url_values_detected():
    r = profile_env("prod", ENV)
    assert "DATABASE_URL" in r.url_values


def test_numeric_values_detected():
    r = profile_env("prod", ENV)
    assert "PORT" in r.numeric_values


def test_boolean_values_detected():
    r = profile_env("prod", ENV)
    assert "DEBUG" in r.boolean_values


def test_uppercase_key_count():
    r = profile_env("prod", ENV)
    assert r.uppercase_keys >= 5


def test_lowercase_key_count():
    r = profile_env("prod", ENV)
    assert r.lowercase_keys == 1


def test_env_name_stored():
    r = profile_env("staging", {})
    assert r.env_name == "staging"


def test_empty_env():
    r = profile_env("empty", {})
    assert r.total_keys == 0
    assert r.empty_values == []


def test_summary_contains_env_name():
    r = profile_env("prod", ENV)
    assert "prod" in r.summary()


def test_summary_contains_total_keys():
    r = profile_env("prod", ENV)
    assert str(len(ENV)) in r.summary()
