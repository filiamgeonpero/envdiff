"""Tests for envdiff.encryptor."""
import pytest

from envdiff.encryptor import (
    EncryptResult,
    decrypt_env,
    encrypt_env,
    _MARKER,
)

_PASS = "s3cr3t"


def make_env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# encrypt_env – sensitive_only=True (default)
# ---------------------------------------------------------------------------

def test_sensitive_key_is_encrypted():
    env = make_env(DB_PASSWORD="hunter2", APP_NAME="myapp")
    result = encrypt_env(env, _PASS)
    assert result.encrypted["DB_PASSWORD"].startswith(_MARKER)


def test_non_sensitive_key_unchanged_by_default():
    env = make_env(APP_NAME="myapp")
    result = encrypt_env(env, _PASS)
    assert result.encrypted["APP_NAME"] == "myapp"


def test_changed_keys_lists_encrypted_keys():
    env = make_env(API_TOKEN="abc", HOST="localhost")
    result = encrypt_env(env, _PASS)
    assert "API_TOKEN" in result.changed_keys
    assert "HOST" not in result.changed_keys


def test_has_changes_true_when_any_encrypted():
    env = make_env(SECRET_KEY="xyz")
    result = encrypt_env(env, _PASS)
    assert result.has_changes() is True


def test_has_changes_false_when_nothing_encrypted():
    env = make_env(HOST="localhost", PORT="5432")
    result = encrypt_env(env, _PASS)
    assert result.has_changes() is False


# ---------------------------------------------------------------------------
# explicit keys list
# ---------------------------------------------------------------------------

def test_explicit_keys_encrypts_only_specified():
    env = make_env(HOST="localhost", PORT="5432", NAME="db")
    result = encrypt_env(env, _PASS, keys=["HOST"])
    assert result.encrypted["HOST"].startswith(_MARKER)
    assert result.encrypted["PORT"] == "5432"


# ---------------------------------------------------------------------------
# sensitive_only=False
# ---------------------------------------------------------------------------

def test_sensitive_only_false_encrypts_all():
    env = make_env(HOST="localhost", PORT="5432")
    result = encrypt_env(env, _PASS, sensitive_only=False)
    assert all(v.startswith(_MARKER) for v in result.encrypted.values())
    assert len(result.changed_keys) == 2


# ---------------------------------------------------------------------------
# decrypt_env
# ---------------------------------------------------------------------------

def test_roundtrip_restores_original_value():
    env = make_env(DB_PASSWORD="hunter2")
    encrypted = encrypt_env(env, _PASS).encrypted
    restored = decrypt_env(encrypted, _PASS)
    assert restored["DB_PASSWORD"] == "hunter2"


def test_decrypt_non_encrypted_value_unchanged():
    env = make_env(HOST="localhost")
    result = decrypt_env(env, _PASS)
    assert result["HOST"] == "localhost"


def test_already_encrypted_not_double_encrypted():
    env = make_env(DB_PASSWORD="hunter2")
    enc1 = encrypt_env(env, _PASS).encrypted
    enc2 = encrypt_env(enc1, _PASS).encrypted
    # second pass should leave already-encrypted value alone
    assert enc2["DB_PASSWORD"] == enc1["DB_PASSWORD"]


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    env = make_env(HOST="localhost")
    result = encrypt_env(env, _PASS)
    assert result.summary() == "No keys encrypted."


def test_summary_with_changes():
    env = make_env(DB_PASSWORD="x")
    result = encrypt_env(env, _PASS)
    assert "DB_PASSWORD" in result.summary()
