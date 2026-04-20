"""Tests for envdiff.cli_summary."""
import textwrap
from pathlib import Path

import pytest

from envdiff.cli_summary import build_summary_parser, run_summary


def write_env(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return str(p)


def parse_args(files, extra=None):
    parser = build_summary_parser()
    argv = list(files)
    if extra:
        argv.extend(extra)
    return parser.parse_args(argv)


# --- exit codes ---

def test_identical_files_exit_zero(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=value\n")
    args = parse_args([a, b])
    assert run_summary(args) == 0


def test_differences_exit_zero_without_flag(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=other\n")
    args = parse_args([a, b])
    assert run_summary(args) == 0


def test_differences_exit_one_with_flag(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=other\n")
    args = parse_args([a, b], ["--fail-on-diff"])
    assert run_summary(args) == 1


def test_missing_file_returns_2(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    args = parse_args([a, "/nonexistent/.env"])
    assert run_summary(args) == 2


def test_single_file_returns_2(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    args = parse_args([a])
    assert run_summary(args) == 2


# --- output content ---

def test_identical_output_message(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=value\n")
    args = parse_args([a, b])
    run_summary(args)
    out = capsys.readouterr().out
    assert "identical" in out.lower()


def test_diff_output_contains_env_names(tmp_path, capsys):
    a = write_env(tmp_path, ".env.prod", "KEY=prod_val\nONLY_A=1\n")
    b = write_env(tmp_path, ".env.staging", "KEY=staging_val\n")
    args = parse_args([a, b])
    run_summary(args)
    out = capsys.readouterr().out
    assert ".env.prod" in out
    assert ".env.staging" in out


def test_diff_output_shows_missing_count(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "KEY=val\nEXTRA=1\n")
    b = write_env(tmp_path, ".env.b", "KEY=val\n")
    args = parse_args([a, b])
    run_summary(args)
    out = capsys.readouterr().out
    assert "1 missing" in out


def test_three_files_produces_two_pair_summaries(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "A=1\n")
    b = write_env(tmp_path, ".env.b", "A=2\n")
    c = write_env(tmp_path, ".env.c", "A=1\n")
    args = parse_args([a, b, c])
    run_summary(args)
    out = capsys.readouterr().out
    # Two pairs: a vs b, b vs c
    assert out.count("DIFF") + out.count("OK") >= 2


def test_worst_pair_shown_when_multiple(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "X=1\nY=2\n")
    b = write_env(tmp_path, ".env.b", "X=1\n")
    c = write_env(tmp_path, ".env.c", "X=1\n")
    args = parse_args([a, b, c])
    run_summary(args)
    out = capsys.readouterr().out
    assert "Worst pair" in out
