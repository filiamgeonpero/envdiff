"""Tests for envdiff.parser."""

import textwrap
from pathlib import Path

import pytest

from envdiff.parser import EnvParseError, parse_env_file


def write_env(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(textwrap.dedent(content), encoding="utf-8")
    return env_file


def test_basic_key_value(tmp_path):
    f = write_env(tmp_path, """
        APP_NAME=myapp
        DEBUG=true
    """)
    result = parse_env_file(f)
    assert result == {"APP_NAME": "myapp", "DEBUG": "true"}


def test_ignores_comments_and_blank_lines(tmp_path):
    f = write_env(tmp_path, """
        # This is a comment

        PORT=8080
    """)
    result = parse_env_file(f)
    assert result == {"PORT": "8080"}


def test_value_with_double_quotes(tmp_path):
    f = write_env(tmp_path, 'SECRET="my secret value"\n')
    result = parse_env_file(f)
    assert result["SECRET"] == "my secret value"


def test_value_with_single_quotes(tmp_path):
    f = write_env(tmp_path, "TOKEN='abc123'\n")
    result = parse_env_file(f)
    assert result["TOKEN"] == "abc123"


def test_empty_value(tmp_path):
    f = write_env(tmp_path, "EMPTY=\n")
    result = parse_env_file(f)
    assert result["EMPTY"] is None


def test_key_without_equals(tmp_path):
    f = write_env(tmp_path, "STANDALONE_KEY\n")
    result = parse_env_file(f)
    assert result["STANDALONE_KEY"] is None


def test_file_not_found():
    with pytest.raises(EnvParseError, match="File not found"):
        parse_env_file("/nonexistent/path/.env")


def test_invalid_key_raises(tmp_path):
    f = write_env(tmp_path, "123INVALID\n")
    with pytest.raises(EnvParseError, match="Invalid key"):
        parse_env_file(f)
