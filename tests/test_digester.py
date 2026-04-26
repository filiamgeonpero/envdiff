"""Tests for envdiff.digester."""
import pytest
from pathlib import Path

from envdiff.digester import (
    DigestEntry,
    DigestResult,
    digest_envs,
    digest_files,
    _digest_env,
)


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_identical_envs_produce_same_digest():
    a = {"FOO": "bar", "BAZ": "qux"}
    b = {"FOO": "bar", "BAZ": "qux"}
    assert _digest_env(a) == _digest_env(b)


def test_different_values_produce_different_digest():
    a = {"FOO": "bar"}
    b = {"FOO": "baz"}
    assert _digest_env(a) != _digest_env(b)


def test_key_order_does_not_affect_digest():
    a = {"A": "1", "B": "2"}
    b = {"B": "2", "A": "1"}
    assert _digest_env(a) == _digest_env(b)


def test_digest_envs_returns_entry_per_env():
    result = digest_envs({"dev": {"X": "1"}, "prod": {"X": "2"}})
    assert len(result.entries) == 2
    names = {e.name for e in result.entries}
    assert names == {"dev", "prod"}


def test_digest_envs_key_count_correct():
    result = digest_envs({"dev": {"A": "1", "B": "2"}})
    assert result.entries[0].key_count == 2


def test_all_match_true_for_identical():
    result = digest_envs({"dev": {"X": "1"}, "prod": {"X": "1"}})
    assert result.all_match is True


def test_all_match_false_for_different():
    result = digest_envs({"dev": {"X": "1"}, "prod": {"X": "2"}})
    assert result.all_match is False


def test_mismatched_pairs_empty_when_identical():
    result = digest_envs({"dev": {"X": "1"}, "prod": {"X": "1"}})
    assert result.mismatched_pairs() == []


def test_mismatched_pairs_returns_pair():
    result = digest_envs({"dev": {"X": "1"}, "prod": {"X": "2"}})
    pairs = result.mismatched_pairs()
    assert len(pairs) == 1
    assert set(pairs[0]) == {"dev", "prod"}


def test_get_returns_entry_by_name():
    result = digest_envs({"staging": {"K": "v"}})
    entry = result.get("staging")
    assert entry is not None
    assert entry.name == "staging"


def test_get_returns_none_for_missing():
    result = digest_envs({"dev": {"K": "v"}})
    assert result.get("prod") is None


def test_summary_all_match():
    result = digest_envs({"dev": {"A": "1"}, "prod": {"A": "1"}})
    assert "identical" in result.summary()


def test_summary_mismatch():
    result = digest_envs({"dev": {"A": "1"}, "prod": {"A": "2"}})
    assert "differing" in result.summary()


def test_digest_files_reads_real_files(tmp_path):
    p1 = write_env(tmp_path, ".env.dev", "FOO=bar\nBAZ=1\n")
    p2 = write_env(tmp_path, ".env.prod", "FOO=bar\nBAZ=1\n")
    result = digest_files([p1, p2])
    assert result.all_match is True


def test_digest_files_detects_difference(tmp_path):
    p1 = write_env(tmp_path, ".env.dev", "FOO=dev\n")
    p2 = write_env(tmp_path, ".env.prod", "FOO=prod\n")
    result = digest_files([p1, p2])
    assert result.all_match is False


def test_entry_str_contains_name():
    entry = DigestEntry(name="dev", path=".env.dev", sha256="abc123", key_count=3)
    assert "dev" in str(entry)
