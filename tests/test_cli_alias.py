"""Tests for envdiff.cli_alias."""
import pytest
from pathlib import Path
from envdiff.cli_alias import build_alias_parser, run_alias


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def parse_args(parser, argv):
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_no_aliases_exits_zero(tmp_path):
    f = write_env(tmp_path, ".env", "FOO=bar\nBAZ=qux\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f)])
    assert run_alias(args) == 0


def test_alias_resolved_exits_zero(tmp_path):
    f = write_env(tmp_path, ".env", "DB_URL=postgres://localhost/db\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f), "--alias", "DATABASE_URL=DB_URL"])
    assert run_alias(args) == 0


def test_multiple_files_exit_zero(tmp_path):
    f1 = write_env(tmp_path, ".env.dev", "DB_URL=postgres://dev\n")
    f2 = write_env(tmp_path, ".env.prod", "DB_URL=postgres://prod\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f1), str(f2), "--alias", "DATABASE_URL=DB_URL"])
    assert run_alias(args) == 0


def test_quiet_flag_exits_zero(tmp_path):
    f = write_env(tmp_path, ".env", "DB_URL=postgres://localhost\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f), "--alias", "DATABASE_URL=DB_URL", "--quiet"])
    assert run_alias(args) == 0


def test_missing_file_returns_2(tmp_path):
    parser = build_alias_parser()
    args = parse_args(parser, [str(tmp_path / "nonexistent.env")])
    assert run_alias(args) == 2


def test_output_contains_summary(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "DB_URL=postgres://localhost\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f), "--alias", "DATABASE_URL=DB_URL"])
    run_alias(args)
    captured = capsys.readouterr()
    assert "DATABASE_URL" in captured.out


def test_no_renames_message_when_no_aliases_match(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "FOO=bar\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f), "--alias", "DATABASE_URL=DB_URL"])
    run_alias(args)
    captured = capsys.readouterr()
    assert "No aliases resolved" in captured.out


def test_malformed_alias_spec_warns_but_continues(tmp_path, capsys):
    f = write_env(tmp_path, ".env", "FOO=bar\n")
    parser = build_alias_parser()
    args = parse_args(parser, [str(f), "--alias", "BADSPEC"])
    result = run_alias(args)
    captured = capsys.readouterr()
    assert result == 0
    assert "Warning" in captured.err
