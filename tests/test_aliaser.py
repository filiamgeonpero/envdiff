"""Tests for envdiff.aliaser."""
import pytest
from envdiff.aliaser import AliasMap, apply_aliases


# ---------------------------------------------------------------------------
# AliasMap
# ---------------------------------------------------------------------------

def test_add_and_retrieve_aliases():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL", "DB_CONNECTION")
    assert am.aliases_for("DATABASE_URL") == ["DB_URL", "DB_CONNECTION"]


def test_canonical_for_known_alias():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    assert am.canonical_for("DB_URL") == "DATABASE_URL"


def test_canonical_for_unknown_key_returns_none():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    assert am.canonical_for("UNKNOWN_KEY") is None


def test_aliases_for_unknown_canonical_returns_empty():
    am = AliasMap()
    assert am.aliases_for("NONEXISTENT") == []


def test_duplicate_alias_not_added_twice():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    am.add("DATABASE_URL", "DB_URL")  # duplicate
    assert am.aliases_for("DATABASE_URL").count("DB_URL") == 1


def test_all_aliases_returns_copy():
    am = AliasMap()
    am.add("FOO", "F")
    result = am.all_aliases()
    result["FOO"].append("SHOULD_NOT_AFFECT_ORIGINAL")
    assert "SHOULD_NOT_AFFECT_ORIGINAL" not in am.aliases_for("FOO")


# ---------------------------------------------------------------------------
# apply_aliases
# ---------------------------------------------------------------------------

def test_alias_key_renamed_to_canonical():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    env = {"DB_URL": "postgres://localhost/db"}
    result = apply_aliases(env, am)
    assert "DATABASE_URL" in result.resolved
    assert "DB_URL" not in result.resolved


def test_non_alias_key_unchanged():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    env = {"SECRET_KEY": "abc123"}
    result = apply_aliases(env, am)
    assert result.resolved["SECRET_KEY"] == "abc123"


def test_canonical_takes_precedence_over_alias():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    env = {"DATABASE_URL": "real_value", "DB_URL": "alias_value"}
    result = apply_aliases(env, am)
    assert result.resolved["DATABASE_URL"] == "real_value"
    assert "DB_URL" not in result.resolved


def test_renames_dict_populated():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    env = {"DB_URL": "postgres://localhost/db"}
    result = apply_aliases(env, am)
    assert result.renames == {"DB_URL": "DATABASE_URL"}


def test_rename_count_reflects_resolved_aliases():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    am.add("SECRET_KEY", "SECRET")
    env = {"DB_URL": "postgres://", "SECRET": "s3cr3t"}
    result = apply_aliases(env, am)
    assert result.rename_count == 2


def test_summary_no_renames():
    am = AliasMap()
    env = {"FOO": "bar"}
    result = apply_aliases(env, am)
    assert result.summary() == "No aliases resolved."


def test_summary_with_renames_contains_arrow():
    am = AliasMap()
    am.add("DATABASE_URL", "DB_URL")
    env = {"DB_URL": "postgres://"}
    result = apply_aliases(env, am)
    assert "->" in result.summary()
    assert "DB_URL" in result.summary()
    assert "DATABASE_URL" in result.summary()
