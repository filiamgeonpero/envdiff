"""Tests for envdiff.cli_split."""
import argparse
from pathlib import Path
import pytest

from envdiff.cli_split import build_split_parser, run_split


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def parse_args(extra: list[str], tmp_path: Path) -> argparse.Namespace:
    parser = build_split_parser()
    return parser.parse_args(extra + ["--outdir", str(tmp_path / "out")])


def test_split_creates_output_files(tmp_path):
    src = write_env(tmp_path, ".env", "prod__DB=prod-db\ndev__DB=dev-db\n")
    args = parse_args([str(src), "--envs", "prod", "dev"], tmp_path)
    rc = run_split(args)
    assert rc == 0
    assert (tmp_path / "out" / ".env.prod").exists()
    assert (tmp_path / "out" / ".env.dev").exists()


def test_split_output_contains_correct_keys(tmp_path):
    src = write_env(tmp_path, ".env", "prod__HOST=ph\ndev__HOST=dh\n")
    args = parse_args([str(src), "--envs", "prod", "dev"], tmp_path)
    run_split(args)
    content = (tmp_path / "out" / ".env.prod").read_text()
    assert "HOST=ph" in content
    assert "prod__" not in content


def test_dry_run_does_not_write_files(tmp_path):
    src = write_env(tmp_path, ".env", "prod__X=1\n")
    args = parse_args([str(src), "--envs", "prod", "--dry-run"], tmp_path)
    run_split(args)
    assert not (tmp_path / "out" / ".env.prod").exists()


def test_missing_file_returns_2(tmp_path):
    args = parse_args([str(tmp_path / "nope.env"), "--envs", "prod"], tmp_path)
    assert run_split(args) == 2


def test_no_strip_keeps_prefix(tmp_path):
    src = write_env(tmp_path, ".env", "prod__KEY=v\n")
    parser = build_split_parser()
    args = parser.parse_args([str(src), "--envs", "prod", "--no-strip",
                               "--outdir", str(tmp_path / "out")])
    run_split(args)
    content = (tmp_path / "out" / ".env.prod").read_text()
    assert "prod__KEY" in content


def test_unmatched_key_warning_printed(tmp_path, capsys):
    src = write_env(tmp_path, ".env", "ORPHAN=val\n")
    args = parse_args([str(src), "--envs", "prod"], tmp_path)
    run_split(args)
    captured = capsys.readouterr()
    assert "unmatched" in captured.err
