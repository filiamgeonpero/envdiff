"""Integration tests: parse → encrypt → decrypt round-trip."""
import textwrap
from pathlib import Path

import pytest

from envdiff.encryptor import decrypt_env, encrypt_env, _MARKER
from envdiff.parser import parse_env_file


def write_env(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(content))
    return p


def test_quoted_password_survives_roundtrip(tmp_path):
    f = write_env(tmp_path, 'DB_PASSWORD="p@ss w0rd"\n')
    env = parse_env_file(str(f))
    enc = encrypt_env(env, "passphrase").encrypted
    dec = decrypt_env(enc, "passphrase")
    assert dec["DB_PASSWORD"] == "p@ss w0rd"


def test_comment_lines_not_included_in_encrypted_output(tmp_path):
    f = write_env(tmp_path, "# comment\nDB_PASSWORD=secret\n")
    env = parse_env_file(str(f))
    enc = encrypt_env(env, "pass").encrypted
    # comments are not parsed as keys, so only DB_PASSWORD present
    assert list(enc.keys()) == ["DB_PASSWORD"]


def test_non_sensitive_keys_unchanged_after_roundtrip(tmp_path):
    f = write_env(tmp_path, "HOST=db.local\nDB_PASSWORD=secret\n")
    env = parse_env_file(str(f))
    enc = encrypt_env(env, "pass").encrypted
    dec = decrypt_env(enc, "pass")
    assert dec["HOST"] == "db.local"
    assert dec["DB_PASSWORD"] == "secret"


def test_multiple_sensitive_keys_all_encrypted(tmp_path):
    content = "DB_PASSWORD=p1\nAPI_TOKEN=t1\nSECRET_KEY=s1\nHOST=localhost\n"
    f = write_env(tmp_path, content)
    env = parse_env_file(str(f))
    result = encrypt_env(env, "pass")
    for k in ("DB_PASSWORD", "API_TOKEN", "SECRET_KEY"):
        assert result.encrypted[k].startswith(_MARKER), k
    assert not result.encrypted["HOST"].startswith(_MARKER)


def test_empty_value_encrypted_and_restored(tmp_path):
    f = write_env(tmp_path, "DB_PASSWORD=\n")
    env = parse_env_file(str(f))
    enc = encrypt_env(env, "pass").encrypted
    dec = decrypt_env(enc, "pass")
    assert dec["DB_PASSWORD"] == ""
