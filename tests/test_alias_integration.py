"""Integration tests: aliaser + parser working together on real files."""
import pytest
from pathlib import Path
from envdiff.parser import parse_env_file
from envdiff.aliaser import AliasMap, apply_aliases


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_alias_applied_after_parse(tmp_path):
    f = write_env(tmp_path, ".env", "DB_URL=postgres://localhost/mydb\nSECRET=abc\n")
    env = parse_env_file(f)
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    result = apply_aliases(env, am)
    assert "DATABASE_URL" in result.resolved
    assert result.resolved["DATABASE_URL"] == "postgres://localhost/mydb"
    assert "SECRET" in result.resolved


def test_quoted_alias_value_preserved(tmp_path):
    f = write_env(tmp_path, ".env", 'DB_URL="postgres://localhost/mydb"\n')
    env = parse_env_file(f)
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    result = apply_aliases(env, am)
    assert result.resolved["DATABASE_URL"] == "postgres://localhost/mydb"


def test_canonical_key_wins_over_alias_in_file(tmp_path):
    content = "DATABASE_URL=canonical_value\nDB_URL=alias_value\n"
    f = write_env(tmp_path, ".env", content)
    env = parse_env_file(f)
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    result = apply_aliases(env, am)
    assert result.resolved["DATABASE_URL"] == "canonical_value"
    assert "DB_URL" not in result.resolved


def test_multiple_aliases_for_same_canonical(tmp_path):
    f = write_env(tmp_path, ".env", "DB_CONNECTION=postgres://localhost\n")
    env = parse_env_file(f)
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL", "DB_CONNECTION")
    result = apply_aliases(env, am)
    assert "DATABASE_URL" in result.resolved
    assert result.rename_count == 1


def test_empty_env_file_no_renames(tmp_path):
    f = write_env(tmp_path, ".env", "# just a comment\n")
    env = parse_env_file(f)
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    result = apply_aliases(env, am)
    assert result.rename_count == 0
    assert result.resolved == {}
