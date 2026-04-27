"""Integration tests for the audit feature (parser -> auditor -> cli_audit)."""
from pathlib import Path

from envdiff.auditor import AuditLog, diff_to_audit, load_audit, save_audit
from envdiff.cli_audit import build_audit_parser, run_audit
from envdiff.parser import parse_env_file


def write_env(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_quoted_values_tracked_correctly(tmp_path):
    old = write_env(tmp_path / "old.env", 'API_URL="http://old.example.com"\n')
    new = write_env(tmp_path / "new.env", 'API_URL="http://new.example.com"\n')
    old_env = parse_env_file(old)
    new_env = parse_env_file(new)
    entries = diff_to_audit(old_env, new_env, ".env")
    assert len(entries) == 1
    assert entries[0].old_value == "http://old.example.com"
    assert entries[0].new_value == "http://new.example.com"


def test_comment_lines_not_tracked(tmp_path):
    old = write_env(tmp_path / "old.env", "# comment\nFOO=1\n")
    new = write_env(tmp_path / "new.env", "# different comment\nFOO=1\n")
    old_env = parse_env_file(old)
    new_env = parse_env_file(new)
    entries = diff_to_audit(old_env, new_env, ".env")
    assert entries == []


def test_full_record_and_reload_cycle(tmp_path):
    old = write_env(tmp_path / "a.env", "DB=postgres\nSECRET=old\n")
    new = write_env(tmp_path / "b.env", "DB=postgres\nSECRET=new\nEXTRA=yes\n")
    log_path = tmp_path / "audit.json"
    parser = build_audit_parser()
    args = parser.parse_args(["record", str(old), str(new), "--log", str(log_path)])
    rc = run_audit(args)
    assert rc == 0
    log = load_audit(log_path)
    keys = {e.key for e in log.entries}
    assert "SECRET" in keys
    assert "EXTRA" in keys
    assert "DB" not in keys


def test_env_name_label_stored(tmp_path):
    old = write_env(tmp_path / "old.env", "K=1\n")
    new = write_env(tmp_path / "new.env", "K=2\n")
    log_path = tmp_path / "audit.json"
    args = build_audit_parser().parse_args(
        ["record", str(old), str(new), "--log", str(log_path), "--env-name", "production"]
    )
    run_audit(args)
    log = load_audit(log_path)
    assert log.entries[0].env_file == "production"


def test_multiple_record_sessions_accumulate(tmp_path):
    for i in range(3):
        old = write_env(tmp_path / f"old{i}.env", f"KEY{i}=before\n")
        new = write_env(tmp_path / f"new{i}.env", f"KEY{i}=after\n")
        log_path = tmp_path / "audit.json"
        args = build_audit_parser().parse_args(
            ["record", str(old), str(new), "--log", str(log_path)]
        )
        run_audit(args)
    log = load_audit(log_path)
    assert len(log.entries) == 3
