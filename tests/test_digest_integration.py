"""Integration tests: parse real files then digest them."""
from pathlib import Path

import pytest

from envdiff.digester import digest_files


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_quoted_values_produce_stable_digest(tmp_path):
    p1 = write_env(tmp_path, ".env.a", 'SECRET="hello world"\n')
    p2 = write_env(tmp_path, ".env.b", 'SECRET="hello world"\n')
    result = digest_files([p1, p2])
    assert result.all_match is True


def test_comment_lines_ignored_in_digest(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "# comment\nFOO=bar\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=bar\n")
    result = digest_files([p1, p2])
    assert result.all_match is True


def test_blank_lines_ignored_in_digest(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "\nFOO=bar\n\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=bar\n")
    result = digest_files([p1, p2])
    assert result.all_match is True


def test_extra_key_makes_digests_differ(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=bar\nEXTRA=1\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=bar\n")
    result = digest_files([p1, p2])
    assert result.all_match is False


def test_three_files_all_identical(tmp_path):
    content = "A=1\nB=2\n"
    paths = [write_env(tmp_path, f".env.{i}", content) for i in range(3)]
    result = digest_files(paths)
    assert result.all_match is True
    assert len(result.entries) == 3


def test_three_files_one_differs(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "A=1\n")
    p2 = write_env(tmp_path, ".env.b", "A=1\n")
    p3 = write_env(tmp_path, ".env.c", "A=99\n")
    result = digest_files([p1, p2, p3])
    assert result.all_match is False
    pairs = result.mismatched_pairs()
    # a-c and b-c differ; a-b match
    assert len(pairs) == 2
