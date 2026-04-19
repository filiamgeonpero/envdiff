import os
import pytest
from pathlib import Path
from envdiff.cli_profile import build_profile_parser, run_profile


def write_env(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


def test_single_file_exit_zero(tmp_path):
    f = write_env(tmp_path, ".env", "KEY=value\nPORT=8080\n")
    parser = build_profile_parser()
    args = parser.parse_args([f])
    assert run_profile(args) == 0


def test_multiple_files_exit_zero(tmp_path):
    f1 = write_env(tmp_path, "a.env", "A=1\n")
    f2 = write_env(tmp_path, "b.env", "B=2\n")
    parser = build_profile_parser()
    args = parser.parse_args([f1, f2])
    assert run_profile(args) == 0


def test_missing_file_returns_2(tmp_path):
    parser = build_profile_parser()
    args = parser.parse_args([str(tmp_path / "nope.env")])
    assert run_profile(args) == 2


def test_output_contains_total_keys(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "A=1\nB=2\nC=3\n")
    parser = build_profile_parser()
    args = parser.parse_args([f])
    run_profile(args)
    out = capsys.readouterr().out
    assert "3" in out


def test_custom_name_appears_in_output(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "X=y\n")
    parser = build_profile_parser()
    args = parser.parse_args([f, "--names", "production"])
    run_profile(args)
    out = capsys.readouterr().out
    assert "production" in out


def test_empty_file_exit_zero(tmp_path):
    f = write_env(tmp_path, "empty.env", "")
    parser = build_profile_parser()
    args = parser.parse_args([f])
    assert run_profile(args) == 0
