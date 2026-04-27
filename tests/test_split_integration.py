"""Integration tests: parse real .env files then split them."""
from pathlib import Path
import pytest

from envdiff.parser import parse_env_file
from envdiff.splitter import SplitOptions, split_env


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parsed_file_splits_correctly(tmp_path):
    src = write_env(tmp_path, ".env", (
        "prod__DB_HOST=prod-db\n"
        "dev__DB_HOST=dev-db\n"
        "# a comment\n"
        "prod__SECRET=abc\n"
    ))
    merged = parse_env_file(src)
    opts = SplitOptions(envs=["prod", "dev"])
    result = split_env(merged, opts)
    assert result.envs["prod"]["DB_HOST"] == "prod-db"
    assert result.envs["dev"]["DB_HOST"] == "dev-db"
    assert result.envs["prod"]["SECRET"] == "abc"


def test_quoted_values_survive_split(tmp_path):
    src = write_env(tmp_path, ".env", 'prod__URL="https://example.com"\n')
    merged = parse_env_file(src)
    opts = SplitOptions(envs=["prod"])
    result = split_env(merged, opts)
    assert result.envs["prod"]["URL"] == "https://example.com"


def test_blank_lines_and_comments_ignored(tmp_path):
    src = write_env(tmp_path, ".env", (
        "\n"
        "# comment\n"
        "dev__KEY=value\n"
        "\n"
    ))
    merged = parse_env_file(src)
    opts = SplitOptions(envs=["dev"])
    result = split_env(merged, opts)
    assert result.envs["dev"] == {"KEY": "value"}


def test_three_env_split(tmp_path):
    src = write_env(tmp_path, ".env", (
        "prod__X=1\nstaging__X=2\ndev__X=3\n"
    ))
    merged = parse_env_file(src)
    opts = SplitOptions(envs=["prod", "staging", "dev"])
    result = split_env(merged, opts)
    assert result.envs["prod"]["X"] == "1"
    assert result.envs["staging"]["X"] == "2"
    assert result.envs["dev"]["X"] == "3"
    assert not result.has_unmatched()
