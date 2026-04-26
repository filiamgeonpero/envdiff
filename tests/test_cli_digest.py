"""Tests for envdiff.cli_digest."""
import argparse
import pytest
from pathlib import Path

from envdiff.cli_digest import build_digest_parser, run_digest


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def parse_args(args):
    parser = build_digest_parser()
    return parser.parse_args(args)


def test_identical_files_exit_zero(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=bar\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=bar\n")
    args = parse_args([str(p1), str(p2)])
    assert run_digest(args) == 0


def test_different_files_exit_zero_without_flag(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=dev\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=prod\n")
    args = parse_args([str(p1), str(p2)])
    assert run_digest(args) == 0


def test_different_files_exit_one_with_flag(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=dev\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=prod\n")
    args = parse_args(["--fail-on-diff", str(p1), str(p2)])
    assert run_digest(args) == 1


def test_identical_files_with_flag_still_zero(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=same\n")
    p2 = write_env(tmp_path, ".env.b", "FOO=same\n")
    args = parse_args(["--fail-on-diff", str(p1), str(p2)])
    assert run_digest(args) == 0


def test_missing_file_returns_2(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=bar\n")
    args = parse_args([str(p1), str(tmp_path / "missing.env")])
    assert run_digest(args) == 2


def test_single_file_exit_zero(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=bar\n")
    args = parse_args([str(p1)])
    assert run_digest(args) == 0


def test_short_flag_accepted(tmp_path):
    p1 = write_env(tmp_path, ".env.a", "FOO=bar\n")
    args = parse_args(["--short", str(p1)])
    assert run_digest(args) == 0
