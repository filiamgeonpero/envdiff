"""Integration tests for the cascade CLI command."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_cascade import build_cascade_parser, run_cascade


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def parse_args(parser: argparse.ArgumentParser, *args: str) -> argparse.Namespace:
    return parser.parse_args(list(args))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_single_file_exits_zero(tmp_path, capsys):
    f = write_env(tmp_path, "base.env", "A=1\nB=2\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(f))
    assert run_cascade(args) == 0


def test_multiple_files_exits_zero(tmp_path, capsys):
    base = write_env(tmp_path, "base.env", "A=1\n")
    prod = write_env(tmp_path, "prod.env", "A=2\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(base), str(prod))
    assert run_cascade(args) == 0


def test_missing_file_returns_2(tmp_path, capsys):
    parser = build_cascade_parser()
    args = parse_args(parser, str(tmp_path / "ghost.env"))
    assert run_cascade(args) == 2


def test_summary_printed(tmp_path, capsys):
    f = write_env(tmp_path, "a.env", "X=1\nY=2\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(f))
    run_cascade(args)
    out = capsys.readouterr().out
    assert "2" in out  # 2 keys


def test_show_exclusive_flag(tmp_path, capsys):
    base = write_env(tmp_path, "base.env", "SHARED=x\nONLY_BASE=y\n")
    prod = write_env(tmp_path, "prod.env", "SHARED=z\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(base), str(prod), "--show-exclusive")
    run_cascade(args)
    out = capsys.readouterr().out
    assert "ONLY_BASE" in out


def test_show_overrides_flag(tmp_path, capsys):
    base = write_env(tmp_path, "base.env", "KEY=old\n")
    prod = write_env(tmp_path, "prod.env", "KEY=new\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(base), str(prod), "--show-overrides")
    run_cascade(args)
    out = capsys.readouterr().out
    assert "KEY" in out


def test_no_exclusive_message_when_all_shared(tmp_path, capsys):
    base = write_env(tmp_path, "base.env", "A=1\n")
    prod = write_env(tmp_path, "prod.env", "A=2\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(base), str(prod), "--show-exclusive")
    run_cascade(args)
    out = capsys.readouterr().out
    assert "No exclusive" in out


def test_no_overrides_message_when_none(tmp_path, capsys):
    base = write_env(tmp_path, "base.env", "A=1\n")
    prod = write_env(tmp_path, "prod.env", "B=2\n")
    parser = build_cascade_parser()
    args = parse_args(parser, str(base), str(prod), "--show-overrides")
    run_cascade(args)
    out = capsys.readouterr().out
    assert "No overridden" in out
