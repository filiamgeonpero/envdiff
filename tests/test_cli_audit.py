"""Tests for envdiff.cli_audit."""
import json
from pathlib import Path

import pytest

from envdiff.cli_audit import build_audit_parser, run_audit


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def parse_args(argv):
    return build_audit_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# record sub-command
# ---------------------------------------------------------------------------

def test_record_creates_log(tmp_path):
    old = write_env(tmp_path / "old.env", "FOO=1\nBAR=2\n")
    new = write_env(tmp_path / "new.env", "FOO=1\nBAR=3\nBAZ=4\n")
    log = tmp_path / "audit.json"
    args = parse_args(["record", str(old), str(new), "--log", str(log)])
    rc = run_audit(args)
    assert rc == 0
    assert log.exists()


def test_record_captures_correct_number_of_changes(tmp_path):
    old = write_env(tmp_path / "old.env", "A=1\nB=2\n")
    new = write_env(tmp_path / "new.env", "A=1\nB=99\nC=3\n")
    log = tmp_path / "audit.json"
    args = parse_args(["record", str(old), str(new), "--log", str(log)])
    run_audit(args)
    data = json.loads(log.read_text())
    # B changed + C added = 2 entries
    assert len(data["entries"]) == 2


def test_record_appends_to_existing_log(tmp_path):
    old1 = write_env(tmp_path / "old1.env", "X=1\n")
    new1 = write_env(tmp_path / "new1.env", "X=2\n")
    old2 = write_env(tmp_path / "old2.env", "Y=a\n")
    new2 = write_env(tmp_path / "new2.env", "Y=b\n")
    log = tmp_path / "audit.json"
    run_audit(parse_args(["record", str(old1), str(new1), "--log", str(log)]))
    run_audit(parse_args(["record", str(old2), str(new2), "--log", str(log)]))
    data = json.loads(log.read_text())
    assert len(data["entries"]) == 2


def test_record_missing_file_returns_2(tmp_path):
    args = parse_args(["record", "no_such.env", "also_no.env",
                       "--log", str(tmp_path / "a.json")])
    assert run_audit(args) == 2


# ---------------------------------------------------------------------------
# show sub-command
# ---------------------------------------------------------------------------

def test_show_missing_log_returns_2(tmp_path, capsys):
    args = parse_args(["show", "--log", str(tmp_path / "nope.json")])
    assert run_audit(args) == 2


def test_show_prints_entries(tmp_path, capsys):
    old = write_env(tmp_path / "old.env", "K=old\n")
    new = write_env(tmp_path / "new.env", "K=new\n")
    log = tmp_path / "audit.json"
    run_audit(parse_args(["record", str(old), str(new), "--log", str(log)]))
    rc = run_audit(parse_args(["show", "--log", str(log)]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "K" in out


def test_show_filter_by_key(tmp_path, capsys):
    old = write_env(tmp_path / "old.env", "A=1\nB=2\n")
    new = write_env(tmp_path / "new.env", "A=9\nB=8\n")
    log = tmp_path / "audit.json"
    run_audit(parse_args(["record", str(old), str(new), "--log", str(log)]))
    run_audit(parse_args(["show", "--log", str(log), "--key", "A"]))
    out = capsys.readouterr().out
    assert "A" in out
    assert "B" not in out


def test_show_no_matching_entries_message(tmp_path, capsys):
    old = write_env(tmp_path / "old.env", "A=1\n")
    new = write_env(tmp_path / "new.env", "A=2\n")
    log = tmp_path / "audit.json"
    run_audit(parse_args(["record", str(old), str(new), "--log", str(log)]))
    run_audit(parse_args(["show", "--log", str(log), "--key", "NONEXISTENT"]))
    out = capsys.readouterr().out
    assert "No matching" in out
