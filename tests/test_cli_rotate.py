"""Integration tests for envdiff.cli_rotate."""
import argparse
from pathlib import Path

import pytest

from envdiff.cli_rotate import build_rotate_parser, run_rotate


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def parse_args(extra: list) -> argparse.Namespace:
    parser = build_rotate_parser()
    return parser.parse_args(extra)


def test_no_patches_returns_2(tmp_path):
    env_file = write_env(tmp_path / ".env", "DB_PASSWORD=old\n")
    args = parse_args([str(env_file)])
    assert run_rotate(args) == 2


def test_missing_file_returns_2(tmp_path):
    args = parse_args([str(tmp_path / "missing.env"), "--set", "KEY=val"])
    assert run_rotate(args) == 2


def test_invalid_patch_format_exits(tmp_path):
    env_file = write_env(tmp_path / ".env", "DB_PASSWORD=old\n")
    args = parse_args([str(env_file), "--set", "NOEQUALS"])
    with pytest.raises(SystemExit) as exc_info:
        run_rotate(args)
    assert exc_info.value.code == 2


def test_dry_run_does_not_write(tmp_path):
    env_file = write_env(tmp_path / ".env", "SECRET=old_value\n")
    args = parse_args([str(env_file), "--set", "SECRET=new_value", "--dry-run"])
    run_rotate(args)
    assert env_file.read_text() == "SECRET=old_value\n"


def test_rotation_writes_new_value(tmp_path):
    env_file = write_env(tmp_path / ".env", "TOKEN=old_token\nAPP=myapp\n")
    args = parse_args([str(env_file), "--set", "TOKEN=new_token"])
    code = run_rotate(args)
    assert code == 0
    content = env_file.read_text()
    assert "new_token" in content
    assert "myapp" in content


def test_unchanged_key_not_in_output(tmp_path, capsys):
    env_file = write_env(tmp_path / ".env", "TOKEN=old\nAPP=myapp\n")
    args = parse_args([str(env_file), "--set", "TOKEN=new"])
    run_rotate(args)
    captured = capsys.readouterr()
    assert "APP" not in captured.out


def test_quiet_flag_suppresses_per_key_output(tmp_path, capsys):
    env_file = write_env(tmp_path / ".env", "SECRET=old\n")
    args = parse_args([str(env_file), "--set", "SECRET=new", "--quiet"])
    run_rotate(args)
    captured = capsys.readouterr()
    assert "->" not in captured.out
    assert "rotated" in captured.out
