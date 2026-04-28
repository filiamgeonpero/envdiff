"""Tests for envdiff.cli_encrypt."""
import textwrap
from pathlib import Path

import pytest

from envdiff.cli_encrypt import build_encrypt_parser, run_encrypt
from envdiff.encryptor import _MARKER


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


def parse_args(argv):
    return build_encrypt_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# basic operation
# ---------------------------------------------------------------------------

def test_missing_file_returns_2(tmp_path):
    args = parse_args([str(tmp_path / "nope.env"), "--passphrase", "x"])
    assert run_encrypt(args) == 2


def test_encrypt_exits_zero(tmp_path):
    f = write_env(tmp_path, ".env", "DB_PASSWORD=secret\nHOST=localhost\n")
    args = parse_args([str(f), "--passphrase", "pass"])
    assert run_encrypt(args) == 0


def test_encrypt_output_contains_marker(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "DB_PASSWORD=secret\n")
    args = parse_args([str(f), "--passphrase", "pass"])
    run_encrypt(args)
    out = capsys.readouterr().out
    assert _MARKER in out


def test_non_sensitive_key_not_encrypted(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    args = parse_args([str(f), "--passphrase", "pass"])
    run_encrypt(args)
    out = capsys.readouterr().out
    assert _MARKER not in out
    assert "HOST=localhost" in out


# ---------------------------------------------------------------------------
# --all flag
# ---------------------------------------------------------------------------

def test_all_flag_encrypts_non_sensitive(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    args = parse_args([str(f), "--passphrase", "pass", "--all"])
    run_encrypt(args)
    out = capsys.readouterr().out
    assert _MARKER in out


# ---------------------------------------------------------------------------
# --decrypt flag
# ---------------------------------------------------------------------------

def test_decrypt_restores_value(tmp_path, capsys):
    from envdiff.encryptor import encrypt_env

    env = {"DB_PASSWORD": "hunter2"}
    enc = encrypt_env(env, "pass").encrypted
    content = "\n".join(f"{k}={v}" for k, v in enc.items()) + "\n"
    f = write_env(tmp_path, ".env", content)
    args = parse_args([str(f), "--passphrase", "pass", "--decrypt"])
    run_encrypt(args)
    out = capsys.readouterr().out
    assert "hunter2" in out


# ---------------------------------------------------------------------------
# --in-place
# ---------------------------------------------------------------------------

def test_in_place_writes_file(tmp_path):
    f = write_env(tmp_path, ".env", "API_TOKEN=abc123\n")
    args = parse_args([str(f), "--passphrase", "pass", "--in-place"])
    run_encrypt(args)
    content = f.read_text()
    assert _MARKER in content
